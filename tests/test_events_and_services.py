"""Bus events, device triggers and domain services."""

from __future__ import annotations

from typing import Any

import pytest
import voluptuous as vol
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
    async_get_device_automations,
    async_mock_service,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doorbell.const import (
    DOMAIN,
    EVENT_GATE_REQUEST,
    EVENT_LOCK_REQUEST,
    EVENT_LOGIN,
    EVENT_LOGOUT,
    EVENT_RING,
)


def _capture(hass: HomeAssistant, event_type: str) -> list[dict[str, Any]]:
    seen: list[dict[str, Any]] = []

    @callback
    def _listener(event: Event) -> None:
        seen.append(dict(event.data))

    hass.bus.async_listen(event_type, _listener)
    return seen


def _device_id(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert device is not None
    return device.id


async def test_ring_fires_bus_event_with_device_id(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    seen = _capture(hass, EVENT_RING)
    async_fire_mqtt_message(hass, "doorbell/device_trigger/bell", "pressed")
    await hass.async_block_till_done()
    assert len(seen) == 1
    assert seen[0]["device_id"] == _device_id(hass, setup_entry)
    assert seen[0]["entry_id"] == setup_entry.entry_id
    assert seen[0]["topic"] == "doorbell/device_trigger/bell"


async def test_login_and_logout_events(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    logins = _capture(hass, EVENT_LOGIN)
    logouts = _capture(hass, EVENT_LOGOUT)

    async_fire_mqtt_message(hass, "doorbell/sensor/logged_in_user/state", "Alice")
    async_fire_mqtt_message(hass, "doorbell/sensor/login_method/state", "ble")
    async_fire_mqtt_message(hass, "doorbell/sensor/active_page/state", "control")
    await hass.async_block_till_done()
    assert logins == [
        {
            "entry_id": setup_entry.entry_id,
            "device_id": _device_id(hass, setup_entry),
            "name": "Doorbell",
            "user": "Alice",
            "method": "ble",
            "page": "control",
        }
    ]
    assert logouts == []

    # Switching pages while logged in is not a new login.
    async_fire_mqtt_message(hass, "doorbell/sensor/active_page/state", "admin")
    await hass.async_block_till_done()
    assert len(logins) == 1

    async_fire_mqtt_message(hass, "doorbell/sensor/logged_in_user/state", "")
    async_fire_mqtt_message(hass, "doorbell/sensor/login_method/state", "none")
    async_fire_mqtt_message(hass, "doorbell/sensor/active_page/state", "home")
    await hass.async_block_till_done()
    assert len(logouts) == 1


async def test_panel_lock_request_fires_event_without_mapping(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    seen = _capture(hass, EVENT_LOCK_REQUEST)
    async_fire_mqtt_message(hass, "doorbell/lock/front/command", "UNLOCK")
    await hass.async_block_till_done()
    assert seen[-1]["door"] == "front"
    assert seen[-1]["action"] == "unlock"
    assert seen[-1]["entity_id"] is None


async def test_own_commands_are_not_reported_as_panel_requests(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    seen = _capture(hass, EVENT_LOCK_REQUEST)
    await hass.services.async_call(
        "lock", "lock", {"entity_id": "lock.doorbell_front"}, blocking=True
    )
    await hass.async_block_till_done()
    # The broker (and the test broker) echoes our own command back to our
    # wildcard subscription; that echo must not look like a panel request.
    assert seen == []

    # A later, identical command from the panel is a real request again.
    async_fire_mqtt_message(hass, "doorbell/lock/front/command", "LOCK")
    await hass.async_block_till_done()
    assert len(seen) == 1


async def test_panel_gate_request_fires_event(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    seen = _capture(hass, EVENT_GATE_REQUEST)
    async_fire_mqtt_message(hass, "doorbell/cover/gate/command", "OPEN")
    await hass.async_block_till_done()
    assert seen[-1]["gate"] == "gate"
    assert seen[-1]["action"] == "open"


async def test_device_triggers_are_listed(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    device_id = _device_id(hass, setup_entry)
    triggers = await async_get_device_automations(hass, DeviceAutomationType.TRIGGER, device_id)
    ours = {t["type"] for t in triggers if t["domain"] == DOMAIN}
    assert ours == {"ring", "login", "logout", "lock_request", "gate_request"}


async def test_device_trigger_ring_runs_automation(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    device_id = _device_id(hass, setup_entry)
    calls = async_mock_service(hass, "test", "automation")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_id,
                        "type": "ring",
                    },
                    "action": {"service": "test.automation", "data": {"who": "doorbell"}},
                }
            ]
        },
    )
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "doorbell/device_trigger/bell", "pressed")
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["who"] == "doorbell"


async def test_services_publish_modes(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    await hass.services.async_call(DOMAIN, "set_party_mode", {"mode": "easter"}, blocking=True)
    mqtt_mock.async_publish.assert_any_call("doorbell/select/partymode/command", "easter", 1, False)

    device_id = _device_id(hass, setup_entry)
    await hass.services.async_call(
        DOMAIN, "set_house_state", {"state": "away", "device_id": device_id}, blocking=True
    )
    mqtt_mock.async_publish.assert_any_call("doorbell/select/house_state/command", "away", 1, False)


async def test_service_rejects_invalid_mode(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, "set_party_mode", {"mode": "rave"}, blocking=True)


async def test_service_rejects_unknown_device(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "set_party_mode", {"mode": "normal", "device_id": "nope"}, blocking=True
        )


async def test_purge_mqtt_discovery_clears_retained_configs(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    await hass.services.async_call(DOMAIN, "purge_mqtt_discovery", {}, blocking=True)
    published = {c.args[0]: c for c in mqtt_mock.async_publish.call_args_list}
    for topic in (
        "homeassistant/device_trigger/doorbell/config",
        "homeassistant/sensor/last_ring/config",
        "homeassistant/binary_sensor/bell_pressed/config",
        "homeassistant/sensor/logged_in_user/config",
        "homeassistant/sensor/login_method/config",
        "homeassistant/sensor/active_page/config",
        "homeassistant/lock/front/config",
        "homeassistant/lock/workshop/config",
        "homeassistant/cover/gate/config",
        "homeassistant/select/partymode/config",
        "homeassistant/select/house_state/config",
    ):
        assert topic in published, topic
        assert published[topic].args[1:] == ("", 1, True)
