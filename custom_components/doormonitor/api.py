"""Client for the DoorMonitor panel API v1 (``/api/v1``, bearer token plus ``X-Doorbell-Actor``).

The API is specified in the panel's ``API.md``. The token stays here, on the server; the admin
panel reaches the API only through this integration's websocket commands and media views.
"""

from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any
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
    if isinstance(body, dict):
        message = str(body.get("error") or message)
        code = body.get("code")
    return PanelApiError(response.status, message, code if isinstance(code, str) else None)


class PanelApi:
    """One panel, one token, and optionally the admin the requests act for."""

    def __init__(
        self, session: aiohttp.ClientSession, url: str, token: str, actor: str | None = None
    ) -> None:
        self._session = session
        self.url = normalize_url(url)
        self._token = token
        self.actor = actor

    def _url(self, path: str) -> URL:
        return URL(f"{self.url}{PREFIX}/{path}", encoded=True)

    def _headers(self, actor: bool) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._token}"}
        if actor and self.actor:
            headers["X-Doorbell-Actor"] = self.actor
        return headers

    async def request(
        self, method: str, path: str, body: Any = None, *, actor: bool = True
    ) -> Any:
        """Send a JSON request; returns the decoded answer, or ``None`` for 204."""
        kwargs: dict[str, Any] = {"headers": self._headers(actor), "timeout": JSON_TIMEOUT}
        if body is not None:
            kwargs["json"] = body
        try:
            async with self._session.request(method, self._url(path), **kwargs) as response:
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
            raise PanelApiError(0, "The panel is unreachable", UNREACHABLE) from err

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
            return await self._session.request(
                method,
                self._url(path),
                headers={**(headers or {}), **self._headers(True)},
                params=params,
                data=data,
                timeout=STREAM_TIMEOUT,
            )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise PanelApiError(0, "The panel is unreachable", UNREACHABLE) from err

    async def info(self) -> dict[str, Any]:
        return await self.request("GET", "info", actor=False)

    async def session(self, pin: str) -> dict[str, Any]:
        """The admin with this PIN (``POST /session``)."""
        return await self.request("POST", "session", {"pin": pin}, actor=False)
