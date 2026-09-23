"""HTTP views that proxy the panel's media files for the admin panel.

``GET`` serves a file for audio, video and image previews. The browser loads these by URL, so
the admin panel signs each path (``auth/sign_path``). ``Range`` is passed through so players can
seek. ``PUT`` streams an upload to the panel without buffering it; the panel checks the file.
"""

from __future__ import annotations

from http import HTTPStatus

from aiohttp import web
from homeassistant.components.http import KEY_HASS_USER, HomeAssistantView
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .api import PanelApiError, api_path, error_from
from .const import DOMAIN

URL = f"/api/{DOMAIN}/{{entry_id}}/media/{{rest:.+}}"
#: Request headers a download passes on to the panel.
_FORWARD_REQUEST = ("Range", "If-Range")
#: Response headers a download passes back to the browser.
_FORWARD_RESPONSE = (
    "Content-Type",
    "Content-Length",
    "Content-Range",
    "Accept-Ranges",
    "Cache-Control",
    "Last-Modified",
    "ETag",
)
_CHUNK = 64 * 1024


def _segments(rest: str) -> list[str] | None:
    """``groups/<id>/<name>`` or ``photos/<name>``, as path segments."""
    parts = rest.split("/")
    if len(parts) == 3 and parts[0] == "groups" and all(parts):
        return parts
    if len(parts) == 2 and parts[0] == "photos" and parts[1]:
        return parts
    return None


def _error(status: int, message: str, code: str | None = None) -> web.Response:
    body = {"error": message}
    if code:
        body["code"] = code
    return web.json_response(body, status=status)


class MediaView(HomeAssistantView):
    url = URL
    name = f"api:{DOMAIN}:media"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    def _admin(self, request: web.Request, entry_id: str):
        if not request[KEY_HASS_USER].is_admin:
            return _error(HTTPStatus.UNAUTHORIZED, "Only administrators can manage the doorbell")
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if (
            entry is None
            or entry.domain != DOMAIN
            or entry.state is not ConfigEntryState.LOADED
            or entry.runtime_data.admin is None
        ):
            return _error(HTTPStatus.NOT_FOUND, "No such DoorMonitor entry")
        return entry.runtime_data.admin

    async def get(self, request: web.Request, entry_id: str, rest: str) -> web.StreamResponse:
        admin = self._admin(request, entry_id)
        if isinstance(admin, web.Response):
            return admin
        if (segments := _segments(rest)) is None:
            return _error(HTTPStatus.NOT_FOUND, "File not found")
        headers = {h: request.headers[h] for h in _FORWARD_REQUEST if h in request.headers}
        try:
            upstream = await admin.api.open("GET", api_path(["media", *segments]), headers=headers)
        except PanelApiError as err:
            return _error(HTTPStatus.BAD_GATEWAY, err.message, err.code)
        try:
            if upstream.status >= 400:
                err = await error_from(upstream)
                return _error(upstream.status, err.message, err.code)
            response = web.StreamResponse(
                status=upstream.status,
                headers={
                    h: upstream.headers[h] for h in _FORWARD_RESPONSE if h in upstream.headers
                },
            )
            await response.prepare(request)
            async for chunk in upstream.content.iter_chunked(_CHUNK):
                await response.write(chunk)
            await response.write_eof()
            return response
        finally:
            upstream.release()

    async def put(self, request: web.Request, entry_id: str, rest: str) -> web.Response:
        admin = self._admin(request, entry_id)
        if isinstance(admin, web.Response):
            return admin
        if (segments := _segments(rest)) is None:
            return _error(HTTPStatus.NOT_FOUND, "Unknown upload target")
        params = {"overwrite": "true"} if request.query.get("overwrite") == "true" else None

        async def body():
            async for chunk in request.content.iter_chunked(_CHUNK):
                yield chunk

        try:
            upstream = await admin.api.open(
                "PUT",
                api_path(["media", *segments]),
                headers={"Content-Type": request.content_type or "application/octet-stream"},
                params=params,
                data=body(),
            )
        except PanelApiError as err:
            return _error(HTTPStatus.BAD_GATEWAY, err.message, err.code)
        try:
            if upstream.status >= 400:
                err = await error_from(upstream)
                return _error(upstream.status, err.message, err.code)
            return web.json_response(await upstream.json(content_type=None), status=upstream.status)
        finally:
            upstream.release()
