"""Config and options flow: pick the panel's MQTT device, then link its doors and gate."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_DEVICE_ID, CONF_LINKS, DOMAIN, MQTT_DOMAIN
from .sync import panel_entity_ids


def _device_label(device: dr.DeviceEntry) -> str:
    return device.name_by_user or device.name or device.id


def _device_name(hass: HomeAssistant, device_id: str) -> str:
    device = dr.async_get(hass).async_get(device_id)
    return device_id if device is None else _device_label(device)


@callback
def _panel_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """The MQTT devices that have lock or cover entities, i.e. the ones that could be a panel.

    This is done here rather than with a ``DeviceSelector`` filter because the selector matches on
    entities that are in the state machine, so a panel that is offline or whose entities have no
    state yet drops out of the list. The registry always has them.
    """
    registry = dr.async_get(hass)
    options = [
        SelectOptionDict(value=device.id, label=_device_label(device))
        for entry in hass.config_entries.async_entries(MQTT_DOMAIN)
        for device in dr.async_entries_for_config_entry(registry, entry.entry_id)
        if not device.disabled and panel_entity_ids(hass, device.id)
    ]
    return sorted(options, key=lambda option: option["label"].casefold())


def _links_schema(panel_entities: list[str], links: dict[str, str]) -> vol.Schema:
    """One optional real-entity picker per panel lock/cover, keyed by the panel entity_id."""
    return vol.Schema(
        {
            vol.Optional(panel, description={"suggested_value": links.get(panel)}): EntitySelector(
                EntitySelectorConfig(domain=panel.split(".", 1)[0], exclude_entities=panel_entities)
            )
            for panel in panel_entities
        }
    )


def _links_from_input(panel_entities: list[str], user_input: dict[str, Any]) -> dict[str, str]:
    return {panel: user_input[panel] for panel in panel_entities if user_input.get(panel)}


class DoorMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._device_id: str = ""
        self._panel_entities: list[str] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = _panel_options(self.hass)
        if not options:
            return self.async_abort(reason="no_panels_found")

        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            panel_entities = panel_entity_ids(self.hass, device_id)
            if panel_entities:
                self._device_id = device_id
                self._panel_entities = panel_entities
                return await self.async_step_links()
            errors[CONF_DEVICE_ID] = "no_panel_entities"

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_links(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        name = _device_name(self.hass, self._device_id)
        if user_input is not None:
            return self.async_create_entry(
                title=name,
                data={CONF_DEVICE_ID: self._device_id},
                options={CONF_LINKS: _links_from_input(self._panel_entities, user_input)},
            )
        return self.async_show_form(
            step_id="links",
            data_schema=_links_schema(self._panel_entities, {}),
            description_placeholders={"device": name},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DoorMonitorOptionsFlow()


class DoorMonitorOptionsFlow(OptionsFlow):
    """Change which real entities the panel's doors and gate are linked to."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        panel_entities = panel_entity_ids(self.hass, self.config_entry.data[CONF_DEVICE_ID])
        if not panel_entities:
            return self.async_abort(reason="no_panel_entities")
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_LINKS: _links_from_input(panel_entities, user_input)}
            )
        return self.async_show_form(
            step_id="init",
            data_schema=_links_schema(
                panel_entities, self.config_entry.options.get(CONF_LINKS) or {}
            ),
            description_placeholders={"device": self.config_entry.title},
        )
