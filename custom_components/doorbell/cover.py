"""The gate/garage cover shown on the panel."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DoorbellConfigEntry
from .entity import DoorbellEntity
from .hub import DoorbellHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DoorbellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([GateCover(entry.runtime_data)])


class GateCover(DoorbellEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.GATE
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, hub: DoorbellHub) -> None:
        super().__init__(hub, f"cover_{hub.config.gate_id}")
        self._attr_name = hub.config.gate_id.replace("_", " ").capitalize()

    @property
    def is_closed(self) -> bool | None:
        state = self.hub.state.gate
        if state is None or state in ("unknown", "stopped"):
            return None
        return state == "closed"

    @property
    def is_opening(self) -> bool:
        return self.hub.state.gate == "opening"

    @property
    def is_closing(self) -> bool:
        return self.hub.state.gate == "closing"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "gate_id": self.hub.config.gate_id,
            "panel_state": self.hub.state.gate,
            "mapped_entity_id": self.hub.config.gate_entity,
        }

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.hub.async_open_gate()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.hub.async_close_gate()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.hub.async_stop_gate()
