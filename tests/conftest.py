from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_mqtt_message
from pytest_homeassistant_custom_component.typing import MqttMockHAClient, MqttMockPahoClient

from custom_components.doorbell.const import CONF_DEVICE_ID, CONF_LINKS, DOMAIN


@pytest.fixture(autouse=True)
def close_mqtt_socket(mqtt_client_mock: MqttMockPahoClient) -> Generator[None]:
    """Close the fake broker socket after each test.

    The plugin's mocked paho client opens a socket on connect but never closes it, so the MQTT
    integration's 1 s misc timer outlives the test and fails the lingering-timer check.
    """
    yield
    if mqtt_client_mock.on_socket_close is not None:
        mqtt_client_mock.on_socket_close(mqtt_client_mock, None, Mock(fileno=Mock(return_value=-1)))


# Trimmed copies of what dxbell's `discovery_manifest()` publishes.
_DEVICE = {"ids": ["doorbell"], "name": "doorbell", "mdl": "doorbell-dioxus", "mf": "doorbell"}
_AVAILABILITY = {"avty_t": "doorbell/availability", "pl_avail": "online", "pl_not_avail": "offline"}


def _lock_config(door: str) -> dict[str, Any]:
    return {
        "name": door.capitalize(),
        "uniq_id": f"doorbell_lock_{door}",
        "cmd_t": f"doorbell/lock/{door}/command",
        "stat_t": f"doorbell/lock/{door}/state",
        "pl_lock": "LOCK",
        "pl_unlk": "UNLOCK",
        "stat_locked": "locked",
        "stat_unlocked": "unlocked",
        "stat_locking": "locking",
        "stat_unlocking": "unlocking",
        "stat_jammed": "jammed",
        "dev": _DEVICE,
        **_AVAILABILITY,
    }


_GATE_CONFIG = {
    "name": "Gate",
    "uniq_id": "doorbell_gate",
    "cmd_t": "doorbell/cover/gate/command",
    "stat_t": "doorbell/cover/gate/state",
    "pl_open": "OPEN",
    "pl_close": "CLOSE",
    "pl_stop": "STOP",
    "stat_open": "open",
    "stat_opening": "opening",
    "stat_closed": "closed",
    "stat_closing": "closing",
    "stat_stopped": "stopped",
    "dev": _DEVICE,
    **_AVAILABILITY,
}

_LAST_RING_CONFIG = {
    "name": "last_ring",
    "uniq_id": "doorbell_last_ring",
    "stat_t": "doorbell/sensor/last_ring/state",
    "dev_cla": "timestamp",
    "dev": _DEVICE,
    **_AVAILABILITY,
}

PANEL_FRONT = "lock.doorbell_front"
PANEL_WORKSHOP = "lock.doorbell_workshop"
PANEL_GATE = "cover.doorbell_gate"
REAL_FRONT = "lock.real_front"
REAL_GATE = "cover.real_gate"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/ in the test Home Assistant."""


@pytest.fixture
async def panel(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> str:
    """Discover the panel through MQTT like Home Assistant would; returns its device id."""
    for door in ("front", "workshop"):
        async_fire_mqtt_message(
            hass, f"homeassistant/lock/{door}/config", json.dumps(_lock_config(door))
        )
    async_fire_mqtt_message(hass, "homeassistant/cover/gate/config", json.dumps(_GATE_CONFIG))
    async_fire_mqtt_message(
        hass, "homeassistant/sensor/last_ring/config", json.dumps(_LAST_RING_CONFIG)
    )
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "doorbell/availability", "online")
    async_fire_mqtt_message(hass, "doorbell/lock/front/state", "locked")
    async_fire_mqtt_message(hass, "doorbell/lock/workshop/state", "locked")
    async_fire_mqtt_message(hass, "doorbell/cover/gate/state", "closed")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL_FRONT).state == "locked"
    assert hass.states.get(PANEL_GATE).state == "closed"

    (device,) = dr.async_get(hass).async_get_devices(identifiers={("mqtt", "doorbell")})
    return device.id


@pytest.fixture
def real_states() -> dict[str, str]:
    return {REAL_FRONT: "locked", REAL_GATE: "closed"}


@pytest.fixture
def links() -> dict[str, str]:
    return {PANEL_FRONT: REAL_FRONT, PANEL_GATE: REAL_GATE}


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    panel: str,
    real_states: dict[str, str],
    links: dict[str, str],
) -> MockConfigEntry:
    for entity_id, state in real_states.items():
        hass.states.async_set(entity_id, state)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="doorbell",
        unique_id=panel,
        data={CONF_DEVICE_ID: panel},
        options={CONF_LINKS: links},
        version=3,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
