"""Entity state driven by panel MQTT messages, and commands published back."""

from __future__ import annotations

from unittest.mock import call

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_mqtt_message
from pytest_homeassistant_custom_component.typing import MqttMockHAClient


async def test_entities_are_created_for_device(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    for entity_id in (
        "event.doorbell_ring",
        "binary_sensor.doorbell_bell_pressed",
        "binary_sensor.doorbell_connectivity",
        "sensor.doorbell_last_ring",
        "sensor.doorbell_logged_in_user",
        "sensor.doorbell_login_method",
        "sensor.doorbell_active_page",
        "select.doorbell_party_mode",
        "select.doorbell_house_state",
        "lock.doorbell_front",
        "lock.doorbell_workshop",
        "cover.doorbell_gate",
    ):
        assert hass.states.get(entity_id) is not None, entity_id
    assert hass.states.get("lock.doorbell_garage") is None


async def test_mqtt_subscription_uses_base_wildcard(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    subscribed = {c.args[0] for c in mqtt_mock.async_subscribe.call_args_list}
    assert "doorbell/#" in subscribed


async def test_ring_updates_event_entity_and_last_ring(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    assert hass.states.get("event.doorbell_ring").state == STATE_UNKNOWN
    async_fire_mqtt_message(hass, "doorbell/device_trigger/bell", "pressed")
    await hass.async_block_till_done()

    event = hass.states.get("event.doorbell_ring")
    assert event.state != STATE_UNKNOWN
    assert event.attributes["event_type"] == "ring"
    assert hass.states.get("sensor.doorbell_last_ring").state != STATE_UNKNOWN


async def test_ring_ignores_other_payloads(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    async_fire_mqtt_message(hass, "doorbell/device_trigger/bell", "released")
    await hass.async_block_till_done()
    assert hass.states.get("event.doorbell_ring").state == STATE_UNKNOWN


async def test_bell_pressed_pulse(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    async_fire_mqtt_message(hass, "doorbell/binary_sensor/bell_pressed/state", "ON")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.doorbell_bell_pressed").state == STATE_ON
    async_fire_mqtt_message(hass, "doorbell/binary_sensor/bell_pressed/state", "OFF")
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.doorbell_bell_pressed").state == STATE_OFF


async def test_last_ring_timestamp_from_panel(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    async_fire_mqtt_message(hass, "doorbell/sensor/last_ring/state", "2026-09-12T10:11:12+00:00")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.doorbell_last_ring").state == "2026-09-12T10:11:12+00:00"


async def test_session_sensors(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    async_fire_mqtt_message(hass, "doorbell/sensor/logged_in_user/state", "root")
    async_fire_mqtt_message(hass, "doorbell/sensor/login_method/state", "code")
    async_fire_mqtt_message(hass, "doorbell/sensor/active_page/state", "admin")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.doorbell_logged_in_user").state == "root"
    assert hass.states.get("sensor.doorbell_login_method").state == "code"
    assert hass.states.get("sensor.doorbell_active_page").state == "admin"

    async_fire_mqtt_message(hass, "doorbell/sensor/logged_in_user/state", "")
    async_fire_mqtt_message(hass, "doorbell/sensor/login_method/state", "none")
    async_fire_mqtt_message(hass, "doorbell/sensor/active_page/state", "home")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.doorbell_logged_in_user").state == STATE_UNKNOWN
    assert hass.states.get("sensor.doorbell_login_method").state == "none"
    assert hass.states.get("sensor.doorbell_active_page").state == "home"


async def test_availability_marks_entities_unavailable(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    assert hass.states.get("lock.doorbell_front").state != STATE_UNAVAILABLE
    async_fire_mqtt_message(hass, "doorbell/availability", "offline")
    await hass.async_block_till_done()
    assert hass.states.get("lock.doorbell_front").state == STATE_UNAVAILABLE
    assert hass.states.get("binary_sensor.doorbell_connectivity").state == STATE_OFF

    async_fire_mqtt_message(hass, "doorbell/availability", "online")
    await hass.async_block_till_done()
    assert hass.states.get("lock.doorbell_front").state != STATE_UNAVAILABLE
    assert hass.states.get("binary_sensor.doorbell_connectivity").state == STATE_ON


async def test_select_state_and_command(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    async_fire_mqtt_message(hass, "doorbell/select/partymode/state", "halloween")
    async_fire_mqtt_message(hass, "doorbell/select/house_state/state", "away")
    await hass.async_block_till_done()
    assert hass.states.get("select.doorbell_party_mode").state == "halloween"
    assert hass.states.get("select.doorbell_house_state").state == "away"

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.doorbell_party_mode", "option": "christmas"},
        blocking=True,
    )
    mqtt_mock.async_publish.assert_any_call(
        "doorbell/select/partymode/command", "christmas", 1, False
    )

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.doorbell_house_state", "option": "vacation"},
        blocking=True,
    )
    mqtt_mock.async_publish.assert_any_call(
        "doorbell/select/house_state/command", "vacation", 1, False
    )


async def test_invalid_select_state_is_ignored(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    async_fire_mqtt_message(hass, "doorbell/select/partymode/state", "not-a-mode")
    await hass.async_block_till_done()
    assert hass.states.get("select.doorbell_party_mode").state == STATE_UNKNOWN


async def test_lock_entity_state_and_commands(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    async_fire_mqtt_message(hass, "doorbell/lock/front/state", "locked")
    await hass.async_block_till_done()
    assert hass.states.get("lock.doorbell_front").state == "locked"
    assert hass.states.get("lock.doorbell_workshop").state == STATE_UNKNOWN

    for panel_state in ("unlocking", "unlocked", "jammed"):
        async_fire_mqtt_message(hass, "doorbell/lock/front/state", panel_state)
        await hass.async_block_till_done()
        assert hass.states.get("lock.doorbell_front").state == panel_state

    await hass.services.async_call(
        "lock", "lock", {"entity_id": "lock.doorbell_front"}, blocking=True
    )
    mqtt_mock.async_publish.assert_any_call("doorbell/lock/front/command", "LOCK", 1, False)
    await hass.services.async_call(
        "lock", "unlock", {"entity_id": "lock.doorbell_workshop"}, blocking=True
    )
    mqtt_mock.async_publish.assert_any_call("doorbell/lock/workshop/command", "UNLOCK", 1, False)


async def test_cover_entity_state_and_commands(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    for panel_state, expected in (
        ("open", "open"),
        ("opening", "opening"),
        ("closed", "closed"),
        ("closing", "closing"),
    ):
        async_fire_mqtt_message(hass, "doorbell/cover/gate/state", panel_state)
        await hass.async_block_till_done()
        assert hass.states.get("cover.doorbell_gate").state == expected

    for service, payload in (
        ("open_cover", "OPEN"),
        ("close_cover", "CLOSE"),
        ("stop_cover", "STOP"),
    ):
        await hass.services.async_call(
            "cover", service, {"entity_id": "cover.doorbell_gate"}, blocking=True
        )
        mqtt_mock.async_publish.assert_any_call("doorbell/cover/gate/command", payload, 1, False)


async def test_other_gate_ids_are_ignored(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    async_fire_mqtt_message(hass, "doorbell/cover/other/state", "open")
    await hass.async_block_till_done()
    assert hass.states.get("cover.doorbell_gate").state == STATE_UNKNOWN


async def test_unload_entry(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("lock.doorbell_front").state == STATE_UNAVAILABLE


async def test_publish_calls_use_qos1(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    await hass.services.async_call(
        "lock", "lock", {"entity_id": "lock.doorbell_front"}, blocking=True
    )
    assert (
        call("doorbell/lock/front/command", "LOCK", 1, False) in mqtt_mock.async_publish.mock_calls
    )
