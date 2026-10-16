from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.doormonitor.house_state import HouseStateSync


async def test_overlay_updates_reconnect_and_fallback(hass: HomeAssistant) -> None:
    service = AsyncMock()
    hass.services.async_register("select", "select_option", service)
    hass.states.async_set("select.party", "normal")
    hass.states.async_set("sensor.house", "day", {"overlay": "christmas"})
    sync = HouseStateSync(hass, "sensor.house", {"party_mode": "select.party"}, {})
    sync.async_start()
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == "christmas"
    hass.states.async_set("sensor.house", "day", {"overlay": "halloween"})
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == "halloween"
    hass.states.async_set("sensor.house", "unavailable")
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == "halloween"
    hass.states.async_set("select.party", "unavailable")
    hass.states.async_set("select.party", "normal")
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == "halloween"
    hass.states.async_set("select.party", "halloween")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.house", "day", {"overlay": "unmapped"})
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == "normal"
    sync.async_stop()


async def test_options_enable_following_and_override_legacy_links(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    mqtt_mock,
) -> None:
    hass.states.async_set("sensor.house", "day", {"overlay": "christmas", "occupied": True})
    hass.states.async_set("input_boolean.halloween", "on")
    hass.config_entries.async_update_entry(
        setup_entry,
        options={
            **setup_entry.options,
            "mode_links": {"party_mode": {"halloween": "input_boolean.halloween"}},
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "house_state"},
    )
    assert result["step_id"] == "house_state"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "house_state_source": "sensor.house",
            "house_state_axes": ["party_mode"],
            "overlay_map": {"custom": "invalid"},
        },
    )
    assert result["errors"] == {"overlay_map": "invalid_overlay_map"}
    mqtt_mock.async_publish.reset_mock()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "house_state_source": "sensor.house",
            "house_state_axes": ["party_mode"],
            "overlay_map": {"custom": "birthday"},
        },
    )
    await hass.async_block_till_done()
    assert setup_entry.options["overlay_map"] == {"custom": "birthday"}
    published = [
        call.args[1]
        for call in mqtt_mock.async_publish.call_args_list
        if call.args[0] == "doorbell/select/partymode/command"
    ]
    assert published == ["christmas"]
    mqtt_mock.async_publish.reset_mock()
    hass.states.async_set("sensor.house", "day", {"overlay": "custom", "occupied": True})
    await hass.async_block_till_done()
    assert any(
        call.args[:2] == ("doorbell/select/partymode/command", "birthday")
        for call in mqtt_mock.async_publish.call_args_list
    )
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "house_state"}
    )
    mqtt_mock.async_publish.reset_mock()
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "house_state_axes": ["party_mode"],
            "overlay_map": {},
        },
    )
    await hass.async_block_till_done()
    published = [
        call.args[1]
        for call in mqtt_mock.async_publish.call_args_list
        if call.args[0] == "doorbell/select/partymode/command"
    ]
    assert published == ["halloween"]


async def test_custom_mapping_and_vacation_role(hass: HomeAssistant) -> None:
    service = AsyncMock()
    hass.services.async_register("select", "select_option", service)
    hass.states.async_set("select.party", "normal")
    hass.states.async_set("select.house", "home")
    hass.states.async_set(
        "sensor.house",
        "trip",
        {
            "overlay": "kids_party",
            "occupied": False,
            "active_path": ["out", "trip"],
            "config": {"roles": {"vacation": "out"}},
        },
    )
    sync = HouseStateSync(
        hass,
        "sensor.house",
        {
            "party_mode": "select.party",
            "house_state": "select.house",
        },
        {"kids_party": "birthday"},
    )
    sync.async_start()
    await hass.async_block_till_done()
    assert {call.args[0].data["option"] for call in service.call_args_list} == {
        "birthday",
        "vacation",
    }
    sync.async_stop()


@pytest.mark.parametrize(
    ("occupied", "path", "expected"),
    [
        (True, ["here", "sleep"], "home"),
        (False, ["out"], "away"),
        (False, ["trip", "long_trip"], "vacation"),
    ],
)
async def test_house_state_uses_roles_and_inherited_occupancy(
    hass: HomeAssistant,
    occupied,
    path,
    expected,
) -> None:
    service = AsyncMock()
    hass.services.async_register("select", "select_option", service)
    hass.states.async_set("select.house", "unexpected")
    hass.states.async_set(
        "sensor.house",
        path[-1],
        {
            "occupied": occupied,
            "active_path": path,
            "config": {"roles": {"vacation": "trip"}},
        },
    )
    sync = HouseStateSync(hass, "sensor.house", {"house_state": "select.house"}, {})
    sync.async_start()
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == expected
    sync.async_stop()


async def test_missing_source_recovery_and_unload(hass: HomeAssistant) -> None:
    service = AsyncMock()
    hass.services.async_register("select", "select_option", service)
    hass.states.async_set("select.party", "birthday")
    sync = HouseStateSync(hass, "sensor.house", {"party_mode": "select.party"}, {})
    sync.async_start()
    await hass.async_block_till_done()
    service.assert_not_called()
    hass.states.async_set("sensor.house", "day", {"overlay": "none"})
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == "normal"
    service.reset_mock()
    sync.async_stop()
    hass.states.async_set("sensor.house", "day", {"overlay": "easter"})
    await hass.async_block_till_done()
    service.assert_not_called()


@pytest.mark.parametrize("overlay", ["halloween", "christmas", "easter", "birthday"])
async def test_standard_overlay_ids(hass: HomeAssistant, overlay: str) -> None:
    service = AsyncMock()
    hass.services.async_register("select", "select_option", service)
    hass.states.async_set("select.party", "normal")
    hass.states.async_set(
        "sensor.house",
        "day",
        {
            "overlay": overlay,
            "overlay_choice": "auto",
            "overlay_rule": overlay,
        },
    )
    sync = HouseStateSync(hass, "sensor.house", {"party_mode": "select.party"}, {})
    sync.async_start()
    await hass.async_block_till_done()
    assert service.call_args.args[0].data["option"] == overlay
    sync.async_stop()
