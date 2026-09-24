"""The panel API over HTTPS: certificate verification modes, redirects and proxy refusals."""

from __future__ import annotations

import datetime
import hashlib
import ipaddress
import ssl
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doormonitor.api import (
    FINGERPRINT_MISMATCH,
    FORBIDDEN,
    REDIRECT,
    TLS_FAILED,
    PanelApi,
    PanelApiError,
    normalize_fingerprint,
    ssl_setting,
    url_problem,
)
from custom_components.doormonitor.const import (
    CONF_API_FINGERPRINT,
    CONF_API_TOKEN,
    CONF_API_URL,
    CONF_API_VERIFY,
    CONF_LINKS,
)

from .conftest import PANEL_FRONT, REAL_FRONT
from .fake_panel import ROOT_ID, ROOT_PIN, TOKEN, FakePanel
from .test_admin import _add_entry, _admin_step, _options, ws


class Pki:
    """A test CA and certificates it issued, written to ``tmp_path``."""

    def __init__(self, tmp_path: Path) -> None:
        self._dir = tmp_path
        self._key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
        self.ca = self._build(name, name, self._key.public_key(), ca=True)

    def _build(self, subject, issuer, public_key, *, ca=False, sans=()) -> x509.Certificate:
        """A certificate the CA key signs, with what Python's strict verification requires."""
        now = datetime.datetime.now(datetime.UTC)
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False)
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(self._key.public_key()),
                critical=False,
            )
        )
        if ca:
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        if sans:
            builder = builder.add_extension(x509.SubjectAlternativeName(list(sans)), critical=False)
        return builder.sign(self._key, hashes.SHA256())

    def server_context(self, *sans: x509.GeneralName) -> tuple[ssl.SSLContext, str]:
        """A server context for a certificate this CA issued, and its SHA-256 fingerprint."""
        key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "door-api")])
        cert = self._build(subject, self.ca.subject, key.public_key(), sans=sans)
        cert_file, key_file = self._dir / f"{id(cert)}.pem", self._dir / f"{id(cert)}.key"
        cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_file.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        der = cert.public_bytes(serialization.Encoding.DER)
        return context, hashlib.sha256(der).hexdigest()

    def client_context(self) -> ssl.SSLContext:
        """A context that trusts this CA, as a system trust store with it installed would."""
        return ssl.create_default_context(
            cadata=self.ca.public_bytes(serialization.Encoding.PEM).decode()
        )


LOCALHOST = x509.IPAddress(ipaddress.ip_address("127.0.0.1"))
ELSEWHERE = x509.DNSName("door-api.elsewhere.example")


async def _serve(app: web.Application, context: ssl.SSLContext | None = None) -> TestServer:
    server = TestServer(app, host="127.0.0.1")
    await server.start_server(ssl=context)
    return server


@pytest.fixture(autouse=True)
def refused_handshakes_are_expected(hass: HomeAssistant) -> Generator[None]:
    """A client refusing the test server's certificate aborts the handshake, which the server's
    loop reports as an error; that is the point of these tests, not a failure."""
    loop = hass.loop
    original = loop.get_exception_handler()

    def handler(loop, context) -> None:
        if isinstance(context.get("exception"), ssl.SSLError | ConnectionResetError):
            return
        if original is not None:
            original(loop, context)

    loop.set_exception_handler(handler)
    yield
    loop.set_exception_handler(original)


@pytest.fixture
def pki(tmp_path: Path) -> Pki:
    return Pki(tmp_path)


@pytest.fixture
async def tls_panel(socket_enabled: None, pki: Pki) -> AsyncGenerator[tuple[FakePanel, str, str]]:
    """The fake panel over HTTPS with a certificate valid for 127.0.0.1; yields its fingerprint."""
    panel = FakePanel()
    context, fingerprint = pki.server_context(LOCALHOST)
    server = await _serve(panel.app, context)
    yield panel, str(server.make_url("")).rstrip("/"), fingerprint
    await server.close()


@pytest.fixture
async def trusting_session(pki: Pki) -> AsyncGenerator[aiohttp.ClientSession]:
    """A session whose system trust includes the test CA."""
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=pki.client_context()))
    yield session
    await session.close()


def _colons(fingerprint: str) -> str:
    return ":".join(fingerprint[i : i + 2] for i in range(0, 64, 2)).upper()


