"""Config flow, options flow and entry setup."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doormonitor.const import CONF_DEVICE_ID, CONF_LINKS, DOMAIN

from .conftest import (
    PANEL_FRONT,
    PANEL_GATE,
    PANEL_WORKSHOP,
    REAL_FRONT,
    REAL_GATE,
    discover_panel,
)


def _offered_devices(result: dict) -> list[dict[str, str]]:
    """The device options the user step offers."""
    (selector,) = result["data_schema"].schema.values()
    return selector.config["options"]


async def test_user_flow_picks_device_and_links(hass: HomeAssistant, panel: str) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert _offered_devices(result) == [{"value": panel, "label": "doorbell"}]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: panel}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "links"
    # Only the panel's locks and cover, not its sensors.
    assert [str(k) for k in result["data_schema"].schema] == [
        PANEL_GATE,
        PANEL_FRONT,
        PANEL_WORKSHOP,
    ]

    hass.states.async_set(REAL_FRONT, "locked")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {PANEL_FRONT: REAL_FRONT}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "doorbell"
    assert result["data"] == {CONF_DEVICE_ID: panel}
    assert result["result"].options == {CONF_LINKS: {PANEL_FRONT: REAL_FRONT}}
    assert result["result"].unique_id == panel
    assert result["result"].state is ConfigEntryState.LOADED


async def test_user_flow_offers_the_panel_but_not_other_mqtt_devices(
    hass: HomeAssistant, panel: str, mqtt_mock: MqttMockHAClient
) -> None:
    """An MQTT lock or cover of its own does not make a device a panel."""
    (mqtt_entry,) = hass.config_entries.async_entries("mqtt")
    dr.async_get(hass).async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "garage_controller")},
        name="Garage Controller",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert _offered_devices(result) == [{"value": panel, "label": "doorbell"}]


async def test_user_flow_offers_an_offline_panel(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """A panel that has not come online is still in the registry, so it is offered."""
    device_id = await discover_panel(hass)
    assert hass.states.get(PANEL_FRONT).state == "unavailable"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert _offered_devices(result) == [{"value": device_id, "label": "doorbell"}]


async def test_user_flow_aborts_when_no_panel_was_discovered(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_panels_found"


async def test_user_flow_aborts_on_duplicate_device(
    hass: HomeAssistant, setup_entry: MockConfigEntry, panel: str
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: panel}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_relinks_and_reloads(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    before = setup_entry.runtime_data
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["links", "admin"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "links"}
    )
    assert result["type"] is FlowResultType.FORM
    suggested = {str(k): k.description["suggested_value"] for k in result["data_schema"].schema}
    assert suggested == {PANEL_GATE: REAL_GATE, PANEL_FRONT: REAL_FRONT, PANEL_WORKSHOP: None}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {PANEL_WORKSHOP: "lock.real_workshop"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert setup_entry.options == {CONF_LINKS: {PANEL_WORKSHOP: "lock.real_workshop"}}
    assert setup_entry.runtime_data is not before


async def test_setup_fails_when_device_is_gone(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_DEVICE_ID: "nope"}, options={CONF_LINKS: {}}, version=1
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR
