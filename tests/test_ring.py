"""Ring notifications: chosen people's phones are notified, some only while they are home."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
    async_mock_service,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.doormonitor.const import (
    CONF_DEVICE_ID,
    CONF_LINKS,
    CONF_RING_NOTIFY,
    CONF_RING_SOURCE,
    DOMAIN,
)
from custom_components.doormonitor.ring import message_language

from .conftest import _AVAILABILITY, _DEVICE, discover_panel

BELL_TOPIC = "doorbell/binary_sensor/bell_pressed/state"
BELL = "binary_sensor.doorbell_bell_pressed"
PERSON_A = "person.person_a"
PERSON_B = "person.person_b"

_BELL_CONFIG = {
    "name": "bell_pressed",
    "uniq_id": "doorbell_bell_pressed",
    "stat_t": BELL_TOPIC,
    "dev": _DEVICE,
    **_AVAILABILITY,
}


def _person(hass: HomeAssistant, person: str, phone: str, state: str) -> list[ServiceCall]:
    """A person with one Companion-app phone; returns the calls to its notify service."""
    app = MockConfigEntry(domain="mobile_app")
    app.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=app.entry_id, identifiers={("mobile_app", phone)}, name=phone
    )
    tracker = er.async_get(hass).async_get_or_create(
        "device_tracker", "mobile_app", phone, device_id=device.id
    )
    hass.states.async_set(
        person, state, {"device_trackers": [tracker.entity_id], "friendly_name": person}
    )
    return async_mock_service(hass, "notify", f"mobile_app_{phone.lower().replace(' ', '_')}")


async def _discover_bell(hass: HomeAssistant) -> str:
    device_id = await discover_panel(hass)
    async_fire_mqtt_message(
        hass, "homeassistant/binary_sensor/bell_pressed/config", json.dumps(_BELL_CONFIG)
    )
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, "doorbell/availability", "online")
    async_fire_mqtt_message(hass, BELL_TOPIC, "OFF")
    await hass.async_block_till_done()
    assert hass.states.get(BELL).state == "off"
    return device_id


async def _entry(hass: HomeAssistant, device_id: str, **options: Any) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="doorbell",
        unique_id=device_id,
        data={CONF_DEVICE_ID: device_id},
        options={CONF_LINKS: {}, **options},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _ring(hass: HomeAssistant) -> None:
    async_fire_mqtt_message(hass, BELL_TOPIC, "ON")
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, BELL_TOPIC, "OFF")
    await hass.async_block_till_done()


@pytest.fixture
async def bell(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> str:
    return await _discover_bell(hass)


async def test_ring_skips_away_people_who_asked_for_it(
    hass: HomeAssistant, bell: str, freezer: FrozenDateTimeFactory
) -> None:
    home = _person(hass, PERSON_A, "Phone A", "not_home")
    anywhere = _person(hass, PERSON_B, "Phone B", "not_home")
    await _entry(
        hass,
        bell,
        **{
            CONF_RING_NOTIFY: [
                {"person": PERSON_A, "only_home": True},
                {"person": PERSON_B, "only_home": False},
            ]
        },
    )

    await _ring(hass)
    assert home == []
    (call,) = anywhere
    assert call.data["title"] == "doorbell"
    assert call.data["message"] == "Someone is at the door"
    assert call.data["data"]["push"] == {"interruption-level": "time-sensitive"}

    hass.states.async_set(PERSON_A, "home", hass.states.get(PERSON_A).attributes)
    freezer.tick(timedelta(seconds=11))  # past the double-press window
    await _ring(hass)
    assert len(home) == 1
    assert len(anywhere) == 2


async def test_double_press_and_reconnect_send_once(hass: HomeAssistant, bell: str) -> None:
    calls = _person(hass, PERSON_A, "Phone A", "home")
    await _entry(hass, bell, **{CONF_RING_NOTIFY: [{"person": PERSON_A, "only_home": True}]})

    await _ring(hass)
    await _ring(hass)
    assert len(calls) == 1

    # The panel going offline and back with the sensor on is not a ring.
    async_fire_mqtt_message(hass, "doorbell/availability", "offline")
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, "doorbell/availability", "online")
    async_fire_mqtt_message(hass, BELL_TOPIC, "ON")
    await hass.async_block_till_done()
    assert len(calls) == 1


async def test_message_follows_home_assistant_language(hass: HomeAssistant, bell: str) -> None:
    await hass.config.async_update(language="nb")
    calls = _person(hass, PERSON_A, "Phone A", "home")
    await _entry(hass, bell, **{CONF_RING_NOTIFY: [{"person": PERSON_A, "only_home": False}]})
    await _ring(hass)
    assert calls[0].data["message"] == "Det ringer på døra"


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("nb-NO", "nb"),
        ("no", "nb"),
        ("nn", "nb"),
        ("NB_no", "nb"),
        ("en-GB", "en"),
        ("de", "en"),
        (None, "en"),
        ("", "en"),
    ],
)
def test_message_language(language: str | None, expected: str) -> None:
    assert message_language(language) == expected


async def test_event_entity_as_ring_signal(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    device_id = await discover_panel(hass)  # no bell sensor: the bell is on KNX
    hass.states.async_set("event.knx_bell", "unknown")
    calls = _person(hass, PERSON_A, "Phone A", "home")
    await _entry(
        hass,
        device_id,
        **{
            CONF_RING_NOTIFY: [{"person": PERSON_A, "only_home": False}],
            CONF_RING_SOURCE: "event.knx_bell",
        },
    )
    hass.states.async_set("event.knx_bell", "2026-10-28T12:00:00+00:00")
    await hass.async_block_till_done()
    assert len(calls) == 1
    hass.states.async_set("event.knx_bell", "unavailable")
    hass.states.async_set("event.knx_bell", "2026-10-28T12:00:00+00:00")
    await hass.async_block_till_done()
    assert len(calls) == 1


async def test_options_flow_sets_only_when_home_per_person(hass: HomeAssistant, bell: str) -> None:
    calls = _person(hass, PERSON_A, "Phone A", "not_home")
    _person(hass, PERSON_B, "Phone B", "not_home")
    entry = await _entry(hass, bell)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "notify"}
    )
    assert result["step_id"] == "notify"
    assert result["description_placeholders"] == {"bell": BELL}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RING_NOTIFY: [PERSON_A, PERSON_B]}
    )
    assert result["step_id"] == "notify_home"
    ((field, selector),) = result["data_schema"].schema.items()
    assert str(field) == "only_home"
    assert field.default() == []
    assert selector.config["options"] == [
        {"value": PERSON_A, "label": PERSON_A},
        {"value": PERSON_B, "label": PERSON_B},
    ]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"only_home": [PERSON_B]}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_RING_NOTIFY] == [
        {"person": PERSON_A, "only_home": False},
        {"person": PERSON_B, "only_home": True},
    ]
    assert CONF_RING_SOURCE not in entry.options
    assert entry.options[CONF_LINKS] == {}

    await _ring(hass)  # the reloaded entry notifies
    assert len(calls) == 1

    # Opening it again shows what was saved; clearing the people turns it off.
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "notify"}
    )
    suggested = {str(k): k.description["suggested_value"] for k in result["data_schema"].schema}
    assert suggested == {CONF_RING_NOTIFY: [PERSON_A, PERSON_B], CONF_RING_SOURCE: None}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RING_NOTIFY: [PERSON_A]}
    )
    (field,) = result["data_schema"].schema
    assert field.default() == []
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert entry.options[CONF_RING_NOTIFY] == [{"person": PERSON_A, "only_home": False}]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "notify"}
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_RING_NOTIFY not in entry.options


async def test_options_flow_needs_a_ring_signal_without_bell_sensor(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    device_id = await discover_panel(hass)
    _person(hass, PERSON_A, "Phone A", "home")
    entry = await _entry(hass, device_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "notify"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RING_NOTIFY: [PERSON_A]}
    )
    assert result["errors"] == {CONF_RING_SOURCE: "ring_source_required"}
    hass.states.async_set("binary_sensor.knx_bell", "off")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_RING_NOTIFY: [PERSON_A], CONF_RING_SOURCE: "binary_sensor.knx_bell"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"only_home": [PERSON_A]}
    )
    assert entry.options[CONF_RING_SOURCE] == "binary_sensor.knx_bell"
    assert entry.options[CONF_RING_NOTIFY] == [{"person": PERSON_A, "only_home": True}]
