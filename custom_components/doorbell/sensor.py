"""Sensors: last ring, logged-in user, login method, active page."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DoorbellConfigEntry
from .const import ACTIVE_PAGES, LOGIN_METHODS
from .entity import DoorbellEntity
from .hub import DoorbellHub, DoorbellState


@dataclass(frozen=True, kw_only=True)
class DoorbellSensorDescription(SensorEntityDescription):
    value_fn: Callable[[DoorbellState], datetime | str | None]


SENSORS: tuple[DoorbellSensorDescription, ...] = (
    DoorbellSensorDescription(
        key="last_ring",
        name="Last ring",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:bell",
        value_fn=lambda s: s.last_ring,
    ),
    DoorbellSensorDescription(
        key="logged_in_user",
        name="Logged in user",
        icon="mdi:account",
        value_fn=lambda s: s.logged_in_user or None,
    ),
    DoorbellSensorDescription(
        key="login_method",
        name="Login method",
        device_class=SensorDeviceClass.ENUM,
        options=LOGIN_METHODS,
        icon="mdi:login",
        value_fn=lambda s: s.login_method,
    ),
    DoorbellSensorDescription(
        key="active_page",
        name="Active page",
        device_class=SensorDeviceClass.ENUM,
        options=ACTIVE_PAGES,
        icon="mdi:tablet-dashboard",
        value_fn=lambda s: s.active_page,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DoorbellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = entry.runtime_data
    async_add_entities(DoorbellSensor(hub, description) for description in SENSORS)


class DoorbellSensor(DoorbellEntity, SensorEntity):
    entity_description: DoorbellSensorDescription

    def __init__(self, hub: DoorbellHub, description: DoorbellSensorDescription) -> None:
        super().__init__(hub, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> datetime | str | None:
        return self.entity_description.value_fn(self.hub.state)
