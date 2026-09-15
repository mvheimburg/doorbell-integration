"""Two-way sync between the panel's discovered MQTT entities and the real entities."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Event, HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_mqtt_message,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doorbell.const import REQUEST_TIMEOUT_S

from .conftest import REAL_FRONT, REAL_GATE

FRONT_CMD = "doorbell/lock/front/command"
GATE_CMD = "doorbell/cover/gate/command"


def _published(mqtt_mock: MqttMockHAClient, topic: str) -> list[str]:
    return [c.args[1] for c in mqtt_mock.async_publish.call_args_list if c.args[0] == topic]


def _real_calls(events: list[Event], *real: str) -> list[tuple[str, str]]:
    """Service calls made on real (non-panel) entities, as (service, entity_id)."""
    return [
        (e.data["service"], e.data["service_data"]["entity_id"])
        for e in events
        if e.data["service_data"].get("entity_id") in (real or (REAL_FRONT, REAL_GATE))
    ]


@pytest.fixture
async def calls(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> list[Event]:
    """Service calls from here on; start-up pushes are forgotten."""
    mqtt_mock.async_publish.reset_mock()
    return async_capture_events(hass, EVENT_CALL_SERVICE)


async def _panel(hass: HomeAssistant, topic: str, payload: str) -> None:
    async_fire_mqtt_message(hass, topic, payload)
    await hass.async_block_till_done()


async def _real(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()


@pytest.mark.parametrize("real_states", [{REAL_FRONT: "unlocked", REAL_GATE: "closed"}])
async def test_setup_shows_real_state_on_panel(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK"]
    # Panel already claims closed, but that may be stale: it is told anyway.
    assert _published(mqtt_mock, GATE_CMD) == ["CLOSE"]
    assert _published(mqtt_mock, "doorbell/lock/workshop/command") == []  # not linked


async def test_panel_press_drives_real_lock(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    assert _real_calls(calls) == [("unlock", REAL_FRONT)]
    assert _published(mqtt_mock, FRONT_CMD) == []


async def test_panel_press_already_under_way_is_not_repeated(
    hass: HomeAssistant, calls: list[Event]
) -> None:
    await _real(hass, REAL_FRONT, "unlocking")
    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    assert _real_calls(calls) == []


async def test_real_change_is_shown_on_panel_and_echo_ignored(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _real(hass, REAL_FRONT, "unlocking")
    assert _published(mqtt_mock, FRONT_CMD) == []  # moving: wait

    await _real(hass, REAL_FRONT, "unlocked")
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK"]

    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    assert _real_calls(calls) == []
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK"]


async def test_quick_relock_does_not_bounce(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _real(hass, REAL_FRONT, "unlocked")
    await _real(hass, REAL_FRONT, "locked")  # auto-relock before the panel answered
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK"]

    # The late echo is not a request to unlock; the panel is corrected instead.
    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK", "LOCK"]
    await _panel(hass, "doorbell/lock/front/state", "locked")
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK", "LOCK"]
    assert _real_calls(calls) == []


async def test_panel_coming_online_gets_real_state(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/availability", "offline")
    await _real(hass, REAL_FRONT, "unlocked")
    assert _published(mqtt_mock, FRONT_CMD) == []  # nobody to tell

    await _panel(hass, "doorbell/availability", "online")
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK"]
    await _panel(hass, "doorbell/lock/front/state", "unlocked")

    # The panel re-publishing its boot default right after is not a press.
    await _panel(hass, "doorbell/lock/front/state", "locked")
    assert _published(mqtt_mock, FRONT_CMD) == ["UNLOCK", "UNLOCK"]
    assert _real_calls(calls) == []


async def test_real_entity_not_following_request_is_shown_on_panel(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    assert _real_calls(calls) == [("unlock", REAL_FRONT)]

    # The real lock never moves.
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=REQUEST_TIMEOUT_S + 1))
    await hass.async_block_till_done()
    assert _published(mqtt_mock, FRONT_CMD) == ["LOCK"]


async def test_real_entity_following_request_leaves_panel_alone(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    await _real(hass, REAL_FRONT, "unlocking")
    await _real(hass, REAL_FRONT, "unlocked")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=REQUEST_TIMEOUT_S + 1))
    await hass.async_block_till_done()
    assert _published(mqtt_mock, FRONT_CMD) == []


async def test_gate_sync_both_directions(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/cover/gate/state", "open")
    assert _real_calls(calls) == [("open_cover", REAL_GATE)]

    await _real(hass, REAL_GATE, "opening")
    await _real(hass, REAL_GATE, "open")
    assert _published(mqtt_mock, GATE_CMD) == []  # panel already shows open

    await _real(hass, REAL_GATE, "closing")
    assert _published(mqtt_mock, GATE_CMD) == []
    await _real(hass, REAL_GATE, "closed")
    assert _published(mqtt_mock, GATE_CMD) == ["CLOSE"]


async def test_unlinked_door_and_unavailable_real_lock(
    hass: HomeAssistant, calls: list[Event], mqtt_mock: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/lock/workshop/state", "unlocked")
    assert calls == []

    await _real(hass, REAL_FRONT, "unavailable")
    await _panel(hass, "doorbell/lock/front/state", "unlocked")
    assert _real_calls(calls) == []

    # Once the real lock is back, the panel shows its state.
    await _real(hass, REAL_FRONT, "locked")
    assert _published(mqtt_mock, FRONT_CMD) == ["LOCK"]


async def test_unload_stops_sync(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    calls: list[Event],
    mqtt_mock: MqttMockHAClient,
) -> None:
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    await _real(hass, REAL_FRONT, "unlocked")
    await _panel(hass, "doorbell/cover/gate/state", "open")
    assert _published(mqtt_mock, FRONT_CMD) == []
    assert _real_calls(calls) == []
