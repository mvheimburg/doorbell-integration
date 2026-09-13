"""Two-way sync between panel doors/gate and mapped real entities."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
    async_mock_service,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient


@pytest.fixture
def entry_options(mapped_options: dict[str, Any]) -> dict[str, Any]:
    return mapped_options


@pytest.fixture(autouse=True)
def real_entities(hass: HomeAssistant) -> None:
    hass.states.async_set("lock.real_front", "locked")
    hass.states.async_set("cover.real_gate", "closed")


def _published(mqtt_mock: MqttMockHAClient, topic: str) -> list[str]:
    return [c.args[1] for c in mqtt_mock.async_publish.call_args_list if c.args[0] == topic]


async def test_panel_unlock_request_drives_real_lock(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    unlock_calls = async_mock_service(hass, "lock", "unlock")
    lock_calls = async_mock_service(hass, "lock", "lock")

    async_fire_mqtt_message(hass, "doorbell/lock/front/command", "UNLOCK")
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in unlock_calls] == ["lock.real_front"]

    # Real lock is already locked: a LOCK request needs no service call.
    async_fire_mqtt_message(hass, "doorbell/lock/front/command", "LOCK")
    await hass.async_block_till_done()
    assert lock_calls == []


async def test_unmapped_door_request_does_not_call_services(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    unlock_calls = async_mock_service(hass, "lock", "unlock")
    async_fire_mqtt_message(hass, "doorbell/lock/workshop/command", "UNLOCK")
    await hass.async_block_till_done()
    assert unlock_calls == []


async def test_ha_unlock_drives_real_lock_and_panel(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    # Mocking lock.unlock also swallows calls to lock.doorbell_front, so go
    # through the hub (the entity delegates to it 1:1, see test_entities).
    unlock_calls = async_mock_service(hass, "lock", "unlock")
    await setup_entry.runtime_data.async_unlock_door("front")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/lock/front/command") == ["UNLOCK"]
    assert [c.data["entity_id"] for c in unlock_calls] == ["lock.real_front"]


async def test_real_lock_change_is_pushed_to_panel(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    async_fire_mqtt_message(hass, "doorbell/lock/front/state", "locked")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/lock/front/command") == []

    hass.states.async_set("lock.real_front", "unlocking")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/lock/front/command") == []  # transitional: wait

    hass.states.async_set("lock.real_front", "unlocked")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/lock/front/command") == ["UNLOCK"]

    # The broker echo of our own command was suppressed: no real-lock service
    # call, and the panel confirming the new state publishes nothing more.
    unlock_calls = async_mock_service(hass, "lock", "unlock")
    async_fire_mqtt_message(hass, "doorbell/lock/front/state", "unlocked")
    await hass.async_block_till_done()
    assert unlock_calls == []
    assert _published(mqtt_mock, "doorbell/lock/front/command") == ["UNLOCK"]


async def test_panel_state_lagging_real_lock_is_corrected(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    # Real lock is locked (fixture); panel claims unlocked → push LOCK to the panel.
    async_fire_mqtt_message(hass, "doorbell/lock/front/state", "unlocked")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/lock/front/command") == ["LOCK"]


async def test_gate_sync_both_directions(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    open_calls = async_mock_service(hass, "cover", "open_cover")
    stop_calls = async_mock_service(hass, "cover", "stop_cover")

    async_fire_mqtt_message(hass, "doorbell/cover/gate/command", "OPEN")
    async_fire_mqtt_message(hass, "doorbell/cover/gate/command", "STOP")
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in open_calls] == ["cover.real_gate"]
    assert [c.data["entity_id"] for c in stop_calls] == ["cover.real_gate"]

    # Panel says closed, real gate is closed: nothing to do.
    async_fire_mqtt_message(hass, "doorbell/cover/gate/state", "closed")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/cover/gate/command") == []

    hass.states.async_set("cover.real_gate", "opening")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/cover/gate/command") == []

    hass.states.async_set("cover.real_gate", "open")
    await hass.async_block_till_done()
    assert _published(mqtt_mock, "doorbell/cover/gate/command") == ["OPEN"]


async def test_lock_attributes_show_mapping(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    state = hass.states.get("lock.doorbell_front")
    assert state.attributes["mapped_entity_id"] == "lock.real_front"
    assert hass.states.get("lock.doorbell_workshop").attributes["mapped_entity_id"] is None
    assert (
        hass.states.get("cover.doorbell_gate").attributes["mapped_entity_id"] == "cover.real_gate"
    )
