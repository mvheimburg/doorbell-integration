"""Config and options flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doorbell.config_flow import parse_doors
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


def test_parse_doors() -> None:
    assert parse_doors("Front, workshop ,Garage,, front") == ["front", "workshop", "garage"]
    assert parse_doors(["a", " b "]) == ["a", "b"]
    assert parse_doors("Side door") == ["side_door"]


async def test_user_flow_creates_entry(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Front door panel",
            CONF_BASE_TOPIC: "/panel/",
            CONF_DISCOVERY_PREFIX: "homeassistant",
            CONF_DOORS: "front, garage",
            CONF_GATE_ID: "Gate",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Front door panel"
    assert result["data"] == {
        CONF_NAME: "Front door panel",
        CONF_BASE_TOPIC: "panel",
        CONF_DISCOVERY_PREFIX: "homeassistant",
        CONF_DOORS: ["front", "garage"],
        CONF_GATE_ID: "gate",
    }
    assert result["result"].unique_id == "panel"
    assert hass.states.get("lock.front_door_panel_front") is not None


async def test_user_flow_validation_errors(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "x",
            CONF_BASE_TOPIC: "door/#",
            CONF_DISCOVERY_PREFIX: "homeassistant",
            CONF_DOORS: " , ",
            CONF_GATE_ID: "gate",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_BASE_TOPIC: "invalid_topic", CONF_DOORS: "no_doors"}


async def test_user_flow_aborts_on_duplicate_topic(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Again",
            CONF_BASE_TOPIC: "doorbell",
            CONF_DISCOVERY_PREFIX: "homeassistant",
            CONF_DOORS: "front",
            CONF_GATE_ID: "gate",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_maps_entities_and_reloads(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    hass.states.async_set("lock.real_front", "locked")
    hass.states.async_set("cover.real_gate", "closed")

    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    keys = {str(k) for k in result["data_schema"].schema}
    assert {"lock_front", "lock_workshop", CONF_GATE_ENTITY} <= keys

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_BASE_TOPIC: "doorbell",
            CONF_DISCOVERY_PREFIX: "homeassistant",
            CONF_DOORS: "front, cellar",
            CONF_GATE_ID: "gate",
            "lock_front": "lock.real_front",
            "lock_workshop": "lock.gone",  # workshop is being removed; mapping dropped
            CONF_GATE_ENTITY: "cover.real_gate",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert setup_entry.options == {
        CONF_BASE_TOPIC: "doorbell",
        CONF_DISCOVERY_PREFIX: "homeassistant",
        CONF_DOORS: ["front", "cellar"],
        CONF_GATE_ID: "gate",
        CONF_LOCK_MAP: {"front": "lock.real_front"},
        CONF_GATE_ENTITY: "cover.real_gate",
    }

    # Entry reloaded: cellar appeared, workshop is gone (registry entry removed too).
    assert hass.states.get("lock.doorbell_cellar") is not None
    assert hass.states.get("lock.doorbell_workshop") is None
    assert (
        hass.states.get("lock.doorbell_front").attributes["mapped_entity_id"] == "lock.real_front"
    )
