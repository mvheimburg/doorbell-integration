"""Party mode and house state set from on/off entities in Home Assistant."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Event, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_mqtt_message,
    async_mock_service,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doormonitor.const import (
    CONF_API_TOKEN,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_LINKS,
    CONF_MODE_LINKS,
    DOMAIN,
)

from .conftest import PANEL_FRONT, REAL_FRONT, discover_panel

PARTY_CMD = "doorbell/select/partymode/command"
HOUSE_CMD = "doorbell/select/house_state/command"
HALLOWEEN = "input_boolean.halloween"
CHRISTMAS = "calendar.christmas"
BIRTHDAY = "input_boolean.birthday"
AWAY = "binary_sensor.everyone_away"

PARTY_LINKS = {
    "party_mode": {"halloween": HALLOWEEN, "christmas": CHRISTMAS, "birthday": BIRTHDAY},
}


def _published(mqtt_mock: MqttMockHAClient, topic: str) -> list[str]:
    return [c.args[1] for c in mqtt_mock.async_publish.call_args_list if c.args[0] == topic]


async def _set(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()


async def _panel(hass: HomeAssistant, topic: str, payload: str) -> None:
    async_fire_mqtt_message(hass, topic, payload)
    await hass.async_block_till_done()


@pytest.fixture
def mode_links() -> dict[str, dict[str, str]]:
    return PARTY_LINKS


@pytest.fixture
def real_states() -> dict[str, str]:
    return {REAL_FRONT: "locked", HALLOWEEN: "off", CHRISTMAS: "off", BIRTHDAY: "off"}


@pytest.fixture
async def published(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> MqttMockHAClient:
    """The MQTT mock with start-up publishes forgotten."""
    mqtt_mock.async_publish.reset_mock()
    return mqtt_mock


async def test_setup_sends_the_mode_the_sources_call_for(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    # Nothing is on, so normal; the panel already shows it but may be stale.
    assert _published(mqtt_mock, PARTY_CMD) == ["normal"]
    # No house state links: the integration leaves it alone.
    assert _published(mqtt_mock, HOUSE_CMD) == []


@pytest.mark.parametrize(
    "real_states", [{REAL_FRONT: "locked", HALLOWEEN: "on", BIRTHDAY: "on", CHRISTMAS: "off"}]
)
async def test_setup_prefers_the_later_option_when_sources_tie(
    hass: HomeAssistant, setup_entry: MockConfigEntry, mqtt_mock: MqttMockHAClient
) -> None:
    assert _published(mqtt_mock, PARTY_CMD)[-1] == "birthday"


async def test_source_turning_on_sets_the_mode_and_off_restores_default(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    await _set(hass, HALLOWEEN, "on")
    assert _published(published, PARTY_CMD) == ["halloween"]
    await _panel(hass, "doorbell/select/partymode/state", "halloween")

    await _set(hass, HALLOWEEN, "off")
    assert _published(published, PARTY_CMD) == ["halloween", "normal"]


async def test_latest_source_wins_and_falls_back_to_the_one_still_on(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    await _set(hass, CHRISTMAS, "on")
    await _panel(hass, "doorbell/select/partymode/state", "christmas")
    await _set(hass, BIRTHDAY, "on")
    await _panel(hass, "doorbell/select/partymode/state", "birthday")
    await _set(hass, BIRTHDAY, "off")
    assert _published(published, PARTY_CMD) == ["christmas", "birthday", "christmas"]


async def test_unavailable_source_keeps_its_last_state(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    await _set(hass, HALLOWEEN, "on")
    await _panel(hass, "doorbell/select/partymode/state", "halloween")
    await _set(hass, HALLOWEEN, "unavailable")
    await _set(hass, HALLOWEEN, "on")
    assert _published(published, PARTY_CMD) == ["halloween"]


async def test_choice_on_the_panel_is_kept_until_a_source_changes(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/select/partymode/state", "easter")
    assert _published(published, PARTY_CMD) == []

    await _set(hass, HALLOWEEN, "on")
    assert _published(published, PARTY_CMD) == ["halloween"]


@pytest.mark.parametrize(
    "real_states", [{REAL_FRONT: "locked", HALLOWEEN: "on", CHRISTMAS: "off", BIRTHDAY: "off"}]
)
async def test_panel_coming_online_is_told_the_mode(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    await _panel(hass, "doorbell/select/partymode/state", "halloween")
    await _panel(hass, "doorbell/availability", "offline")
    await _panel(hass, "doorbell/availability", "online")
    assert _published(published, PARTY_CMD) == ["halloween"]

    # It rebooted with normal; that arriving after it came online is corrected, not kept.
    published.async_publish.reset_mock()
    await _panel(hass, "doorbell/select/partymode/state", "normal")
    assert _published(published, PARTY_CMD) == ["halloween"]


@pytest.mark.parametrize("mode_links", [{"house_state": {"away": AWAY}}])
async def test_house_state_follows_its_source(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    await _set(hass, AWAY, "on")
    await _panel(hass, "doorbell/select/house_state/state", "away")
    await _set(hass, AWAY, "off")
    assert _published(published, HOUSE_CMD) == ["away", "home"]
    assert _published(published, PARTY_CMD) == []


async def test_unload_stops_setting_modes(
    hass: HomeAssistant, setup_entry: MockConfigEntry, published: MqttMockHAClient
) -> None:
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await _set(hass, HALLOWEEN, "on")
    assert _published(published, PARTY_CMD) == []


async def test_axis_left_to_knx_is_skipped(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    device_id = await discover_panel(hass, selects=("house_state",))
    await _panel(hass, "doorbell/availability", "online")
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=device_id,
        data={CONF_DEVICE_ID: device_id},
        options={CONF_LINKS: {}, CONF_MODE_LINKS: PARTY_LINKS},
        version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    await _set(hass, HALLOWEEN, "on")
    assert _published(mqtt_mock, PARTY_CMD) == []


@pytest.mark.parametrize("mode_links", [{}])
async def test_options_flow_links_modes(hass: HomeAssistant, setup_entry: MockConfigEntry) -> None:
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "modes"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "modes"
    sections = {str(k): v for k, v in result["data_schema"].schema.items()}
    assert list(sections) == ["party_mode", "house_state"]
    assert [str(k) for k in sections["party_mode"].schema.schema] == [
        "halloween",
        "christmas",
        "easter",
        "birthday",
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"party_mode": {"halloween": HALLOWEEN}, "house_state": {}},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert setup_entry.options == {
        CONF_LINKS: {PANEL_FRONT: REAL_FRONT, "cover.doorbell_gate": "cover.real_gate"},
        CONF_MODE_LINKS: {"party_mode": {"halloween": HALLOWEEN}},
    }


async def test_removing_the_admin_connection_keeps_mode_links(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    hass.config_entries.async_update_entry(
        setup_entry,
        options={**setup_entry.options, CONF_API_URL: "http://panel:8081", CONF_API_TOKEN: "t"},
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "admin"}
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_API_URL not in setup_entry.options
    assert setup_entry.options[CONF_MODE_LINKS] == PARTY_LINKS


AWAY_SWITCH = "input_boolean.away"
VACATION_SWITCH = "input_boolean.vacation"
HOUSE_SWITCHES = {"house_state": {"away": AWAY_SWITCH, "vacation": VACATION_SWITCH}}


def _switch_calls(calls: list[Event]) -> list[tuple[str, str]]:
    return [
        (c.data["service"], c.data["service_data"]["entity_id"])
        for c in calls
        if c.data["domain"] == "input_boolean"
    ]


@pytest.fixture
def switch_calls(hass: HomeAssistant) -> list[Event]:
    """Service calls, in order, with input_boolean turn_on/turn_off mocked."""
    async_mock_service(hass, "input_boolean", "turn_on")
    async_mock_service(hass, "input_boolean", "turn_off")
    return async_capture_events(hass, EVENT_CALL_SERVICE)


@pytest.mark.parametrize("mode_links", [HOUSE_SWITCHES])
@pytest.mark.parametrize(
    "real_states", [{REAL_FRONT: "locked", AWAY_SWITCH: "off", VACATION_SWITCH: "off"}]
)
async def test_choice_on_the_panel_is_written_back_to_the_switches(
    hass: HomeAssistant, published: MqttMockHAClient, switch_calls: list[Event]
) -> None:
    await _panel(hass, "doorbell/select/house_state/state", "away")
    assert _switch_calls(switch_calls) == [("turn_on", AWAY_SWITCH)]
    await _set(hass, AWAY_SWITCH, "on")

    await _panel(hass, "doorbell/select/house_state/state", "vacation")
    assert _switch_calls(switch_calls)[1:] == [
        ("turn_off", AWAY_SWITCH),
        ("turn_on", VACATION_SWITCH),
    ]
    await _set(hass, AWAY_SWITCH, "off")
    await _set(hass, VACATION_SWITCH, "on")

    await _panel(hass, "doorbell/select/house_state/state", "home")
    assert _switch_calls(switch_calls)[3:] == [("turn_off", VACATION_SWITCH)]
    await _set(hass, VACATION_SWITCH, "off")

    # The switches following the panel never sent the panel anything back.
    assert _published(published, HOUSE_CMD) == []

    # A change made in Home Assistant afterwards still reaches the panel.
    await _set(hass, AWAY_SWITCH, "on")
    assert _published(published, HOUSE_CMD) == ["away"]


@pytest.mark.parametrize("mode_links", [HOUSE_SWITCHES])
@pytest.mark.parametrize(
    "real_states", [{REAL_FRONT: "locked", AWAY_SWITCH: "off", VACATION_SWITCH: "off"}]
)
async def test_our_own_push_is_not_written_back(
    hass: HomeAssistant, published: MqttMockHAClient, switch_calls: list[Event]
) -> None:
    await _set(hass, VACATION_SWITCH, "on")
    assert _published(published, HOUSE_CMD) == ["vacation"]
    await _panel(hass, "doorbell/select/house_state/state", "vacation")
    assert _switch_calls(switch_calls) == []


@pytest.mark.parametrize("mode_links", [{"house_state": {"away": AWAY}}])
@pytest.mark.parametrize("real_states", [{REAL_FRONT: "locked", AWAY: "off"}])
async def test_sources_that_cannot_be_switched_are_left_alone(
    hass: HomeAssistant, published: MqttMockHAClient
) -> None:
    calls = async_capture_events(hass, EVENT_CALL_SERVICE)
    await _panel(hass, "doorbell/select/house_state/state", "away")
    assert [c.data["domain"] for c in calls] == []
    assert _published(published, HOUSE_CMD) == []

    # The panel keeps its choice until the sensor changes.
    await _set(hass, AWAY, "on")
    await _set(hass, AWAY, "off")
    assert _published(published, HOUSE_CMD) == ["home"]


@pytest.mark.parametrize("mode_links", [HOUSE_SWITCHES])
@pytest.mark.parametrize(
    "real_states", [{REAL_FRONT: "locked", AWAY_SWITCH: "on", VACATION_SWITCH: "off"}]
)
async def test_panel_boot_state_is_not_written_back(
    hass: HomeAssistant, published: MqttMockHAClient, switch_calls: list[Event]
) -> None:
    await _panel(hass, "doorbell/select/house_state/state", "away")
    await _panel(hass, "doorbell/availability", "offline")
    await _panel(hass, "doorbell/availability", "online")
    await _panel(hass, "doorbell/select/house_state/state", "home")
    assert _switch_calls(switch_calls) == []
    assert _published(published, HOUSE_CMD)[-1] == "away"
