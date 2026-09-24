"""Client for the DoorMonitor panel API v1 (``/api/v1``, bearer token plus ``X-Doorbell-Actor``).

The API is specified in the panel's ``API.md``. The token stays here, on the server; the admin
panel reaches the API only through this integration's websocket commands and media views.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterable
from typing import Any, Literal
from urllib.parse import quote

import aiohttp
from yarl import URL

PREFIX = "/api/v1"
#: JSON requests are small; a panel that does not answer within this is down or restarting.
JSON_TIMEOUT = aiohttp.ClientTimeout(total=15)
#: Media is streamed, so only connecting is bounded.
STREAM_TIMEOUT = aiohttp.ClientTimeout(total=None, sock_connect=10, sock_read=60)

#: Error codes that are not the panel's own.
UNREACHABLE = "unreachable"
BAD_RESPONSE = "bad-response"
#: The certificate failed normal validation (issuer, expiry or host name).
TLS_FAILED = "tls-failed"
#: The certificate is not the one whose fingerprint is pinned.
FINGERPRINT_MISMATCH = "fingerprint-mismatch"
#: Something answered 401 or 403 without the panel's error body, e.g. a reverse proxy.
UNAUTHORIZED = "unauthorized"
FORBIDDEN = "forbidden"
#: A redirect, which is never followed so the token cannot leave for another origin.
REDIRECT = "redirect"

#: How the panel's TLS certificate is checked (options). Entries without it use system trust.
VERIFY_SYSTEM = "system"
VERIFY_FINGERPRINT = "fingerprint"
VERIFY_DISABLED = "disabled"
VERIFY_MODES = (VERIFY_SYSTEM, VERIFY_FINGERPRINT, VERIFY_DISABLED)

type SslSetting = Literal[True, False] | aiohttp.Fingerprint


class PanelApiError(Exception):
    """An answer the panel refused, or no answer at all (``status`` 0)."""

    def __init__(self, status: int, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code


def normalize_url(url: str) -> str:
    """``http://host:8081/api/v1/`` and ``http://host:8081`` both give ``http://host:8081``."""
    url = url.strip().rstrip("/")
    if url.endswith(PREFIX):
        url = url[: -len(PREFIX)].rstrip("/")
    return url


def url_problem(url: str) -> str | None:
    """Why a normalized panel URL can't be used, as an options-form error key, or ``None``."""
    try:
        parsed = URL(url)
    except ValueError:
        return "invalid_url"
    if parsed.scheme not in ("http", "https") or not parsed.host:
        return "invalid_url"
    if parsed.user is not None or parsed.password is not None:
        return "url_credentials"
    return None


def normalize_fingerprint(value: str) -> str | None:
    """A SHA-256 fingerprint as 64 lower-case hex digits; colons and spaces around are optional.

    ``None`` when it is not one.
    """
    digits = value.strip().replace(":", "").lower()
    return digits if re.fullmatch(r"[0-9a-f]{64}", digits) else None


def ssl_setting(mode: str | None, fingerprint: str | None) -> SslSetting:
    """What each request passes as ``ssl=`` for a verification mode.

    System trust leaves HA's session to verify normally; a pin checks the certificate itself,
    instead of its issuer and host name. An unusable pin raises rather than weakening the check.
    """
    if mode == VERIFY_DISABLED:
        return False
    if mode == VERIFY_FINGERPRINT:
        digits = normalize_fingerprint(fingerprint or "")
        if digits is None:
            raise ValueError("The pinned certificate fingerprint is not a SHA-256 fingerprint")
        return aiohttp.Fingerprint(bytes.fromhex(digits))
    return True


def api_path(segments: list[str]) -> str:
    """Join path segments, percent-encoding each (file names may hold spaces)."""
    return "/".join(quote(segment, safe="") for segment in segments)


