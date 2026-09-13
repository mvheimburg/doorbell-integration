"""The Doorbell integration: a DoorMonitor panel as a Home Assistant device."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_DEVICE_ID,
    ATTR_MODE,
    ATTR_STATE,
    DOMAIN,
    HOUSE_STATES,
    PARTY_MODES,
    SERVICE_PURGE_MQTT_DISCOVERY,
    SERVICE_SET_HOUSE_STATE,
    SERVICE_SET_PARTY_MODE,
)
from .hub import DoorbellHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.EVENT,
    Platform.LOCK,
    Platform.SELECT,
    Platform.SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DoorbellConfigEntry = ConfigEntry[DoorbellHub]

_SERVICE_TARGET = {vol.Optional(ATTR_DEVICE_ID): cv.string}
SET_PARTY_MODE_SCHEMA = vol.Schema(
    {**_SERVICE_TARGET, vol.Required(ATTR_MODE): vol.In(PARTY_MODES)}
)
SET_HOUSE_STATE_SCHEMA = vol.Schema(
    {**_SERVICE_TARGET, vol.Required(ATTR_STATE): vol.In(HOUSE_STATES)}
)
PURGE_SCHEMA = vol.Schema(_SERVICE_TARGET)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register domain services once."""
    _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DoorbellConfigEntry) -> bool:
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT integration is not available")

    hub = DoorbellHub(hass, entry)
    await hub.async_setup()
    entry.runtime_data = hub

    _async_remove_stale_entities(hass, entry, hub)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DoorbellConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_unload()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: DoorbellConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


@callback
def _async_remove_stale_entities(
    hass: HomeAssistant, entry: DoorbellConfigEntry, hub: DoorbellHub
) -> None:
    """Drop lock/cover entities for doors or gates that were removed from the options."""
    registry = er.async_get(hass)
    valid = {f"{entry.entry_id}_lock_{door}" for door in hub.config.doors}
    valid.add(f"{entry.entry_id}_cover_{hub.config.gate_id}")
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.domain not in ("lock", "cover"):
            continue
        if reg_entry.unique_id not in valid:
            _LOGGER.info("Removing stale entity %s", reg_entry.entity_id)
            registry.async_remove(reg_entry.entity_id)


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SET_PARTY_MODE):
        return

    def _hubs() -> list[DoorbellHub]:
        return [
            entry.runtime_data
            for entry in hass.config_entries.async_loaded_entries(DOMAIN)
            if isinstance(entry.runtime_data, DoorbellHub)
        ]

    def _resolve(call: ServiceCall) -> DoorbellHub:
        hubs = _hubs()
        device_id = call.data.get(ATTR_DEVICE_ID)
        if device_id:
            for hub in hubs:
                if hub.device_id == device_id:
                    return hub
            raise ServiceValidationError(f"No doorbell with device_id {device_id}")
        if len(hubs) == 1:
            return hubs[0]
        if not hubs:
            raise ServiceValidationError("No doorbell is configured")
        raise ServiceValidationError("Several doorbells are configured; pass device_id")

    async def _set_party_mode(call: ServiceCall) -> None:
        await _resolve(call).async_set_party_mode(call.data[ATTR_MODE])

    async def _set_house_state(call: ServiceCall) -> None:
        await _resolve(call).async_set_house_state(call.data[ATTR_STATE])

    async def _purge(call: ServiceCall) -> None:
        await _resolve(call).async_purge_mqtt_discovery()

    hass.services.async_register(
        DOMAIN, SERVICE_SET_PARTY_MODE, _set_party_mode, schema=SET_PARTY_MODE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_HOUSE_STATE, _set_house_state, schema=SET_HOUSE_STATE_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_PURGE_MQTT_DISCOVERY, _purge, schema=PURGE_SCHEMA)
