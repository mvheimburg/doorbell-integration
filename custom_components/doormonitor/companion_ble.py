"""Companion app transmitter discovery for the admin user form."""

import re

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

_BEACON = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
    r"_([0-9]{1,5})_([0-9]{1,5})"
)


@callback
def companion_beacons(hass: HomeAssistant, user_id: str) -> list[dict[str, str]]:
    """Return panel-formatted beacon IDs, joined by registration rather than display names."""
    registry = er.async_get(hass)
    devices = dr.async_get(hass)
    found: dict[str, dict[str, str]] = {}
    for entry in hass.config_entries.async_entries("mobile_app"):
        if entry.data.get("user_id") != user_id or entry.disabled_by:
            continue
        webhook = entry.data.get("webhook_id")
        if not webhook:
            continue
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
            if (
                entity.domain != "sensor"
                or entity.platform != "mobile_app"
                or entity.unique_id != f"{webhook}_ble_emitter"
                or entity.disabled_by
            ):
                continue
            state = hass.states.get(entity.entity_id)
            if (
                state is None
                or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE)
                or state.attributes.get("Supports transmitter") is False
            ):
                continue
            value = state.attributes.get("id")
            if not isinstance(value, str) or not (match := _BEACON.fullmatch(value)):
                continue
            uuid, major, minor = match.groups()
            if int(major) > 65535 or int(minor) > 65535:
                continue
            beacon_id = f"{uuid.replace("-", "").lower()}_{int(major)}_{int(minor)}"
            device = devices.async_get(entity.device_id) if entity.device_id else None
            if device is not None and device.disabled_by:
                continue
            name = (device.name_by_user or device.name) if device else None
            found.setdefault(beacon_id, {"name": name or entry.title, "id": beacon_id})
    return sorted(found.values(), key=lambda beacon: (beacon["name"].casefold(), beacon["id"]))
