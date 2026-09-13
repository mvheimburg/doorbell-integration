from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doorbell.const import (
    CONF_BASE_TOPIC,
    CONF_DISCOVERY_PREFIX,
    CONF_DOORS,
    CONF_GATE_ENTITY,
    CONF_GATE_ID,
    CONF_LOCK_MAP,
    CONF_NAME,
    DOMAIN,
)

BASE_DATA: dict[str, Any] = {
    CONF_NAME: "Doorbell",
    CONF_BASE_TOPIC: "doorbell",
    CONF_DISCOVERY_PREFIX: "homeassistant",
    CONF_DOORS: ["front", "workshop"],
    CONF_GATE_ID: "gate",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/ in the test Home Assistant."""


@pytest.fixture
def entry_options() -> dict[str, Any]:
    return {}


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, entry_options: dict[str, Any]
) -> AsyncGenerator[MockConfigEntry]:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Doorbell",
        unique_id="doorbell",
        data=BASE_DATA,
        options=entry_options,
        version=2,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry


@pytest.fixture
def mapped_options() -> dict[str, Any]:
    return {
        CONF_LOCK_MAP: {"front": "lock.real_front"},
        CONF_GATE_ENTITY: "cover.real_gate",
    }
