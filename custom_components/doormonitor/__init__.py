"""The DoorMonitor integration: keep a DoorMonitor panel's doors and gate in sync with real ones,
and manage the panel's users, appearance and media from an admin panel in Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from . import links, panel, websocket
from .admin import DoorMonitorData, async_create_admin
from .const import CONF_DEVICE_ID, CONF_LINKS, DOMAIN
from .media import MediaView
from .sync import PanelSync, panel_entity_ids

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DoorMonitorConfigEntry = ConfigEntry[DoorMonitorData]

#: Set while an entry reloads after its options changed, so the panel is kept.
_RELOADING = (DOMAIN, "reloading")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    websocket.async_register(hass)
    if hass.http is not None:
        hass.http.register_view(MediaView(hass))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> bool:
    device_id = entry.data[CONF_DEVICE_ID]
    if dr.async_get(hass).async_get(device_id) is None:
        raise ConfigEntryError(
            f"Panel device {device_id} no longer exists; remove and re-add the integration"
        )

    panel_entities = set(panel_entity_ids(hass, device_id))
    door_links: dict[str, str] = {}
    for panel_entity, real in (entry.options.get(CONF_LINKS) or {}).items():
        if panel_entity in panel_entities:
            door_links[panel_entity] = real
        else:
            _LOGGER.warning(
                "%s: %s is no longer on the panel, not syncing it", entry.title, panel_entity
            )

    admin = await async_create_admin(hass, entry)
    sync = PanelSync(hass, entry.title, door_links)
    sync.async_start()
    entry.runtime_data = DoorMonitorData(sync, admin)
    entry.async_on_unload(sync.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await panel.async_register(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> bool:
    # Keep the panel through an options reload; drop it with the last entry.
    reloading = hass.data.get(_RELOADING, set())
    if entry.entry_id not in reloading and not [
        other
        for other in hass.config_entries.async_loaded_entries(DOMAIN)
        if other.entry_id != entry.entry_id
    ]:
        panel.async_unregister(hass)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> None:
    await links.async_remove(hass, entry.entry_id)


async def _async_update_listener(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> None:
    reloading = hass.data.setdefault(_RELOADING, set())
    reloading.add(entry.entry_id)
    try:
        await hass.config_entries.async_reload(entry.entry_id)
    finally:
        reloading.discard(entry.entry_id)
