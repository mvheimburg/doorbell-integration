"""The DoorMonitor integration: keep a DoorMonitor panel's doors and gate in sync with real ones."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import CONF_DEVICE_ID, CONF_LINKS, DOMAIN
from .sync import PanelSync, panel_entity_ids

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DoorMonitorConfigEntry = ConfigEntry[PanelSync]


async def async_setup_entry(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> bool:
    device_id = entry.data[CONF_DEVICE_ID]
    if dr.async_get(hass).async_get(device_id) is None:
        raise ConfigEntryError(
            f"Panel device {device_id} no longer exists; remove and re-add the integration"
        )

    panel_entities = set(panel_entity_ids(hass, device_id))
    links: dict[str, str] = {}
    for panel, real in (entry.options.get(CONF_LINKS) or {}).items():
        if panel in panel_entities:
            links[panel] = real
        else:
            _LOGGER.warning("%s: %s is no longer on the panel, not syncing it", entry.title, panel)

    sync = PanelSync(hass, entry.title, links)
    sync.async_start()
    entry.runtime_data = sync
    entry.async_on_unload(sync.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> bool:
    return True


async def _async_update_listener(hass: HomeAssistant, entry: DoorMonitorConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
