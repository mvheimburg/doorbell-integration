"""One lock entity per door shown on the panel."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
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
    async_add_entities(DoorLock(hub, door_id) for door_id in hub.config.doors)


class DoorLock(DoorbellEntity, LockEntity):
    def __init__(self, hub: DoorbellHub, door_id: str) -> None:
        super().__init__(hub, f"lock_{door_id}")
        self.door_id = door_id
        self._attr_name = door_id.replace("_", " ").capitalize()

    @property
    def _state(self) -> str | None:
        return self.hub.state.doors.get(self.door_id)

    @property
    def is_locked(self) -> bool | None:
        state = self._state
        if state is None or state == "unknown":
            return None
        return state == "locked"

    @property
    def is_locking(self) -> bool:
        return self._state == "locking"

    @property
    def is_unlocking(self) -> bool:
        return self._state == "unlocking"

    @property
    def is_jammed(self) -> bool:
        return self._state == "jammed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "door_id": self.door_id,
            "mapped_entity_id": self.hub.config.lock_map.get(self.door_id),
        }

    async def async_lock(self, **kwargs: Any) -> None:
        await self.hub.async_lock_door(self.door_id)

    async def async_unlock(self, **kwargs: Any) -> None:
        await self.hub.async_unlock_door(self.door_id)
