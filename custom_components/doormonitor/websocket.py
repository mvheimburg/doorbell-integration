"""Admin websocket API for the DoorMonitor admin panel.

The panel's browser code never sees the API token: it calls these commands, and the integration
forwards them to the panel API as the configured doorbell admin. Errors come back with the
panel's own sentence as the message, and its ``code`` (or ``http-<status>``) as the error code.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback

from .admin import DoorMonitorAdmin
from .api import PanelApiError, api_path
from .const import DOMAIN

#: The panel API routes the admin panel may reach through ``doormonitor/admin/call``.
#: ``None`` matches any one path segment. Media uploads and downloads go through the HTTP views.
ALLOWED_ROUTES: tuple[tuple[str, tuple[str | None, ...]], ...] = (
    ("GET", ("info",)),
    ("GET", ("users",)),
    ("GET", ("users", None)),
    ("DELETE", ("users", None)),
    ("GET", ("appearance",)),
    ("PUT", ("modes", None, None)),
    ("GET", ("media",)),
    ("POST", ("media-groups",)),
    ("PATCH", ("media-groups", None)),
    ("DELETE", ("media-groups", None)),
    ("PATCH", ("media", "groups", None, None)),
    ("DELETE", ("media", "groups", None, None)),
    ("PATCH", ("media", "photos", None)),
    ("DELETE", ("media", "photos", None)),
)

NOT_CONFIGURED = "not-configured"


def _allowed(method: str, path: list[str]) -> bool:
    return any(
        method == allowed_method
        and len(path) == len(pattern)
        and all(
            part == literal or (literal is None and part)
            for part, literal in zip(path, pattern, strict=True)
        )
        for allowed_method, pattern in ALLOWED_ROUTES
    )


def _loaded_entries(hass: HomeAssistant) -> list:
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]


def _admin(hass: HomeAssistant, connection, msg) -> DoorMonitorAdmin | None:
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "No such DoorMonitor entry")
        return None
    if entry.runtime_data.admin is None:
        connection.send_error(
            msg["id"], NOT_CONFIGURED, "The admin connection is not set up under Configure"
        )
        return None
    return entry.runtime_data.admin


def _send_api_error(connection, msg_id: int, err: PanelApiError) -> None:
    connection.send_error(msg_id, err.code or f"http-{err.status}", err.message)


async def _ha_users(hass: HomeAssistant) -> list[dict[str, str]]:
    """The people who log in to Home Assistant: active users that are not system users."""
    users = [
        {"id": user.id, "name": user.name or user.id}
        for user in await hass.auth.async_get_users()
        if user.is_active and not user.system_generated
    ]
    return sorted(users, key=lambda user: user["name"].casefold())


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_info)
    websocket_api.async_register_command(hass, ws_call)
    websocket_api.async_register_command(hass, ws_users)
    websocket_api.async_register_command(hass, ws_save_user)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): "doormonitor/admin/info", vol.Optional("entry_id"): str}
)
@websocket_api.async_response
async def ws_info(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The entries, and for the chosen one (the first set up one by default) its ``GET /info``."""
    entries = _loaded_entries(hass)
    result: dict[str, Any] = {
        "entries": [
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "configured": entry.runtime_data.admin is not None,
            }
            for entry in entries
        ]
    }
    entry = next((e for e in entries if e.entry_id == msg.get("entry_id")), None) or next(
        (e for e in entries if e.runtime_data.admin is not None), entries[0] if entries else None
    )
    if entry is None:
        connection.send_result(msg["id"], result)
        return
    result["entry_id"] = entry.entry_id
    admin: DoorMonitorAdmin | None = entry.runtime_data.admin
    result["configured"] = admin is not None
    if admin is not None:
        result["actor_name"] = admin.actor_name
        try:
            result["info"] = await admin.api.info()
        except PanelApiError as err:
            result["error"] = {"code": err.code or f"http-{err.status}", "message": err.message}
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "doormonitor/admin/call",
        vol.Required("entry_id"): str,
        vol.Required("method"): vol.In(["GET", "POST", "PUT", "PATCH", "DELETE"]),
        vol.Required("path"): [str],
        vol.Optional("body"): vol.Any(dict, list),
    }
)
@websocket_api.async_response
async def ws_call(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Forward one JSON request to the panel API."""
    method, path = msg["method"], msg["path"]
    if not _allowed(method, path):
        connection.send_error(
            msg["id"], websocket_api.ERR_INVALID_FORMAT, f"{method} {'/'.join(path)} is not allowed"
        )
        return
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        result = await admin.api.request(method, api_path(path), msg.get("body"))
    except PanelApiError as err:
        _send_api_error(connection, msg["id"], err)
        return
    if method == "DELETE" and path[0] == "users":
        await admin.links.async_set(path[1], None)
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): "doormonitor/admin/users", vol.Required("entry_id"): str}
)
@websocket_api.async_response
async def ws_users(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """The doorbell's users, the Home Assistant users, and which of them are linked."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    try:
        users = await admin.api.request("GET", "users")
    except PanelApiError as err:
        _send_api_error(connection, msg["id"], err)
        return
    ha_users = await _ha_users(hass)
    await admin.links.async_prune(
        {user["id"] for user in users}, {user["id"] for user in ha_users}
    )
    connection.send_result(
        msg["id"], {"users": users, "ha_users": ha_users, "links": admin.links.links}
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "doormonitor/admin/save_user",
        vol.Required("entry_id"): str,
        vol.Optional("user_id"): str,
        vol.Required("user"): dict,
        vol.Optional("ha_user_id"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_save_user(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Create (no ``user_id``) or replace a doorbell user, then store its Home Assistant link."""
    if (admin := _admin(hass, connection, msg)) is None:
        return
    user_id = msg.get("user_id")
    ha_user_id = msg.get("ha_user_id")
    if ha_user_id:
        ha_user = await hass.auth.async_get_user(ha_user_id)
        if ha_user is None or ha_user.system_generated or not ha_user.is_active:
            connection.send_error(
                msg["id"], "unknown-ha-user", "That Home Assistant user no longer exists"
            )
            return
        owner = admin.links.owner_of(ha_user_id)
        if owner is not None and owner != user_id:
            connection.send_error(
                msg["id"],
                "ha-user-linked",
                "That Home Assistant user is already linked to another doorbell user",
            )
            return
    try:
        if user_id:
            stored = await admin.api.request("PUT", api_path(["users", user_id]), msg["user"])
        else:
            stored = await admin.api.request("POST", "users", msg["user"])
    except PanelApiError as err:
        _send_api_error(connection, msg["id"], err)
        return
    await admin.links.async_set(stored["id"], ha_user_id)
    connection.send_result(msg["id"], stored)
