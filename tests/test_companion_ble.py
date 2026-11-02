"""Discover only validated transmitter IDs belonging to the selected HA user."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.doormonitor.companion_ble import companion_beacons

UUID = "12345678-1234-5678-9abc-123456789abc"


def sensor(
    hass,
    *,
    owner="ha-a",
    suffix="ble_emitter",
    value=None,
    state="Transmitting",
    disabled=False,
    domain="mobile_app",
    title="Phone A",
    webhook="hook",
    **attributes,
):
    entry = MockConfigEntry(
        domain=domain, title=title, data={"user_id": owner, "webhook_id": webhook}
    )
    entry.add_to_hass(hass)
    entity = er.async_get(hass).async_get_or_create(
        "sensor",
        domain,
        f"{webhook}_{suffix}",
        config_entry=entry,
        suggested_object_id="renamed_reading",
        disabled_by=er.RegistryEntryDisabler.USER if disabled else None,
    )
    hass.states.async_set(entity.entity_id, state, {"id": value, **attributes})
    return entry, entity


def test_discovers_owned_renamed_sensor_and_deduplicates(hass: HomeAssistant):
    sensor(hass, value=f"{UUID}_100_40004")
    sensor(hass, value=f"{UUID.upper()}_100_40004", webhook="second")
    sensor(hass, value=f"{UUID}_101_2", webhook="third", title="Phone B")
    sensor(hass, owner="ha-b", value=f"{UUID}_5_6", webhook="other")
    assert companion_beacons(hass, "ha-a") == [
        {"name": "Phone A", "id": f"{UUID}_100_40004"},
        {"name": "Phone B", "id": f"{UUID}_101_2"},
    ]
    assert companion_beacons(hass, "ha-b") == [
        {"name": "Phone A", "id": f"{UUID}_5_6"},
    ]
    assert companion_beacons(hass, "missing") == []


@pytest.mark.parametrize(
    "extra",
    [
        {"state": "unavailable"},
        {"state": "unknown"},
        {"disabled": True},
        {"suffix": "beacon_monitor"},
        {"domain": "mqtt"},
        {"value": None},
        {"value": "bad_1_2"},
        {"value": f"{UUID}_65536_1"},
        {"value": f"{UUID}_-1_2"},
        {"value": f"{UUID}_1"},
        {"value": f"{UUID}_1_2_extra"},
        {"value": 123},
        {"Supports transmitter": False},
    ],
)
def test_excludes_unusable_and_unrelated_sensors(hass: HomeAssistant, extra):
    sensor(hass, **({"value": f"{UUID}_1_2"} | extra))
    assert companion_beacons(hass, "ha-a") == []


def test_stopped_transmitter_keeps_its_configured_identity(hass: HomeAssistant):
    sensor(hass, value=f"{UUID}_1_2", state="Stopped")
    assert companion_beacons(hass, "ha-a") == [{"name": "Phone A", "id": f"{UUID}_1_2"}]


async def test_missing_state_and_disabled_registration_are_excluded(hass: HomeAssistant):
    from homeassistant.config_entries import ConfigEntryDisabler

    entry, entity = sensor(hass, value=f"{UUID}_1_2")
    hass.states.async_remove(entity.entity_id)
    assert companion_beacons(hass, "ha-a") == []
    hass.states.async_set(entity.entity_id, "Transmitting", {"id": f"{UUID}_1_2"})
    await hass.config_entries.async_set_disabled_by(entry.entry_id, ConfigEntryDisabler.USER)
    assert companion_beacons(hass, "ha-a") == []