# -- helpers -------------------------------------------------------------------


def test_fingerprints_are_normalized_or_rejected() -> None:
    digits = "ab" * 32
    assert normalize_fingerprint(f"  {_colons(digits)}\n") == digits
    assert normalize_fingerprint(digits.upper()) == digits
    assert normalize_fingerprint("ab" * 31) is None
    assert normalize_fingerprint("zz" * 32) is None
    assert normalize_fingerprint("") is None
    with pytest.raises(ValueError):
        ssl_setting("fingerprint", "not a fingerprint")
    assert ssl_setting(None, None) is True
    assert ssl_setting("system", "ab" * 32) is True
    assert ssl_setting("disabled", None) is False
    assert isinstance(ssl_setting("fingerprint", digits), aiohttp.Fingerprint)


def test_urls_with_credentials_or_without_host_are_refused() -> None:
    assert url_problem("https://door-api.example.lan") is None
    assert url_problem("http://192.168.1.10:8081") is None
    assert url_problem("https://user:pass@door-api.example.lan") == "url_credentials"
    assert url_problem("https://user@door-api.example.lan") == "url_credentials"
    assert url_problem("ftp://door-api.example.lan") == "invalid_url"
    assert url_problem("door-api.example.lan") == "invalid_url"


# -- the client ------------------------------------------------------------------


async def test_system_trust_accepts_a_trusted_certificate(
    tls_panel, trusting_session: aiohttp.ClientSession
) -> None:
    _, url, _ = tls_panel
    assert (await PanelApi(trusting_session, url, TOKEN).info())["api"] == 1


async def test_system_trust_refuses_untrusted_and_wrong_host_certificates(
    hass: HomeAssistant, tls_panel, pki: Pki, trusting_session: aiohttp.ClientSession
) -> None:
    panel, url, _ = tls_panel
    with pytest.raises(PanelApiError) as untrusted:
        await PanelApi(async_get_clientsession(hass), url, TOKEN).info()
    assert untrusted.value.code == TLS_FAILED

    context, _ = pki.server_context(ELSEWHERE)
    server = await _serve(panel.app, context)
    try:
        with pytest.raises(PanelApiError) as wrong_host:
            await PanelApi(trusting_session, str(server.make_url("")), TOKEN).info()
    finally:
        await server.close()
    assert wrong_host.value.code == TLS_FAILED
    # No request reached the panel, and nothing was retried without verification.
    assert panel.requests == []


async def test_a_pinned_fingerprint_accepts_that_certificate_only(
    hass: HomeAssistant, tls_panel
) -> None:
    panel, url, fingerprint = tls_panel
    session = async_get_clientsession(hass)
    pinned = PanelApi(session, url, TOKEN, ssl=ssl_setting("fingerprint", _colons(fingerprint)))
    assert (await pinned.info())["api"] == 1
    assert len(panel.requests) == 1

    other = PanelApi(session, url, TOKEN, ssl=ssl_setting("fingerprint", "00" * 32))
    with pytest.raises(PanelApiError) as mismatch:
        await other.info()
    assert mismatch.value.code == FINGERPRINT_MISMATCH
    assert "00" * 32 not in mismatch.value.message and fingerprint not in mismatch.value.message
    assert len(panel.requests) == 1


async def test_disabled_verification_accepts_any_certificate(
    hass: HomeAssistant, tls_panel
) -> None:
    _, url, _ = tls_panel
    api = PanelApi(async_get_clientsession(hass), url, TOKEN, ssl=ssl_setting("disabled", None))
    assert (await api.info())["api"] == 1


async def test_redirects_are_not_followed(hass: HomeAssistant, tls_panel) -> None:
    panel, target, _ = tls_panel
    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", lambda r: web.HTTPFound(f"{target}{r.path}"))
    server = await _serve(app)
    try:
        api = PanelApi(async_get_clientsession(hass), str(server.make_url("")), TOKEN)
        with pytest.raises(PanelApiError) as redirect:
            await api.info()
        with pytest.raises(PanelApiError) as streamed:
            await api.open("GET", "media/photos/x.jpg")
    finally:
        await server.close()
    assert redirect.value.code == streamed.value.code == REDIRECT
    assert panel.requests == []


