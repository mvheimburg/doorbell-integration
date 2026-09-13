"""Base entity for the Doorbell integration."""

from __future__ import annotations

from homeassistant.helpers.entity import Entity

from .hub import DoorbellHub


class DoorbellEntity(Entity):
    """An entity belonging to the panel device; re-renders when the hub notifies."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: DoorbellHub, key: str) -> None:
        self.hub = hub
        self._attr_unique_id = f"{hub.entry.entry_id}_{key}"
        self._attr_device_info = hub.device_info

    @property
    def available(self) -> bool:
        # The legacy Python panel never publishes availability: treat unknown as online.
        return self.hub.state.available is not False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.hub.async_add_listener(self.async_write_ha_state))
