"""Config and options flow for the Doorbell integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_BASE_TOPIC,
    CONF_DISCOVERY_PREFIX,
    CONF_DOORS,
    CONF_GATE_ENTITY,
    CONF_GATE_ID,
    CONF_LOCK_MAP,
    CONF_NAME,
    DEFAULT_BASE_TOPIC,
    DEFAULT_DISCOVERY_PREFIX,
    DEFAULT_DOORS,
    DEFAULT_GATE_ID,
    DEFAULT_NAME,
    DOMAIN,
)

_LOCK_PREFIX = "lock_"


def parse_doors(value: str | list[str]) -> list[str]:
    """Normalise a comma separated string (or list) of door ids."""
    items = value if isinstance(value, list) else value.split(",")
    doors: list[str] = []
    for item in items:
        door = item.strip().lower().replace(" ", "_")
        if door and door not in doors:
            doors.append(door)
    return doors


def _base_schema(defaults: dict[str, Any]) -> dict[Any, Any]:
    return {
        vol.Required(
            CONF_BASE_TOPIC, default=defaults.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)
        ): str,
        vol.Required(
            CONF_DISCOVERY_PREFIX,
            default=defaults.get(CONF_DISCOVERY_PREFIX, DEFAULT_DISCOVERY_PREFIX),
        ): str,
        vol.Required(
            CONF_DOORS, default=", ".join(defaults.get(CONF_DOORS) or DEFAULT_DOORS)
        ): TextSelector(TextSelectorConfig()),
        vol.Required(CONF_GATE_ID, default=defaults.get(CONF_GATE_ID, DEFAULT_GATE_ID)): str,
    }


def _validate_base(user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    errors: dict[str, str] = {}
    base_topic = user_input[CONF_BASE_TOPIC].strip().strip("/")
    prefix = user_input[CONF_DISCOVERY_PREFIX].strip().strip("/")
    doors = parse_doors(user_input[CONF_DOORS])
    gate_id = user_input[CONF_GATE_ID].strip().lower().replace(" ", "_")

    if not base_topic or "#" in base_topic or "+" in base_topic:
        errors[CONF_BASE_TOPIC] = "invalid_topic"
    if not prefix:
        errors[CONF_DISCOVERY_PREFIX] = "invalid_topic"
    if not doors:
        errors[CONF_DOORS] = "no_doors"
    if not gate_id:
        errors[CONF_GATE_ID] = "invalid_id"

    data = {
        CONF_BASE_TOPIC: base_topic,
        CONF_DISCOVERY_PREFIX: prefix,
        CONF_DOORS: doors,
        CONF_GATE_ID: gate_id,
    }
    return data, errors


class DoorbellConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            data, errors = _validate_base(user_input)
            name = user_input[CONF_NAME].strip() or DEFAULT_NAME
            if not errors and not await mqtt.async_wait_for_mqtt_client(self.hass):
                return self.async_abort(reason="mqtt_not_configured")
            if not errors:
                await self.async_set_unique_id(data[CONF_BASE_TOPIC])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data={CONF_NAME: name, **data})

        defaults = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
                **_base_schema(defaults),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DoorbellOptionsFlow()


class DoorbellOptionsFlow(OptionsFlow):
    """Edit topics/doors and map panel doors and gate to real entities."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current: dict[str, Any] = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            data, errors = _validate_base(user_input)
            if not errors:
                lock_map = {
                    key[len(_LOCK_PREFIX) :]: value
                    for key, value in user_input.items()
                    if key.startswith(_LOCK_PREFIX) and value
                }
                options = {
                    **data,
                    CONF_LOCK_MAP: {d: e for d, e in lock_map.items() if d in data[CONF_DOORS]},
                    CONF_GATE_ENTITY: user_input.get(CONF_GATE_ENTITY) or None,
                }
                return self.async_create_entry(title="", data=options)
            current = {**current, **user_input}

        doors = parse_doors(current.get(CONF_DOORS) or DEFAULT_DOORS)
        lock_map: dict[str, str] = current.get(CONF_LOCK_MAP) or {}
        schema: dict[Any, Any] = _base_schema(current)
        for door in doors:
            schema[
                vol.Optional(
                    f"{_LOCK_PREFIX}{door}",
                    description={"suggested_value": lock_map.get(door)},
                )
            ] = EntitySelector(EntitySelectorConfig(domain="lock"))
        schema[
            vol.Optional(
                CONF_GATE_ENTITY,
                description={"suggested_value": current.get(CONF_GATE_ENTITY)},
            )
        ] = EntitySelector(EntitySelectorConfig(domain="cover"))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"doors": ", ".join(doors)},
        )
