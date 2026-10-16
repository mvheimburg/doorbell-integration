"""Follow a House State hub's resolved modes without writing back to it."""

from __future__ import annotations

import logging

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import MODE_AXES

_LOGGER = logging.getLogger(__name__)


class HouseStateSync:
    """Map one hub's effective overlay and occupancy to selected panel axes."""

    def __init__(
        self, hass: HomeAssistant, source: str, panels: dict[str, str], mapping: dict[str, str]
    ) -> None:
        self.hass = hass
        self.source = source
        self.panels = panels
        self.mapping = mapping
        self.desired: dict[str, str] = {}
        self._unsub: CALLBACK_TYPE | None = None

    @callback
    def async_start(self) -> None:
        self._unsub = async_track_state_change_event(
            self.hass, [self.source, *self.panels.values()], self._changed
        )
        self._refresh()

    @callback
    def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _changed(self, event: Event[EventStateChangedData]) -> None:
        if event.data["entity_id"] == self.source:
            self._refresh()
        else:
            self._push()

    def _refresh(self) -> None:
        state = self.hass.states.get(self.source)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.warning(
                "House State source %s is unavailable; keeping panel modes", self.source
            )
            return
        attributes = state.attributes
        overlay = attributes.get("overlay")
        if isinstance(overlay, str):
            mode = self.mapping.get(overlay, overlay)
            self.desired["party_mode"] = mode if mode in MODE_AXES["party_mode"][1] else "normal"
        occupied = attributes.get("occupied")
        if isinstance(occupied, bool):
            vacation = (attributes.get("config") or {}).get("roles", {}).get("vacation")
            path = attributes.get("active_path") or []
            self.desired["house_state"] = (
                "home" if occupied else "vacation" if vacation and vacation in path else "away"
            )
        self._push()

    def _push(self) -> None:
        for axis, entity_id in self.panels.items():
            desired = self.desired.get(axis)
            panel = self.hass.states.get(entity_id)
            if (
                desired is None
                or panel is None
                or panel.state
                in (
                    STATE_UNKNOWN,
                    STATE_UNAVAILABLE,
                    desired,
                )
            ):
                continue
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "select",
                    "select_option",
                    {"entity_id": entity_id, "option": desired},
                    blocking=True,
                )
            )
