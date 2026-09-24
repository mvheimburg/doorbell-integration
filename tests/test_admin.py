"""The admin panel: its registration, websocket API, media proxy and the options step behind it."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from aiohttp.test_utils import TestServer
from homeassistant.components.frontend import DATA_PANELS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doormonitor.const import (
    CONF_API_ACTOR,
    CONF_API_ACTOR_NAME,
    CONF_API_TOKEN,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_LINKS,
    DOMAIN,
)

from .conftest import PANEL_FRONT, REAL_FRONT
from .fake_panel import ROOT_ID, ROOT_PIN, TOKEN, FakePanel


@pytest.fixture
async def fake_panel(socket_enabled: None) -> AsyncGenerator[tuple[FakePanel, str]]:
    """A fake panel API on a real localhost port, so streaming and ``Range`` are exercised."""
    panel = FakePanel()
    server = TestServer(panel.app, host="127.0.0.1")
    await server.start_server()
    yield panel, str(server.make_url("")).rstrip("/")
    await server.close()


def _options(url: str, **extra: Any) -> dict[str, Any]:
    return {
        CONF_LINKS: {PANEL_FRONT: REAL_FRONT},
        CONF_API_URL: url,
        CONF_API_TOKEN: TOKEN,
        CONF_API_ACTOR: ROOT_ID,
        CONF_API_ACTOR_NAME: "root",
    } | extra


async def _add_entry(hass: HomeAssistant, device_id: str, options: dict) -> MockConfigEntry:
    await async_setup_component(hass, "http", {})
    hass.states.async_set(REAL_FRONT, "locked")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="doorbell",
        unique_id=device_id,
        data={CONF_DEVICE_ID: device_id},
        options=options,
        version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def admin_entry(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, panel: str, fake_panel
) -> MockConfigEntry:
    return await _add_entry(hass, panel, _options(fake_panel[1]))


async def ws(client, **message):
    await client.send_json_auto_id(message)
    return await client.receive_json()


# -- panel ---------------------------------------------------------------------


async def test_panel_is_for_admins_kept_on_reload_and_removed_with_the_entry(
    hass: HomeAssistant, admin_entry: MockConfigEntry
) -> None:
    panel = hass.data[DATA_PANELS]["doormonitor"]
    assert panel.require_admin is True
    custom = panel.config["_panel_custom"]
    assert custom["name"] == "doormonitor-admin-panel"
    assert custom["module_url"].startswith("/doormonitor_static/doormonitor-admin-panel.js?v=")

    hass.config_entries.async_update_entry(
        admin_entry, options={**admin_entry.options, CONF_LINKS: {}}
    )
    await hass.async_block_till_done()
    assert "doormonitor" in hass.data[DATA_PANELS]

    assert await hass.config_entries.async_unload(admin_entry.entry_id)
    await hass.async_block_till_done()
    assert "doormonitor" not in hass.data[DATA_PANELS]


# -- websocket -----------------------------------------------------------------


async def test_info_reports_the_panel_and_the_admin(
    hass: HomeAssistant, admin_entry: MockConfigEntry, hass_ws_client
) -> None:
    client = await hass_ws_client(hass)
    reply = await ws(client, type="doormonitor/admin/info")
    assert reply["success"]
    result = reply["result"]
    assert result["entries"] == [
        {"entry_id": admin_entry.entry_id, "title": "doorbell", "configured": True}
    ]
    assert result["entry_id"] == admin_entry.entry_id
    assert result["actor_name"] == "root"
    assert result["info"]["features"] == ["users", "appearance", "media-groups", "photos"]


async def test_info_without_admin_connection(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, panel: str, hass_ws_client
) -> None:
    entry = await _add_entry(hass, panel, {CONF_LINKS: {}})
    client = await hass_ws_client(hass)
    result = (await ws(client, type="doormonitor/admin/info"))["result"]
    assert result["configured"] is False
    assert "info" not in result
    call = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=entry.entry_id,
        method="GET",
        path=["users"],
    )
    assert call["error"]["code"] == "not-configured"


async def test_info_reports_a_bad_token(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, panel: str, fake_panel, hass_ws_client
) -> None:
    await _add_entry(hass, panel, _options(fake_panel[1], **{CONF_API_TOKEN: "wrong"}))
    client = await hass_ws_client(hass)
    result = (await ws(client, type="doormonitor/admin/info"))["result"]
    assert result["error"] == {"code": "bad-token", "message": "Bad API token"}


async def test_call_forwards_as_the_admin_and_only_allowed_routes(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel, hass_ws_client
) -> None:
    panel, _ = fake_panel
    client = await hass_ws_client(hass)
    reply = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=admin_entry.entry_id,
        method="PUT",
        path=["modes", "party", "halloween"],
        body={"theme": "doorbell", "mediaGroup": "bells"},
    )
    assert reply["success"], reply
    assert panel.modes[("party", "halloween")] == {"theme": "doorbell", "mediaGroup": "bells"}
    assert panel.requests[-1] == ("PUT", "/api/v1/modes/party/halloween", ROOT_ID)

    # File names are percent-encoded one segment at a time.
    reply = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=admin_entry.entry_id,
        method="DELETE",
        path=["media", "groups", "bells", "Ding Dong.wav"],
    )
    assert reply["success"], reply
    assert ("groups", "bells", "Ding Dong.wav") not in panel.files

    refused = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=admin_entry.entry_id,
        method="POST",
        path=["session"],
        body={"pin": ROOT_PIN},
    )
    assert refused["error"]["code"] == "invalid_format"


async def test_call_passes_the_panels_error_sentence(
    hass: HomeAssistant, admin_entry: MockConfigEntry, hass_ws_client
) -> None:
    client = await hass_ws_client(hass)
    reply = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=admin_entry.entry_id,
        method="DELETE",
        path=["users", ROOT_ID],
    )
    assert reply["error"] == {
        "code": "http-403",
        "message": "The root user can't be deleted",
    }


async def test_a_removed_admin_is_reported_as_not_admin(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel, hass_ws_client
) -> None:
    panel, _ = fake_panel
    panel.users[ROOT_ID]["accessLevel"] = "resident"
    client = await hass_ws_client(hass)
    reply = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=admin_entry.entry_id,
        method="GET",
        path=["media"],
    )
    assert reply["error"]["code"] == "not-admin"


async def test_non_admins_cannot_use_the_api(
    hass: HomeAssistant, admin_entry: MockConfigEntry, hass_ws_client, hass_read_only_access_token
) -> None:
    client = await hass_ws_client(hass, hass_read_only_access_token)
    reply = await ws(client, type="doormonitor/admin/info")
    assert reply["error"]["code"] == "unauthorized"


async def test_unreachable_panel(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, panel: str, hass_ws_client
) -> None:
    entry = await _add_entry(hass, panel, _options("http://127.0.0.1:9"))
    client = await hass_ws_client(hass)
    reply = await ws(
        client, type="doormonitor/admin/call", entry_id=entry.entry_id, method="GET", path=["media"]
    )
    assert reply["error"] == {"code": "unreachable", "message": "The panel is unreachable"}


# -- Home Assistant user links ---------------------------------------------------


def _new_user(name: str, pin: str) -> dict[str, Any]:
    return {
        "name": name,
        "pin": pin,
        "start": "2026-09-23T00:00:00Z",
        "end": None,
        "accessLevel": "resident",
        "bleData": {"phone": None, "watch": None, "misc": None},
    }


async def test_users_are_linked_to_home_assistant_users(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel, hass_ws_client
) -> None:
    panel, _ = fake_panel
    alex = await hass.auth.async_create_user("Alex")
    await hass.auth.async_create_system_user("Hidden system user")
    client = await hass_ws_client(hass)
    entry_id = admin_entry.entry_id

    saved = await ws(
        client,
        type="doormonitor/admin/save_user",
        entry_id=entry_id,
        user=_new_user("Alex", "5555"),
        ha_user_id=alex.id,
    )
    assert saved["success"], saved
    alex_doorbell = saved["result"]["id"]
    assert panel.users[alex_doorbell]["name"] == "Alex"

    listing = (await ws(client, type="doormonitor/admin/users", entry_id=entry_id))["result"]
    assert [u["name"] for u in listing["users"]] == ["Alex", "root"]
    names = [u["name"] for u in listing["ha_users"]]
    assert "Alex" in names
    assert "Hidden system user" not in names
    assert listing["links"] == {alex_doorbell: alex.id}

    # One Home Assistant user stands for one doorbell user.
    other = await ws(
        client,
        type="doormonitor/admin/save_user",
        entry_id=entry_id,
        user=_new_user("Sam", "6666"),
        ha_user_id=alex.id,
    )
    assert other["error"]["code"] == "ha-user-linked"
    assert [u["name"] for u in panel.users.values()] == ["root", "Alex"]

    # A refused save stores no link.
    refused = await ws(
        client,
        type="doormonitor/admin/save_user",
        entry_id=entry_id,
        user_id=alex_doorbell,
        user=_new_user("Alex", ROOT_PIN),
        ha_user_id=None,
    )
    assert refused["error"] == {"code": "http-409", "message": "PIN already in use"}
    assert admin_entry.runtime_data.admin.links.links == {alex_doorbell: alex.id}

    # Unlinking on edit, and deleting the doorbell user, both drop the link.
    await ws(
        client,
        type="doormonitor/admin/save_user",
        entry_id=entry_id,
        user_id=alex_doorbell,
        user=_new_user("Alex", "5555"),
        ha_user_id=None,
    )
    assert admin_entry.runtime_data.admin.links.links == {}
    await ws(
        client,
        type="doormonitor/admin/save_user",
        entry_id=entry_id,
        user_id=alex_doorbell,
        user=_new_user("Alex", "5555"),
        ha_user_id=alex.id,
    )
    deleted = await ws(
        client,
        type="doormonitor/admin/call",
        entry_id=entry_id,
        method="DELETE",
        path=["users", alex_doorbell],
    )
    assert deleted["success"]
    assert admin_entry.runtime_data.admin.links.links == {}


async def test_links_to_removed_users_are_pruned_and_survive_a_reload(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel, hass_ws_client
) -> None:
    panel, _ = fake_panel
    alex = await hass.auth.async_create_user("Alex")
    sam = await hass.auth.async_create_user("Sam")
    client = await hass_ws_client(hass)
    entry_id = admin_entry.entry_id
    ids = []
    for name, pin, ha_user in (("Alex", "5555", alex), ("Sam", "6666", sam)):
        reply = await ws(
            client,
            type="doormonitor/admin/save_user",
            entry_id=entry_id,
            user=_new_user(name, pin),
            ha_user_id=ha_user.id,
        )
        ids.append(reply["result"]["id"])

    await hass.config_entries.async_reload(entry_id)
    await hass.async_block_till_done()
    assert admin_entry.runtime_data.admin.links.links == {ids[0]: alex.id, ids[1]: sam.id}

    del panel.users[ids[0]]  # deleted at the doorbell itself
    await hass.auth.async_remove_user(sam)
    listing = (await ws(client, type="doormonitor/admin/users", entry_id=entry_id))["result"]
    assert listing["links"] == {}


# -- media proxy ----------------------------------------------------------------


async def _signed(client, path: str) -> str:
    reply = await ws(client, type="auth/sign_path", path=path, expires=60)
    return reply["result"]["path"]


async def test_media_download_is_proxied_with_range(
    hass: HomeAssistant,
    admin_entry: MockConfigEntry,
    fake_panel,
    hass_ws_client,
    hass_client,
    hass_client_no_auth,
) -> None:
    panel, _ = fake_panel
    data = panel.files[("groups", "bells", "Ding Dong.wav")]
    base = f"/api/doormonitor/{admin_entry.entry_id}/media"
    http = await hass_client()

    whole = await http.get(f"{base}/groups/bells/Ding%20Dong.wav")
    assert whole.status == 200
    assert await whole.read() == data
    assert whole.headers["Accept-Ranges"] == "bytes"

    part = await http.get(f"{base}/groups/bells/Ding%20Dong.wav", headers={"Range": "bytes=4-9"})
    assert part.status == 206
    assert await part.read() == data[4:10]
    assert part.headers["Content-Range"] == f"bytes 4-9/{len(data)}"
    assert panel.requests[-1][2] == ROOT_ID

    # What <audio src> uses: a signed path, without the bearer header.
    assert await async_setup_component(hass, "auth", {})
    ws_client = await hass_ws_client(hass)
    signed = await _signed(ws_client, f"{base}/photos/summer%202.jpg")
    anonymous = await hass_client_no_auth()
    photo = await anonymous.get(signed)
    assert photo.status == 200
    assert await photo.read() == panel.files[("photos", "summer 2.jpg")]
    assert (await anonymous.get(f"{base}/photos/summer%202.jpg")).status == 401

    missing = await http.get(f"{base}/photos/nope.jpg")
    assert missing.status == 404
    assert (await missing.json())["error"] == "File not found"


async def test_media_upload_is_streamed_to_the_panel(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel, hass_client
) -> None:
    panel, _ = fake_panel
    base = f"/api/doormonitor/{admin_entry.entry_id}/media"
    http = await hass_client()

    stored = await http.put(f"{base}/groups/bells/ring%21.wav", data=b"RIFFnew")
    assert stored.status == 201
    assert await stored.json() == {"name": "ring_.wav"}
    assert panel.files[("groups", "bells", "ring_.wav")] == b"RIFFnew"

    taken = await http.put(f"{base}/groups/bells/ring_.wav", data=b"RIFFx")
    assert taken.status == 409
    assert (await taken.json())["error"] == "ring_.wav already exists"

    replaced = await http.put(f"{base}/groups/bells/ring_.wav?overwrite=true", data=b"RIFFx")
    assert replaced.status == 201
    assert panel.files[("groups", "bells", "ring_.wav")] == b"RIFFx"

    assert (await http.put(f"{base}/elsewhere/x.wav", data=b"x")).status == 404


async def test_media_is_for_admins_only(
    hass: HomeAssistant, admin_entry: MockConfigEntry, hass_client, hass_read_only_access_token
) -> None:
    http = await hass_client(hass_read_only_access_token)
    base = f"/api/doormonitor/{admin_entry.entry_id}/media"
    assert (await http.get(f"{base}/photos/summer%202.jpg")).status == 401
    assert (await http.put(f"{base}/photos/x.jpg", data=b"x")).status == 401


# -- options: the admin connection -----------------------------------------------


async def _admin_step(hass: HomeAssistant, entry: MockConfigEntry) -> dict:
    result = await hass.config_entries.options.async_init(entry.entry_id)
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "admin"}
    )


async def test_admin_step_stores_the_admin_not_the_pin(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, panel: str, fake_panel
) -> None:
    _, url = fake_panel
    entry = await _add_entry(hass, panel, {CONF_LINKS: {PANEL_FRONT: REAL_FRONT}})
    assert entry.runtime_data.admin is None

    form = await _admin_step(hass, entry)
    assert form["type"] is FlowResultType.FORM
    assert form["step_id"] == "admin"

    retry = await hass.config_entries.options.async_configure(
        form["flow_id"], {CONF_API_URL: url, CONF_API_TOKEN: TOKEN}
    )
    assert retry["errors"] == {"admin_pin": "pin_required"}

    wrong = await hass.config_entries.options.async_configure(
        form["flow_id"], {CONF_API_URL: url, CONF_API_TOKEN: TOKEN, "admin_pin": "0000"}
    )
    assert wrong["errors"] == {"base": "invalid_pin"}

    bad_token = await hass.config_entries.options.async_configure(
        form["flow_id"], {CONF_API_URL: url, CONF_API_TOKEN: "nope", "admin_pin": ROOT_PIN}
    )
    assert bad_token["errors"] == {"base": "invalid_token"}

    done = await hass.config_entries.options.async_configure(
        form["flow_id"],
        {CONF_API_URL: f"{url}/api/v1/", CONF_API_TOKEN: TOKEN, "admin_pin": ROOT_PIN},
    )
    await hass.async_block_till_done()
    assert done["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == _options(url, api_verify="system")
    assert ROOT_PIN not in str(entry.options.values())
    assert entry.runtime_data.admin is not None


async def test_admin_step_keeps_token_and_admin_and_can_remove_them(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel
) -> None:
    panel, url = fake_panel
    form = await _admin_step(hass, admin_entry)
    kept = await hass.config_entries.options.async_configure(form["flow_id"], {CONF_API_URL: url})
    await hass.async_block_till_done()
    assert kept["type"] is FlowResultType.CREATE_ENTRY
    # An entry from before the setting existed gets system trust, as it had.
    assert admin_entry.options == _options(url, api_verify="system")

    # The admin was demoted meanwhile: a PIN is needed again.
    panel.users[ROOT_ID]["accessLevel"] = "guest"
    form = await _admin_step(hass, admin_entry)
    gone = await hass.config_entries.options.async_configure(form["flow_id"], {CONF_API_URL: url})
    assert gone["errors"] == {"base": "actor_gone"}

    removed = await hass.config_entries.options.async_configure(form["flow_id"], {})
    await hass.async_block_till_done()
    assert removed["type"] is FlowResultType.CREATE_ENTRY
    assert admin_entry.options == {CONF_LINKS: {PANEL_FRONT: REAL_FRONT}}
    assert admin_entry.runtime_data.admin is None


async def test_admin_step_reports_an_unreachable_panel(
    hass: HomeAssistant, admin_entry: MockConfigEntry
) -> None:
    form = await _admin_step(hass, admin_entry)
    result = await hass.config_entries.options.async_configure(
        form["flow_id"], {CONF_API_URL: "http://127.0.0.1:9", "admin_pin": ROOT_PIN}
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_links_step_keeps_the_admin_connection(
    hass: HomeAssistant, admin_entry: MockConfigEntry, fake_panel
) -> None:
    result = await hass.config_entries.options.async_init(admin_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "links"}
    )
    await hass.config_entries.options.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert admin_entry.options == _options(fake_panel[1], **{CONF_LINKS: {}})
