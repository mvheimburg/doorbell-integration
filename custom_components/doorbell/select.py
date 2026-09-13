"""Selects that send modes to the panel: party mode and house state."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DoorbellConfigEntry
from .const import HOUSE_STATES, PARTY_MODES
from .entity import DoorbellEntity
from .hub import DoorbellHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DoorbellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = entry.runtime_data
    async_add_entities([PartyModeSelect(hub), HouseStateSelect(hub)])


class PartyModeSelect(DoorbellEntity, SelectEntity):
    _attr_name = "Party mode"
    _attr_icon = "mdi:party-popper"
    _attr_options = PARTY_MODES

    def __init__(self, hub: DoorbellHub) -> None:
        super().__init__(hub, "party_mode")

    @property
    def current_option(self) -> str | None:
        return self.hub.state.party_mode

    async def async_select_option(self, option: str) -> None:
        await self.hub.async_set_party_mode(option)


class HouseStateSelect(DoorbellEntity, SelectEntity):
    _attr_name = "House state"
    _attr_icon = "mdi:home-switch"
    _attr_options = HOUSE_STATES

    def __init__(self, hub: DoorbellHub) -> None:
        super().__init__(hub, "house_state")

    @property
    def current_option(self) -> str | None:
        return self.hub.state.house_state

    async def async_select_option(self, option: str) -> None:
        await self.hub.async_set_house_state(option)
