"""Doorbell ring event entity."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DoorbellConfigEntry
from .entity import DoorbellEntity
from .hub import DoorbellHub

EVENT_TYPE_RING = "ring"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DoorbellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([DoorbellRingEvent(entry.runtime_data)])


class DoorbellRingEvent(DoorbellEntity, EventEntity):
    _attr_device_class = EventDeviceClass.DOORBELL
    _attr_event_types = [EVENT_TYPE_RING]
    _attr_name = "Ring"

    def __init__(self, hub: DoorbellHub) -> None:
        super().__init__(hub, "ring")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _on_ring(data: dict[str, Any]) -> None:
            self._trigger_event(EVENT_TYPE_RING, {"timestamp": data.get("timestamp")})
            self.async_write_ha_state()

        self.async_on_remove(self.hub.async_add_ring_listener(_on_ring))
