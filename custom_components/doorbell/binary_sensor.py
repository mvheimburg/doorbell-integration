"""Binary sensors: bell pressed pulse and panel connectivity."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
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
    hub = entry.runtime_data
    async_add_entities([BellPressedSensor(hub), ConnectivitySensor(hub)])


class BellPressedSensor(DoorbellEntity, BinarySensorEntity):
    _attr_name = "Bell pressed"
    _attr_icon = "mdi:bell-ring"

    def __init__(self, hub: DoorbellHub) -> None:
        super().__init__(hub, "bell_pressed")

    @property
    def is_on(self) -> bool:
        return self.hub.state.bell_pressed


class ConnectivitySensor(DoorbellEntity, BinarySensorEntity):
    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub: DoorbellHub) -> None:
        super().__init__(hub, "connectivity")

    @property
    def available(self) -> bool:
        return True  # this sensor reports availability, so it is always available itself

    @property
    def is_on(self) -> bool:
        return self.hub.state.available is not False
