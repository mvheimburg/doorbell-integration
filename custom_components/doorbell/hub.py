"""DoorbellHub: the in-memory representation of one physical DoorMonitor panel.

It owns the single MQTT subscription, keeps the last known panel state, fires
Home Assistant bus events, publishes commands back to the panel and keeps
optional real lock/cover entities in sync with what the panel shows.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.cover import CoverState
from homeassistant.components.lock import LockState
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import EventStateChangedData, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    ACTIVE_PAGES,
    CONF_BASE_TOPIC,
    CONF_DISCOVERY_PREFIX,
    CONF_DOORS,
    CONF_GATE_ENTITY,
    CONF_GATE_ID,
    CONF_LOCK_MAP,
    CONF_NAME,
    DEFAULT_BASE_TOPIC,
    DEFAULT_DISCOVERY_PREFIX,
    DEFAULT_DOORS,
    DEFAULT_GATE_ID,
    DEFAULT_NAME,
    DOMAIN,
    EVENT_GATE_REQUEST,
    EVENT_LOCK_REQUEST,
    EVENT_LOGIN,
    EVENT_LOGOUT,
    EVENT_RING,
    HOUSE_STATES,
    LOGIN_METHODS,
    MANUFACTURER,
    MODEL,
    OWN_COMMAND_WINDOW_S,
    PARTY_MODES,
    PAYLOAD_CLOSE,
    PAYLOAD_LOCK,
    PAYLOAD_OFFLINE,
    PAYLOAD_ON,
    PAYLOAD_ONLINE,
    PAYLOAD_OPEN,
    PAYLOAD_RING,
    PAYLOAD_STOP,
    PAYLOAD_UNLOCK,
)
from .topics import Topics, discovery_config_topics

_LOGGER = logging.getLogger(__name__)

RingListener = Callable[[dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class DoorbellConfig:
    name: str
    base_topic: str
    discovery_prefix: str
    doors: list[str]
    gate_id: str
    lock_map: dict[str, str]
    gate_entity: str | None

    @classmethod
    def from_entry(cls, entry: ConfigEntry) -> DoorbellConfig:
        raw: dict[str, Any] = {**entry.data, **entry.options}
        doors = [d for d in (raw.get(CONF_DOORS) or DEFAULT_DOORS) if d]
        lock_map_raw = raw.get(CONF_LOCK_MAP) or {}
        lock_map = {
            door: entity
            for door, entity in lock_map_raw.items()
            if isinstance(door, str) and isinstance(entity, str) and entity and door in doors
        }
        return cls(
            name=raw.get(CONF_NAME) or DEFAULT_NAME,
            base_topic=(raw.get(CONF_BASE_TOPIC) or DEFAULT_BASE_TOPIC).strip("/"),
            discovery_prefix=(raw.get(CONF_DISCOVERY_PREFIX) or DEFAULT_DISCOVERY_PREFIX).strip(
                "/"
            ),
            doors=doors,
            gate_id=raw.get(CONF_GATE_ID) or DEFAULT_GATE_ID,
            lock_map=lock_map,
            gate_entity=raw.get(CONF_GATE_ENTITY) or None,
        )


@dataclass
class DoorbellState:
    """Last known state of the panel. ``None`` means "not received yet"."""

    available: bool | None = None
    last_ring: datetime | None = None
    bell_pressed: bool = False
    logged_in_user: str = ""
    login_method: str = "none"
    active_page: str = "home"
    party_mode: str | None = None
    house_state: str | None = None
    doors: dict[str, str] = field(default_factory=dict)
    gate: str | None = None


class DoorbellHub:
    """Central object for one panel; created per config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.config = DoorbellConfig.from_entry(entry)
        self.topics = Topics(self.config.base_topic)
        self.state = DoorbellState()
        self.device_id: str | None = None

        self._state_listeners: set[CALLBACK_TYPE] = set()
        self._ring_listeners: set[RingListener] = set()
        self._unsubscribers: list[CALLBACK_TYPE] = []
        # topic -> (payload, monotonic time) of commands we published ourselves
        self._own_commands: dict[str, tuple[str, float]] = {}

    # -- lifecycle -----------------------------------------------------------

    async def async_setup(self) -> None:
        registry = dr.async_get(self.hass)
        device = registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.config.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
        self.device_id = device.id

        _LOGGER.debug("Subscribing to %s", self.topics.wildcard)
        self._unsubscribers.append(
            await mqtt.async_subscribe(self.hass, self.topics.wildcard, self._async_mqtt_message, 1)
        )

        tracked = list(self.config.lock_map.values())
        if self.config.gate_entity:
            tracked.append(self.config.gate_entity)
        if tracked:
            self._unsubscribers.append(
                async_track_state_change_event(self.hass, tracked, self._async_real_entity_changed)
            )

    async def async_unload(self) -> None:
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()

    @property
    def device_info(self) -> dr.DeviceInfo:
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.config.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    # -- listeners -----------------------------------------------------------

    @callback
    def async_add_listener(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        self._state_listeners.add(listener)
        return lambda: self._state_listeners.discard(listener)

    @callback
    def async_add_ring_listener(self, listener: RingListener) -> CALLBACK_TYPE:
        self._ring_listeners.add(listener)
        return lambda: self._ring_listeners.discard(listener)

    @callback
    def _notify(self) -> None:
        for listener in list(self._state_listeners):
            listener()

    def _event_data(self, **extra: Any) -> dict[str, Any]:
        return {
            "entry_id": self.entry.entry_id,
            "device_id": self.device_id,
            "name": self.config.name,
            **extra,
        }

    # -- inbound MQTT --------------------------------------------------------

    @callback
    def _async_mqtt_message(self, msg: mqtt.ReceiveMessage) -> None:
        topic = msg.topic
        payload = msg.payload if isinstance(msg.payload, str) else str(msg.payload)
        parts = self.topics.relative(topic)
        if parts is None:
            return
        _LOGGER.debug("MQTT %s = %r", topic, payload)

        match parts:
            case ["availability"]:
                self._handle_availability(payload)
            case ["device_trigger", "bell"]:
                if payload == PAYLOAD_RING:
                    self._handle_ring(topic)
            case ["binary_sensor", "bell_pressed", "state"]:
                self.state.bell_pressed = payload == PAYLOAD_ON
                self._notify()
            case ["sensor", "last_ring", "state"]:
                self.state.last_ring = _parse_timestamp(payload)
                self._notify()
            case ["sensor", "logged_in_user", "state"]:
                self.state.logged_in_user = payload.strip()
                self._notify()
            case ["sensor", "login_method", "state"]:
                value = payload.strip().lower()
                self.state.login_method = value if value in LOGIN_METHODS else "none"
                self._notify()
            case ["sensor", "active_page", "state"]:
                self._handle_active_page(payload.strip().lower())
            case ["select", "partymode", "state"]:
                value = payload.strip().lower()
                self.state.party_mode = value if value in PARTY_MODES else None
                self._notify()
            case ["select", "house_state", "state"]:
                value = payload.strip().lower()
                self.state.house_state = value if value in HOUSE_STATES else None
                self._notify()
            case ["lock", door_id, "state"]:
                self._handle_lock_state(door_id, payload.strip().lower())
            case ["lock", door_id, "command"]:
                self._handle_lock_command(door_id, payload.strip().upper(), topic)
            case ["cover", gate_id, "state"] if gate_id == self.config.gate_id:
                self._handle_cover_state(payload.strip().lower())
            case ["cover", gate_id, "command"] if gate_id == self.config.gate_id:
                self._handle_cover_command(payload.strip().upper(), topic)
            case _:
                pass

    def _handle_availability(self, payload: str) -> None:
        value = payload.strip().lower()
        if value == PAYLOAD_ONLINE:
            self.state.available = True
        elif value == PAYLOAD_OFFLINE:
            self.state.available = False
        else:
            return
        _LOGGER.info("%s is %s", self.config.name, value)
        self._notify()

    def _handle_ring(self, topic: str) -> None:
        now = dt_util.utcnow()
        self.state.last_ring = now
        data = self._event_data(topic=topic, timestamp=now.isoformat())
        _LOGGER.info("%s: ring", self.config.name)
        self.hass.bus.async_fire(EVENT_RING, data)
        for listener in list(self._ring_listeners):
            listener(data)
        self._notify()

    def _handle_active_page(self, page: str) -> None:
        if page not in ACTIVE_PAGES:
            page = "home"
        previous = self.state.active_page
        self.state.active_page = page
        if previous == "home" and page != "home":
            self.hass.bus.async_fire(
                EVENT_LOGIN,
                self._event_data(
                    user=self.state.logged_in_user,
                    method=self.state.login_method,
                    page=page,
                ),
            )
        elif previous != "home" and page == "home":
            self.hass.bus.async_fire(EVENT_LOGOUT, self._event_data(page=page))
        self._notify()

    def _handle_lock_state(self, door_id: str, state: str) -> None:
        self.state.doors[door_id] = state
        self._notify()
        # The panel's belief may lag a real lock: push the real state to the panel.
        real = self.config.lock_map.get(door_id)
        if real:
            self._sync_lock_to_panel(door_id, self.hass.states.get(real))

    def _handle_lock_command(self, door_id: str, command: str, topic: str) -> None:
        if command not in (PAYLOAD_LOCK, PAYLOAD_UNLOCK):
            return
        if self._is_own_command(topic, command):
            return
        action = "lock" if command == PAYLOAD_LOCK else "unlock"
        real = self.config.lock_map.get(door_id)
        _LOGGER.info("%s: panel requests %s of door %s", self.config.name, action, door_id)
        self.hass.bus.async_fire(
            EVENT_LOCK_REQUEST, self._event_data(door=door_id, action=action, entity_id=real)
        )
        if real:
            self.hass.async_create_task(self._async_call_lock(real, action))

    def _handle_cover_state(self, state: str) -> None:
        self.state.gate = state
        self._notify()
        if self.config.gate_entity:
            self._sync_cover_to_panel(self.hass.states.get(self.config.gate_entity))

    def _handle_cover_command(self, command: str, topic: str) -> None:
        actions = {PAYLOAD_OPEN: "open", PAYLOAD_CLOSE: "close", PAYLOAD_STOP: "stop"}
        if command not in actions:
            return
        if self._is_own_command(topic, command):
            return
        action = actions[command]
        real = self.config.gate_entity
        _LOGGER.info("%s: panel requests gate %s", self.config.name, action)
        self.hass.bus.async_fire(
            EVENT_GATE_REQUEST,
            self._event_data(gate=self.config.gate_id, action=action, entity_id=real),
        )
        if real:
            self.hass.async_create_task(self._async_call_cover(real, action))

    # -- outbound MQTT -------------------------------------------------------

    async def _async_publish(self, topic: str, payload: str, *, retain: bool = False) -> None:
        self._own_commands[topic] = (payload, time.monotonic())
        _LOGGER.debug("Publish %s = %r", topic, payload)
        await mqtt.async_publish(self.hass, topic, payload, 1, retain)

    def _is_own_command(self, topic: str, payload: str) -> bool:
        recorded = self._own_commands.get(topic)
        if recorded is None:
            return False
        own_payload, when = recorded
        if own_payload == payload and (time.monotonic() - when) < OWN_COMMAND_WINDOW_S:
            self._own_commands.pop(topic, None)
            return True
        return False

    async def async_set_party_mode(self, mode: str) -> None:
        if mode not in PARTY_MODES:
            raise ValueError(f"invalid party mode {mode!r}; expected one of {PARTY_MODES}")
        await self._async_publish(self.topics.party_mode_command, mode)

    async def async_set_house_state(self, state: str) -> None:
        if state not in HOUSE_STATES:
            raise ValueError(f"invalid house state {state!r}; expected one of {HOUSE_STATES}")
        await self._async_publish(self.topics.house_state_command, state)

    async def async_lock_door(self, door_id: str) -> None:
        await self._async_publish(self.topics.lock_command(door_id), PAYLOAD_LOCK)
        if real := self.config.lock_map.get(door_id):
            await self._async_call_lock(real, "lock")

    async def async_unlock_door(self, door_id: str) -> None:
        await self._async_publish(self.topics.lock_command(door_id), PAYLOAD_UNLOCK)
        if real := self.config.lock_map.get(door_id):
            await self._async_call_lock(real, "unlock")

    async def async_open_gate(self) -> None:
        await self._async_publish(self.topics.cover_command(self.config.gate_id), PAYLOAD_OPEN)
        if self.config.gate_entity:
            await self._async_call_cover(self.config.gate_entity, "open")

    async def async_close_gate(self) -> None:
        await self._async_publish(self.topics.cover_command(self.config.gate_id), PAYLOAD_CLOSE)
        if self.config.gate_entity:
            await self._async_call_cover(self.config.gate_entity, "close")

    async def async_stop_gate(self) -> None:
        await self._async_publish(self.topics.cover_command(self.config.gate_id), PAYLOAD_STOP)
        if self.config.gate_entity:
            await self._async_call_cover(self.config.gate_entity, "stop")

    async def async_purge_mqtt_discovery(self) -> list[str]:
        """Clear the retained discovery configs the panel itself publishes.

        The panel advertises its entities through MQTT discovery, which would
        duplicate the entities provided by this integration. Publishing an empty
        retained payload removes them. Turn discovery off on the panel as well,
        or they come back on its next reconnect.
        """
        topics = discovery_config_topics(
            self.config.discovery_prefix,
            self.config.base_topic,
            self.config.doors,
            self.config.gate_id,
        )
        for topic in topics:
            await mqtt.async_publish(self.hass, topic, "", 1, True)
        _LOGGER.info("Purged %d retained MQTT discovery configs", len(topics))
        return topics

    # -- real entity sync ----------------------------------------------------

    async def _async_call_lock(self, entity_id: str, action: str) -> None:
        current = self.hass.states.get(entity_id)
        target = LockState.LOCKED if action == "lock" else LockState.UNLOCKED
        if current is not None and current.state == target:
            return
        await self.hass.services.async_call(
            "lock", action, {ATTR_ENTITY_ID: entity_id}, blocking=False
        )

    async def _async_call_cover(self, entity_id: str, action: str) -> None:
        await self.hass.services.async_call(
            "cover", f"{action}_cover", {ATTR_ENTITY_ID: entity_id}, blocking=False
        )

    @callback
    def _async_real_entity_changed(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        new_state = event.data["new_state"]
        if entity_id == self.config.gate_entity:
            self._sync_cover_to_panel(new_state)
            return
        for door_id, real in self.config.lock_map.items():
            if real == entity_id:
                self._sync_lock_to_panel(door_id, new_state)

    def _sync_lock_to_panel(self, door_id: str, real_state: Any) -> None:
        if real_state is None or real_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        if real_state.state == LockState.LOCKED:
            target, command = LockState.LOCKED, PAYLOAD_LOCK
        elif real_state.state in (LockState.UNLOCKED, LockState.OPEN):
            target, command = LockState.UNLOCKED, PAYLOAD_UNLOCK
        else:
            return  # locking / unlocking / jammed: wait for a settled state
        if self.state.doors.get(door_id) == target:
            return
        _LOGGER.debug("Sync door %s to panel: %s", door_id, command)
        self.hass.async_create_task(self._async_publish(self.topics.lock_command(door_id), command))

    def _sync_cover_to_panel(self, real_state: Any) -> None:
        if real_state is None or real_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        if real_state.state == CoverState.OPEN:
            target, command = CoverState.OPEN, PAYLOAD_OPEN
        elif real_state.state == CoverState.CLOSED:
            target, command = CoverState.CLOSED, PAYLOAD_CLOSE
        else:
            return  # opening / closing: wait for a settled state
        if self.state.gate == target:
            return
        _LOGGER.debug("Sync gate to panel: %s", command)
        self.hass.async_create_task(
            self._async_publish(self.topics.cover_command(self.config.gate_id), command)
        )


def _parse_timestamp(payload: str) -> datetime | None:
    parsed = dt_util.parse_datetime(payload.strip())
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.UTC)
    return parsed
