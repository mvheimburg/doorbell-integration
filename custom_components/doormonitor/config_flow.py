"""Config and options flow: pick the panel's MQTT device, then link its doors and gate."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import UNREACHABLE, PanelApi, PanelApiError, api_path, normalize_url
from .const import (
    CONF_ADMIN_PIN,
    CONF_API_ACTOR,
    CONF_API_ACTOR_NAME,
    CONF_API_TOKEN,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_LINKS,
    DOMAIN,
    MQTT_DOMAIN,
)
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
    """Link the doors and gate, or set up the admin connection to the panel API."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["links", "admin"])

    async def async_step_links(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change which real entities the panel's doors and gate are linked to."""
        panel_entities = panel_entity_ids(self.hass, self.config_entry.data[CONF_DEVICE_ID])
        if not panel_entities:
            return self.async_abort(reason="no_panel_entities")
        if user_input is not None:
            return self.async_create_entry(
                data={
                    **self.config_entry.options,
                    CONF_LINKS: _links_from_input(panel_entities, user_input),
                }
            )
        return self.async_show_form(
            step_id="links",
            data_schema=_links_schema(
                panel_entities, self.config_entry.options.get(CONF_LINKS) or {}
            ),
            description_placeholders={"device": self.config_entry.title},
        )

    async def async_step_admin(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Where the panel API is, its token, and the doorbell admin to act as.

        The PIN is only used to look the admin up (``POST /session``); the admin's id is stored,
        never the PIN. Left empty, the PIN keeps the admin chosen before. An empty URL removes the
        connection.
        """
        options = self.config_entry.options
        errors: dict[str, str] = {}
        placeholders = {"actor": options.get(CONF_API_ACTOR_NAME) or "–"}
        if user_input is not None:
            url = normalize_url(user_input.get(CONF_API_URL) or "")
            if not url:
                return self.async_create_entry(data={CONF_LINKS: options.get(CONF_LINKS) or {}})
            token = user_input.get(CONF_API_TOKEN) or options.get(CONF_API_TOKEN) or ""
            pin = (user_input.get(CONF_ADMIN_PIN) or "").strip()
            actor = options.get(CONF_API_ACTOR)
            if not token:
                errors[CONF_API_TOKEN] = "token_required"
            elif not pin and not actor:
                errors[CONF_ADMIN_PIN] = "pin_required"
            else:
                api = PanelApi(async_get_clientsession(self.hass), url, token, actor)
                try:
                    await api.info()
                    if pin:
                        admin = await api.session(pin)
                        actor, actor_name = admin["id"], admin.get("name") or ""
                    else:
                        # Still an active admin? Any actor route tells.
                        actor_name = (await api.request("GET", api_path(["users", actor])))[
                            "name"
                        ]
                except PanelApiError as err:
                    errors["base"] = _admin_error(err)
                    placeholders["detail"] = err.message
                else:
                    return self.async_create_entry(
                        data={
                            **options,
                            CONF_API_URL: url,
                            CONF_API_TOKEN: token,
                            CONF_API_ACTOR: actor,
                            CONF_API_ACTOR_NAME: actor_name,
                        }
                    )
        placeholders.setdefault("detail", "")
        suggested_url = (user_input or {}).get(CONF_API_URL, options.get(CONF_API_URL))
        schema = vol.Schema(
            {
                vol.Optional(CONF_API_URL, description={"suggested_value": suggested_url}): (
                    TextSelector(TextSelectorConfig(type=TextSelectorType.URL))
                ),
                vol.Optional(CONF_API_TOKEN): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional(CONF_ADMIN_PIN): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(
            step_id="admin",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )


def _admin_error(err: PanelApiError) -> str:
    """The options form error key for a panel API failure."""
    if err.code == UNREACHABLE:
        return "cannot_connect"
    if err.code == "bad-token":
        return "invalid_token"
    if err.code == "wrong-pin":
        return "invalid_pin"
    if err.code == "too-many-attempts":
        return "too_many_attempts"
    if err.code == "not-admin" or err.status == 404:
        return "actor_gone"
    return "unknown"