async def error_from(response: aiohttp.ClientResponse) -> PanelApiError:
    """The panel's ``{"error", "code"}`` body as an exception."""
    message = f"The panel answered {response.status}"
    code = None
    try:
        body = await response.json(content_type=None)
    except (ValueError, aiohttp.ClientError):
        body = None
    if isinstance(body, dict) and "error" in body:
        message = str(body.get("error") or message)
        code = body.get("code")
    elif response.status == 401:
        code = UNAUTHORIZED
    elif response.status == 403:
        code = FORBIDDEN
    return PanelApiError(response.status, message, code if isinstance(code, str) else None)


def redirect_error(response: aiohttp.ClientResponse) -> PanelApiError:
    return PanelApiError(
        response.status, f"The panel answered with a redirect ({response.status})", REDIRECT
    )


def connection_error(err: aiohttp.ClientError | TimeoutError) -> PanelApiError:
    """Tell a refused certificate apart from a panel that can't be reached at all.

    Neither message holds the token, nor the fingerprint a mismatching server presented: that one
    must be verified independently, never copied from here.
    """
    if isinstance(err, aiohttp.ServerFingerprintMismatch):
        return PanelApiError(
            0,
            "The panel's TLS certificate is not the one whose fingerprint is pinned",
            FINGERPRINT_MISMATCH,
        )
    if isinstance(err, aiohttp.ClientSSLError):
        cause = err.os_error
        reason = getattr(cause, "verify_message", None) or getattr(cause, "reason", None) or cause
        message = f"The panel's TLS certificate was not accepted: {reason}"
        return PanelApiError(0, message, TLS_FAILED)
    return PanelApiError(0, "The panel is unreachable", UNREACHABLE)


class PanelApi:
    """One panel, one token, and optionally the admin the requests act for.

    Every request, the setup check included, carries the same ``ssl`` setting, and redirects are
    not followed. HA's shared session is used as it is: its own TLS policy is never changed.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        token: str,
        actor: str | None = None,
        *,
        ssl: SslSetting = True,
    ) -> None:
        self._session = session
        self.url = normalize_url(url)
        self._token = token
        self.actor = actor
        self._ssl = ssl

    def _url(self, path: str) -> URL:
        return URL(f"{self.url}{PREFIX}/{path}", encoded=True)

    def _headers(self, actor: bool) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._token}"}
        if actor and self.actor:
            headers["X-Doorbell-Actor"] = self.actor
        return headers

    async def request(self, method: str, path: str, body: Any = None, *, actor: bool = True) -> Any:
        """Send a JSON request; returns the decoded answer, or ``None`` for 204."""
        kwargs: dict[str, Any] = {
            "headers": self._headers(actor),
            "timeout": JSON_TIMEOUT,
            "ssl": self._ssl,
            "allow_redirects": False,
        }
        if body is not None:
            kwargs["json"] = body
        try:
            async with self._session.request(method, self._url(path), **kwargs) as response:
                if 300 <= response.status < 400:
                    raise redirect_error(response)
                if response.status >= 400:
                    raise await error_from(response)
                if response.status == 204:
                    return None
                try:
                    return await response.json(content_type=None)
                except ValueError as err:
                    raise PanelApiError(
                        response.status, "The panel sent an answer that isn't JSON", BAD_RESPONSE
                    ) from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise connection_error(err) from err

    async def open(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        data: AsyncIterable[bytes] | None = None,
    ) -> aiohttp.ClientResponse:
        """Start a streamed media request. The caller reads and releases the response."""
        try:
            response = await self._session.request(
                method,
                self._url(path),
                headers={**(headers or {}), **self._headers(True)},
                params=params,
                data=data,
                timeout=STREAM_TIMEOUT,
                ssl=self._ssl,
                allow_redirects=False,
            )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise connection_error(err) from err
        if 300 <= response.status < 400:
            response.release()
            raise redirect_error(response)
        return response

    async def info(self) -> dict[str, Any]:
        return await self.request("GET", "info", actor=False)

    async def session(self, pin: str) -> dict[str, Any]:
        """The admin with this PIN (``POST /session``)."""
        return await self.request("POST", "session", {"pin": pin}, actor=False)
