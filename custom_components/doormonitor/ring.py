"""Ring notifications: a push to chosen people's phones when the doorbell rings.

Each chosen person gets the notification through their Home Assistant Companion app. A person can
be marked "only when home": they are then skipped unless their ``person`` entity is ``home``.

The ring comes from the panel's ``bell_pressed`` binary sensor, which pulses ``on`` for each press.
Only an ``off`` -> ``on`` change counts, so a restart or a reconnect does not resend an old ring.
A panel whose bell is on KNX has no such sensor; any binary sensor or event entity can be chosen
as the ring signal instead.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_HOME, STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import BELL_PRESSED_SUFFIX, DOMAIN, RING_DEDUPE_S, RING_ONLY_HOME, RING_PERSON

_LOGGER = logging.getLogger(__name__)

_MESSAGES = {
    "en": "Someone is at the door",
    "nb": "Det ringer på døra",
}


def message_language(language: str | None) -> str:
    """nb, nb-NO, no and nn (no Nynorsk of its own) get Bokmål; others English."""
    base = (language or "").strip().lower().replace("_", "-").split("-", 1)[0]
    return "nb" if base in ("nb", "no", "nn") else "en"


@callback
def panel_bell_entity(hass: HomeAssistant, device_id: str) -> str | None:
    """The panel's ``bell_pressed`` binary sensor; missing when the bell is on KNX."""
    for entry in er.async_entries_for_device(er.async_get(hass), device_id):
        if entry.domain == "binary_sensor" and entry.unique_id.endswith(BELL_PRESSED_SUFFIX):
            return entry.entity_id
    return None


@callback
def notify_services(hass: HomeAssistant, person_id: str) -> list[str]:
    """The Companion-app notify services of a person's phones."""
    state = hass.states.get(person_id)
    if state is None:
        return []
    entities, devices = er.async_get(hass), dr.async_get(hass)
    services: list[str] = []
    for tracker in state.attributes.get("device_trackers", []):
        entry = entities.async_get(tracker)
        if entry is None or entry.platform != "mobile_app" or entry.device_id is None:
            continue
        device = devices.async_get(entry.device_id)
        # mobile_app names its service after the registered device name.
        if device is None or not device.name:
            continue
        service = f"mobile_app_{slugify(device.name)}"
        if hass.services.has_service("notify", service) and service not in services:
            services.append(service)
    return services


def is_ring(entity_id: str, old: Any, new: Any) -> bool:
    """Whether a state change of the ring signal is a new ring."""
    if old is None or new is None:
        return False
    if entity_id.startswith("event."):
        # An event entity's state is the time it last fired.
        return (
            old.state != STATE_UNAVAILABLE
            and new.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
            and new.state != old.state
        )
    return old.state == STATE_OFF and new.state == STATE_ON


class RingNotifier:
    """Watches the ring signal and notifies the chosen people."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        source: str,
        people: list[dict[str, Any]],
        title: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.source = source
        self.people = people
        self.title = title
        self._last: datetime | None = None

    @callback
    def async_start(self) -> None:
        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, [self.source], self._on_change)
        )

    @callback
    def _on_change(self, event: Event[EventStateChangedData]) -> None:
        if not is_ring(self.source, event.data["old_state"], event.data["new_state"]):
            return
        now = dt_util.utcnow()
        if self._last and now - self._last < timedelta(seconds=RING_DEDUPE_S):
            return  # one visitor pressing twice
        self._last = now
        self.async_notify()

    @callback
    def recipients(self) -> list[str]:
        """The notify services to reach now: everyone chosen, less those away who asked for it."""
        services: list[str] = []
        for person in self.people:
            person_id = person[RING_PERSON]
            if person.get(RING_ONLY_HOME):
                state = self.hass.states.get(person_id)
                if state is None or state.state != STATE_HOME:
                    continue
            found = notify_services(self.hass, person_id)
            if not found:
                _LOGGER.warning(
                    "%s: %s has no Companion app to notify about the ring", self.title, person_id
                )
            services += [s for s in found if s not in services]
        return services

    @callback
    def async_notify(self) -> None:
        data = {
            "title": self.title,
            "message": _MESSAGES[message_language(self.hass.config.language)],
            "data": {
                # A newer ring replaces the older notification.
                "tag": f"{DOMAIN}_{self.entry.entry_id}_ring",
                "group": DOMAIN,
                "push": {"interruption-level": "time-sensitive"},
                "ttl": 0,
                "priority": "high",
            },
        }
        for service in self.recipients():
            self.entry.async_create_background_task(
                self.hass, self._async_call(service, data), f"{DOMAIN}_ring_{service}"
            )

    async def _async_call(self, service: str, data: dict[str, Any]) -> None:
        try:
            await self.hass.services.async_call("notify", service, data, blocking=True)
        except Exception:  # noqa: BLE001 - one broken phone must not stop the rest
            _LOGGER.exception("Could not notify %s", service)
