"""PanelSync: keeps a panel's lock/cover entities in step with the real entities they stand for.

The panel entities are the ones the MQTT integration discovered for the DoorMonitor panel. The
panel has no hardware; its state is only what it shows. The rules:

* A real entity settling on a new state is pushed to the panel by calling the lock/cover service
  on the panel entity, which MQTT delivers to the panel as a command.
* The panel settling on a state the real entity does not have is a request (someone pressed on
  the panel, or operated the panel entity in Home Assistant) and drives the real entity.
* Echoes of our own pushes, the first state after the panel comes online, and anything it shows
  during ``PANEL_BOOT_GRACE_S`` are not requests; the real state is pushed instead.
* If the real entity has not followed a request after ``REQUEST_TIMEOUT_S``, the panel is put
  back to the real state.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from functools import partial

from homeassistant.components.cover import CoverState
from homeassistant.components.lock import LockState
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import ECHO_WINDOW_S, LINKABLE_DOMAINS, PANEL_BOOT_GRACE_S, REQUEST_TIMEOUT_S

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _Kind:
    domain: str
    #: settled entity state -> sync value
    settled: dict[str, str]
    #: moving entity state -> the sync value it is heading for
    heading: dict[str, str]
    #: sync value -> service that gets an entity there
    services: dict[str, str]


_KINDS: dict[str, _Kind] = {
    "lock": _Kind(
        domain="lock",
        settled={
            LockState.LOCKED: "locked",
            LockState.UNLOCKED: "unlocked",
            LockState.OPEN: "unlocked",
        },
        heading={
            LockState.LOCKING: "locked",
            LockState.UNLOCKING: "unlocked",
            LockState.OPENING: "unlocked",
        },
        services={"locked": "lock", "unlocked": "unlock"},
    ),
    "cover": _Kind(
        domain="cover",
        settled={CoverState.OPEN: "open", CoverState.CLOSED: "closed"},
        heading={CoverState.OPENING: "open", CoverState.CLOSING: "closed"},
        services={"open": "open_cover", "closed": "close_cover"},
    ),
}


@callback
def panel_entity_ids(hass: HomeAssistant, device_id: str) -> list[str]:
    """The panel device's lock and cover entities, i.e. what can be linked."""
    registry = er.async_get(hass)
    return sorted(
        entry.entity_id
        for entry in er.async_entries_for_device(registry, device_id)
        if entry.domain in LINKABLE_DOMAINS
    )


@dataclass
class _Link:
    panel: str
    real: str
    kind: _Kind
    #: sync value -> monotonic time we pushed it to the panel
    pushed: dict[str, float] = field(default_factory=dict)
    boot_until: float = 0.0
    cancel_timeout: CALLBACK_TYPE | None = None


class PanelSync:
    """Two-way sync for one panel; created per config entry."""

    def __init__(self, hass: HomeAssistant, name: str, links: dict[str, str]) -> None:
        self.hass = hass
        self.name = name
        self._links = [
            _Link(panel, real, _KINDS[panel.split(".", 1)[0]]) for panel, real in links.items()
        ]
        self._by_panel = {link.panel: link for link in self._links}
        self._by_real: dict[str, list[_Link]] = {}
        for link in self._links:
            self._by_real.setdefault(link.real, []).append(link)
        self._unsub: CALLBACK_TYPE | None = None

    @callback
    def async_start(self) -> None:
        if not self._links:
            return
        self._unsub = async_track_state_change_event(
            self.hass, [*self._by_panel, *self._by_real], self._async_state_changed
        )
        # What HA last saw from the panel may not be what it shows now.
        for link in self._links:
            self._push_real_state(link, force=True)

    @callback
    def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        for link in self._links:
            if link.cancel_timeout:
                link.cancel_timeout()
                link.cancel_timeout = None

    @callback
    def _async_state_changed(self, event: Event[EventStateChangedData]) -> None:
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        old = old_state.state if old_state else None
        new = new_state.state if new_state else None
        if old == new:
            return  # attribute-only update
        entity_id = event.data["entity_id"]
        if link := self._by_panel.get(entity_id):
            self._panel_changed(link, old, new)
        for link in self._by_real.get(entity_id, ()):
            self._push_real_state(link)

    def _panel_changed(self, link: _Link, old: str | None, new: str | None) -> None:
        if new is None or new == STATE_UNAVAILABLE:
            return
        now = time.monotonic()
        if old is None or old == STATE_UNAVAILABLE:
            # The panel came online: it shows whatever it booted with.
            link.boot_until = now + PANEL_BOOT_GRACE_S
            self._push_real_state(link, force=True)
            return

        value = link.kind.settled.get(new)
        if value is None:
            return  # unknown, moving or jammed
        pushed_at = link.pushed.pop(value, None)
        if pushed_at is not None and now - pushed_at < ECHO_WINDOW_S:
            # Our own push arriving; the real entity may have moved on since.
            self._push_real_state(link)
            return
        if old == STATE_UNKNOWN or now < link.boot_until:
            self._push_real_state(link)
            return
        self._request(link, value)

    def _request(self, link: _Link, value: str) -> None:
        link.pushed.clear()
        real = self.hass.states.get(link.real)
        if real is None or real.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            # The panel is corrected once the real entity reports a state.
            _LOGGER.warning(
                "%s: %s requested %s, but %s has no state", self.name, link.panel, value, link.real
            )
            return
        if value in (link.kind.settled.get(real.state), link.kind.heading.get(real.state)):
            return
        service = link.kind.services[value]
        _LOGGER.info("%s: %s requested %s, calling %s", self.name, link.panel, value, link.real)
        self._call(link.kind.domain, service, link.real)

        if link.cancel_timeout:
            link.cancel_timeout()
        link.cancel_timeout = async_call_later(
            self.hass, REQUEST_TIMEOUT_S, partial(self._async_request_timeout, link)
        )

    @callback
    def _async_request_timeout(self, link: _Link, _now: object) -> None:
        link.cancel_timeout = None
        self._push_real_state(link)

    def _push_real_state(self, link: _Link, *, force: bool = False) -> None:
        """Make the panel show the real entity's settled state."""
        real = self.hass.states.get(link.real)
        panel = self.hass.states.get(link.panel)
        if real is None or panel is None or panel.state == STATE_UNAVAILABLE:
            return
        value = link.kind.settled.get(real.state)
        if value is None:
            return  # no state yet, or moving: wait until it settles
        if link.kind.settled.get(panel.state) == value:
            if not force:
                return
        else:
            link.pushed[value] = time.monotonic()
        _LOGGER.debug("%s: showing %s as %s on %s", self.name, link.real, value, link.panel)
        self._call(link.kind.domain, link.kind.services[value], link.panel)

    def _call(self, domain: str, service: str, entity_id: str) -> None:
        self.hass.async_create_task(
            self.hass.services.async_call(
                domain, service, {ATTR_ENTITY_ID: entity_id}, blocking=False
            )
        )
