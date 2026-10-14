"""ModeSync: sets the panel's party mode and house state from on/off entities in Home Assistant.

Each option of a mode select (other than the first) can be linked to a source entity: an input
boolean, binary sensor, switch, schedule or calendar. The option applies while its source is
``on``. The rules:

* The panel is set by calling ``select.select_option`` on its MQTT select, which MQTT delivers to
  the panel as a command.
* If several sources are on, the one that turned on last wins; when it turns off, the panel falls
  back to the next most recent, or to the first option (``normal``, ``home``) if none is on.
* The panel is only set when the option this gives changes, at start-up, and when the panel comes
  online (it boots with the first option).
* A choice made on the panel itself is written back: the ``input_boolean`` or ``switch`` linked to
  it is turned on and the other linked ones are turned off. Sources that can't be switched (binary
  sensors, schedules, calendars) are left as they are. Either way the panel keeps its choice until
  one of the sources changes for some other reason.
* A source going ``unavailable`` or ``unknown`` keeps its last state, so a restart of whatever
  provides it does not flip the panel.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from homeassistant.components.select import ATTR_OPTION, SERVICE_SELECT_OPTION
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .const import MODE_AXES, PANEL_BOOT_GRACE_S

_LOGGER = logging.getLogger(__name__)

SELECT_DOMAIN = "select"
#: Source domains a choice made on the panel can be written back to.
WRITABLE_DOMAINS = ("input_boolean", "switch")


@callback
def panel_mode_entities(hass: HomeAssistant, device_id: str) -> dict[str, str]:
    """The panel device's mode selects, as ``axis -> entity_id``.

    An axis the panel has handed to KNX has no select, and is missing here.
    """
    registry = er.async_get(hass)
    selects = [
        entry
        for entry in er.async_entries_for_device(registry, device_id)
        if entry.domain == SELECT_DOMAIN
    ]
    found: dict[str, str] = {}
    for axis, (suffix, _options) in MODE_AXES.items():
        for entry in selects:
            if entry.unique_id.endswith(suffix):
                found[axis] = entry.entity_id
                break
    return found


@dataclass
class _Axis:
    name: str
    panel: str
    options: tuple[str, ...]
    #: option -> source entity_id, in the panel's option order
    sources: dict[str, str]
    #: the option the panel should show: what the sources call for, or what was chosen on it
    desired: str | None = None
    boot_until: float = 0.0

    @property
    def default(self) -> str:
        return self.options[0]


class ModeSync:
    """Source entities -> panel mode selects, for one panel; created per config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        panels: dict[str, str],
        links: dict[str, dict[str, str]],
    ) -> None:
        """``panels`` comes from :func:`panel_mode_entities`, ``links`` is the mode links option."""
        self.hass = hass
        self.name = name
        self._axes: list[_Axis] = []
        for axis, panel in panels.items():
            options = MODE_AXES[axis][1]
            sources = {
                option: source
                for option in options[1:]
                if (source := (links.get(axis) or {}).get(option))
            }
            if sources:
                self._axes.append(_Axis(axis, panel, options, sources))
        self._by_panel = {axis.panel: axis for axis in self._axes}
        #: source entity_id -> when it turned on, for the sources that are on
        self._on: dict[str, float] = {}
        #: source entity_id -> the state we are switching it to, while a write-back is under way
        self._writing: dict[str, str] = {}
        self._unsub: CALLBACK_TYPE | None = None

    @callback
    def async_start(self) -> None:
        if not self._axes:
            return
        sources = {source for axis in self._axes for source in axis.sources.values()}
        for source in sources:
            state = self.hass.states.get(source)
            if state is not None and state.state == STATE_ON:
                self._on[source] = state.last_changed.timestamp()
        self._unsub = async_track_state_change_event(
            self.hass, [*self._by_panel, *sources], self._async_state_changed
        )
        for axis in self._axes:
            axis.desired = self._resolve(axis)
            self._push(axis, force=True)

    @callback
    def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _async_state_changed(self, event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        old = old_state.state if old_state else None
        new = new_state.state if new_state else None
        if old == new:
            return  # attribute-only update
        entity_id = event.data["entity_id"]
        if axis := self._by_panel.get(entity_id):
            self._panel_changed(axis, old, new)
            return
        self._source_changed(entity_id, new, new_state.last_changed.timestamp() if new_state else 0)

    def _source_changed(self, source: str, new: str | None, changed_at: float) -> None:
        if new in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return  # keep its last state
        if new == STATE_ON:
            self._on.setdefault(source, changed_at)
        else:
            self._on.pop(source, None)
        if self._writing.get(source) == (STATE_ON if new == STATE_ON else STATE_OFF):
            del self._writing[source]
            return  # our own write-back: the panel already shows the choice
        for axis in self._axes:
            if source not in axis.sources.values():
                continue
            desired = self._resolve(axis)
            if desired != axis.desired:
                axis.desired = desired
                self._push(axis)

    def _panel_changed(self, axis: _Axis, old: str | None, new: str | None) -> None:
        if new is None or new == STATE_UNAVAILABLE:
            return
        if old is None or old == STATE_UNAVAILABLE:
            # The panel came online: it shows whatever it booted with, and may still report it.
            axis.boot_until = time.monotonic() + PANEL_BOOT_GRACE_S
            self._push(axis, force=True)
        elif time.monotonic() < axis.boot_until:
            self._push(axis)
        elif new != axis.desired and new in axis.options:
            # Not our push arriving: someone chose it on the panel.
            axis.desired = new
            self._write_back(axis, new)

    def _write_back(self, axis: _Axis, chosen: str) -> None:
        """Make the switchable sources agree with an option chosen on the panel."""
        _LOGGER.info("%s: %s set to %s on the panel", self.name, axis.panel, chosen)
        for option, source in axis.sources.items():
            domain = source.split(".", 1)[0]
            if domain not in WRITABLE_DOMAINS:
                continue
            target = STATE_ON if option == chosen else STATE_OFF
            state = self.hass.states.get(source)
            if state is None or state.state == target:
                continue
            self._writing[source] = target
            service = SERVICE_TURN_ON if target == STATE_ON else SERVICE_TURN_OFF
            self.hass.async_create_task(
                self.hass.services.async_call(
                    domain, service, {ATTR_ENTITY_ID: source}, blocking=False
                )
            )

    def _resolve(self, axis: _Axis) -> str:
        """The option of the source that turned on last, or the default if none is on.

        Sources that turned on together, e.g. at start-up, go by the panel's order: the later
        option wins, so a birthday shows over the season it falls in.
        """
        on = [
            (self._on[source], index, option)
            for index, (option, source) in enumerate(axis.sources.items())
            if source in self._on
        ]
        return max(on)[2] if on else axis.default

    def _push(self, axis: _Axis, *, force: bool = False) -> None:
        """Make the panel show the option the sources call for."""
        panel = self.hass.states.get(axis.panel)
        if axis.desired is None or panel is None or panel.state == STATE_UNAVAILABLE:
            return
        if panel.state == axis.desired and not force:
            return
        _LOGGER.info("%s: setting %s to %s", self.name, axis.panel, axis.desired)
        self.hass.async_create_task(
            self.hass.services.async_call(
                SELECT_DOMAIN,
                SERVICE_SELECT_OPTION,
                {ATTR_ENTITY_ID: axis.panel, ATTR_OPTION: axis.desired},
                blocking=False,
            )
        )
