"""The admin side of a config entry: the panel API client and the Home Assistant user links."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PanelApi, ssl_setting
from .const import (
    CONF_API_ACTOR,
    CONF_API_ACTOR_NAME,
    CONF_API_FINGERPRINT,
    CONF_API_TOKEN,
    CONF_API_URL,
    CONF_API_VERIFY,
)
from .links import UserLinks
from .sync import PanelSync


@dataclass
class DoorMonitorAdmin:
    api: PanelApi
    #: Name of the doorbell admin the integration acts as, when it was chosen.
    actor_name: str
    links: UserLinks


@dataclass
class DoorMonitorData:
    sync: PanelSync
    #: ``None`` until the admin connection is set up under Configure.
    admin: DoorMonitorAdmin | None


async def async_create_admin(hass: HomeAssistant, entry: ConfigEntry) -> DoorMonitorAdmin | None:
    options = entry.options
    if not (options.get(CONF_API_URL) and options.get(CONF_API_TOKEN)):
        return None
    api = PanelApi(
        async_get_clientsession(hass),
        options[CONF_API_URL],
        options[CONF_API_TOKEN],
        options.get(CONF_API_ACTOR),
        ssl=ssl_setting(options.get(CONF_API_VERIFY), options.get(CONF_API_FINGERPRINT)),
    )
    links = UserLinks(hass, entry.entry_id)
    await links.async_load()
    return DoorMonitorAdmin(api, options.get(CONF_API_ACTOR_NAME) or "", links)