async def test_a_proxy_refusal_is_not_the_panels_own(hass: HomeAssistant, socket_enabled) -> None:
    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", lambda r: web.Response(status=403, text="Forbidden"))
    server = await _serve(app)
    try:
        with pytest.raises(PanelApiError) as refused:
            await PanelApi(async_get_clientsession(hass), str(server.make_url("")), TOKEN).info()
    finally:
        await server.close()
    assert (refused.value.status, refused.value.code) == (403, FORBIDDEN)


# -- options and runtime -----------------------------------------------------------


async def test_admin_step_pins_a_fingerprint_used_by_every_request(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    panel: str,
    tls_panel,
    hass_ws_client,
    hass_client,
) -> None:
    fake, url, fingerprint = tls_panel
    entry = await _add_entry(hass, panel, {CONF_LINKS: {PANEL_FRONT: REAL_FRONT}})
    form = await _admin_step(hass, entry)
    assert form["data_schema"]({})[CONF_API_VERIFY] == "system"

    user_input = {CONF_API_URL: url, CONF_API_TOKEN: TOKEN, "admin_pin": ROOT_PIN}
    untrusted = await hass.config_entries.options.async_configure(form["flow_id"], user_input)
    assert untrusted["errors"] == {"base": "tls_failed"}
    assert fake.requests == []

    malformed = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input | {CONF_API_VERIFY: "fingerprint", CONF_API_FINGERPRINT: "ab:cd"},
    )
    assert malformed["errors"] == {CONF_API_FINGERPRINT: "invalid_fingerprint"}

    plain_http = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input
        | {
            CONF_API_URL: url.replace("https://", "http://"),
            CONF_API_VERIFY: "fingerprint",
            CONF_API_FINGERPRINT: fingerprint,
        },
    )
    assert plain_http["errors"] == {CONF_API_URL: "https_required"}

    credentials = await hass.config_entries.options.async_configure(
        form["flow_id"], user_input | {CONF_API_URL: url.replace("https://", "https://u:p@")}
    )
    assert credentials["errors"] == {CONF_API_URL: "url_credentials"}

    changed = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input | {CONF_API_VERIFY: "fingerprint", CONF_API_FINGERPRINT: "11" * 32},
    )
    assert changed["errors"] == {"base": "fingerprint_mismatch"}
    assert fake.requests == []
    # The form keeps what was entered, so it can be corrected.
    shown = {str(k): k for k in changed["data_schema"].schema}
    assert shown[CONF_API_FINGERPRINT].description["suggested_value"] == "11" * 32

    done = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input
        | {CONF_API_VERIFY: "fingerprint", CONF_API_FINGERPRINT: f" {_colons(fingerprint)} "},
    )
    await hass.async_block_till_done()
    assert done["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == _options(
        url, **{CONF_API_VERIFY: "fingerprint", CONF_API_FINGERPRINT: fingerprint}
    )

    # Runtime JSON calls and streamed media use the pin too.
    client = await hass_ws_client(hass)
    reply = await ws(client, type="doormonitor/admin/info")
    assert reply["result"]["info"]["api"] == 1
    http = await hass_client()
    photo = await http.get(f"/api/doormonitor/{entry.entry_id}/media/photos/summer%202.jpg")
    assert photo.status == 200
    assert fake.requests[-1] == ("GET", "/api/v1/media/photos/summer 2.jpg", ROOT_ID)

    # Choosing another mode forgets the pin.
    form = await _admin_step(hass, entry)
    back = await hass.config_entries.options.async_configure(
        form["flow_id"], {CONF_API_URL: url, CONF_API_VERIFY: "disabled"}
    )
    await hass.async_block_till_done()
    assert back["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_API_FINGERPRINT not in entry.options
    assert entry.options[CONF_API_VERIFY] == "disabled"


async def test_a_changed_certificate_is_reported_at_runtime(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, panel: str, tls_panel, hass_ws_client
) -> None:
    fake, url, _ = tls_panel
    await _add_entry(
        hass,
        panel,
        _options(url, **{CONF_API_VERIFY: "fingerprint", CONF_API_FINGERPRINT: "22" * 32}),
    )
    client = await hass_ws_client(hass)
    result = (await ws(client, type="doormonitor/admin/info"))["result"]
    assert result["error"]["code"] == FINGERPRINT_MISMATCH
    assert TOKEN not in str(result)
    assert fake.requests == []
