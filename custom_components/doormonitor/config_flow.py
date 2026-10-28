"""Config and options flow: pick the panel's MQTT device, then link its doors, gate and modes."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    ObjectSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    FINGERPRINT_MISMATCH,
    FORBIDDEN,
    REDIRECT,
    TLS_FAILED,
    UNAUTHORIZED,
    UNREACHABLE,
    VERIFY_FINGERPRINT,
    VERIFY_MODES,
    VERIFY_SYSTEM,
    PanelApi,
    PanelApiError,
    api_path,
    normalize_fingerprint,
    normalize_url,
    ssl_setting,
    url_problem,
)
from .const import (
    CONF_ADMIN_PIN,
    CONF_API_ACTOR,
    CONF_API_ACTOR_NAME,
    CONF_API_FINGERPRINT,
    CONF_API_TOKEN,
    CONF_API_URL,
    CONF_API_VERIFY,
    CONF_DEVICE_ID,
    CONF_HOUSE_AXES,
    CONF_HOUSE_STATE,
    CONF_LINKS,
    CONF_MODE_LINKS,
    CONF_OVERLAY_MAP,
    CONF_RING_NOTIFY,
    CONF_RING_SOURCE,
    DOMAIN,
    MODE_AXES,
    MODE_SOURCE_DOMAINS,
    MQTT_DOMAIN,
    RING_ONLY_HOME,
    RING_PERSON,
    RING_SOURCE_DOMAINS,
)
from .modes import panel_mode_entities
from .ring import panel_bell_entity
from .sync import panel_entity_ids

#: The admin connection's options, dropped together when the connection is removed.
_ADMIN_KEYS = (
    CONF_API_URL,
    CONF_API_VERIFY,
    CONF_API_FINGERPRINT,
    CONF_API_TOKEN,
    CONF_API_ACTOR,
    CONF_API_ACTOR_NAME,
)


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


def _modes_schema(axes: list[str], links: dict[str, dict[str, str]]) -> vol.Schema:
    """One section per mode select on the panel, with a source picker per option but the first."""
    source = EntitySelector(EntitySelectorConfig(domain=list(MODE_SOURCE_DOMAINS)))
    return vol.Schema(
        {
            vol.Required(axis): section(
                vol.Schema(
                    {
                        vol.Optional(
                            option,
                            description={"suggested_value": (links.get(axis) or {}).get(option)},
                        ): source
                        for option in MODE_AXES[axis][1][1:]
                    }
                )
            )
            for axis in axes
        }
    )


def _modes_from_input(axes: list[str], user_input: dict[str, Any]) -> dict[str, dict[str, str]]:
    links = {
        axis: {option: source for option, source in (user_input.get(axis) or {}).items() if source}
        for axis in axes
    }
    return {axis: sources for axis, sources in links.items() if sources}


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
    """Link the doors and gate, choose who is notified of a ring, or set up the admin connection."""

    def __init__(self) -> None:
        self._people: list[str] = []
        self._ring_source: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["links", "modes", "house_state", "notify", "admin"]
        )

    async def async_step_notify(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose who gets a phone notification when the bell rings."""
        options = self.config_entry.options
        bell = panel_bell_entity(self.hass, self.config_entry.data[CONF_DEVICE_ID])
        errors: dict[str, str] = {}
        if user_input is not None:
            self._people = list(dict.fromkeys(user_input.get(CONF_RING_NOTIFY) or []))
            self._ring_source = user_input.get(CONF_RING_SOURCE) or None
            if self._people and not (self._ring_source or bell):
                errors[CONF_RING_SOURCE] = "ring_source_required"
            elif self._people:
                return await self.async_step_notify_home()
            else:
                return self._save_notify([])
            shown = user_input
        else:
            shown = {
                CONF_RING_NOTIFY: [p[RING_PERSON] for p in options.get(CONF_RING_NOTIFY) or []],
                CONF_RING_SOURCE: options.get(CONF_RING_SOURCE),
            }
        return self.async_show_form(
            step_id="notify",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_RING_NOTIFY,
                        description={"suggested_value": shown.get(CONF_RING_NOTIFY)},
                    ): EntitySelector(EntitySelectorConfig(domain="person", multiple=True)),
                    vol.Optional(
                        CONF_RING_SOURCE,
                        description={"suggested_value": shown.get(CONF_RING_SOURCE)},
                    ): EntitySelector(EntitySelectorConfig(domain=list(RING_SOURCE_DOMAINS))),
                }
            ),
            description_placeholders={"bell": bell or "–"},
        )

    async def async_step_notify_home(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """One checkbox per chosen person: notify them only while they are home."""
        if user_input is not None:
            only_home = set(user_input.get(RING_ONLY_HOME) or [])
            return self._save_notify(
                [
                    {RING_PERSON: person, RING_ONLY_HOME: person in only_home}
                    for person in self._people
                ]
            )
        before = {
            p[RING_PERSON]
            for p in self.config_entry.options.get(CONF_RING_NOTIFY) or []
            if p.get(RING_ONLY_HOME)
        }
        choices = [
            SelectOptionDict(value=person, label=_person_name(self.hass, person))
            for person in self._people
        ]
        return self.async_show_form(
            step_id="notify_home",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        RING_ONLY_HOME, default=[p for p in self._people if p in before]
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=choices, multiple=True, mode=SelectSelectorMode.LIST
                        )
                    )
                }
            ),
        )

    def _save_notify(self, people: list[dict[str, Any]]) -> ConfigFlowResult:
        data = {
            key: value
            for key, value in self.config_entry.options.items()
            if key not in (CONF_RING_NOTIFY, CONF_RING_SOURCE)
        }
        if people:
            data[CONF_RING_NOTIFY] = people
            if self._ring_source:
                data[CONF_RING_SOURCE] = self._ring_source
        return self.async_create_entry(data=data)

    async def async_step_house_state(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose a hub and the axes it controls instead of legacy mode links."""
        options = self.config_entry.options
        errors = {}
        axes = list(panel_mode_entities(self.hass, self.config_entry.data[CONF_DEVICE_ID]))
        if not axes:
            return self.async_abort(reason="no_mode_entities")
        if user_input is not None:
            mapping = user_input.get(CONF_OVERLAY_MAP) or {}
            if not isinstance(mapping, dict) or any(
                not isinstance(key, str) or value not in MODE_AXES["party_mode"][1]
                for key, value in mapping.items()
            ):
                errors[CONF_OVERLAY_MAP] = "invalid_overlay_map"
            else:
                return self.async_create_entry(
                    data={
                        **options,
                        CONF_HOUSE_STATE: user_input.get(CONF_HOUSE_STATE),
                        CONF_HOUSE_AXES: user_input.get(CONF_HOUSE_AXES, []),
                        CONF_OVERLAY_MAP: mapping,
                    }
                )
        shown = user_input if user_input is not None else options
        return self.async_show_form(
            step_id="house_state",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HOUSE_STATE,
                        description={
                            "suggested_value": shown.get(CONF_HOUSE_STATE),
                        },
                    ): EntitySelector(
                        EntitySelectorConfig(domain="sensor", integration="house_state")
                    ),
                    vol.Required(
                        CONF_HOUSE_AXES, default=shown.get(CONF_HOUSE_AXES, axes)
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=axes, multiple=True, translation_key=CONF_HOUSE_AXES
                        )
                    ),
                    vol.Optional(
                        CONF_OVERLAY_MAP, default=shown.get(CONF_OVERLAY_MAP) or {}
                    ): ObjectSelector(),
                }
            ),
        )

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

    async def async_step_modes(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose which entities switch the panel's party mode and house state."""
        axes = list(panel_mode_entities(self.hass, self.config_entry.data[CONF_DEVICE_ID]))
        if not axes:
            return self.async_abort(reason="no_mode_entities")
        if user_input is not None:
            return self.async_create_entry(
                data={
                    **self.config_entry.options,
                    CONF_MODE_LINKS: _modes_from_input(axes, user_input),
                }
            )
        return self.async_show_form(
            step_id="modes",
            data_schema=_modes_schema(axes, self.config_entry.options.get(CONF_MODE_LINKS) or {}),
            description_placeholders={"device": self.config_entry.title},
        )

    async def async_step_admin(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """The panel API's address, certificate check and token, and the admin to act as.

        The PIN is only used to look the admin up (``POST /session``); the admin's id is stored,
        never the PIN. Left empty, the PIN keeps the admin chosen before. An empty URL removes the
        connection. Nothing is saved until the panel accepted the connection as entered.
        """
        options = self.config_entry.options
        errors: dict[str, str] = {}
        placeholders = {"actor": options.get(CONF_API_ACTOR_NAME) or "–"}
        if user_input is not None:
            url = normalize_url(user_input.get(CONF_API_URL) or "")
            if not url:
                return self.async_create_entry(
                    data={key: value for key, value in options.items() if key not in _ADMIN_KEYS}
                )
            verify = user_input.get(CONF_API_VERIFY) or VERIFY_SYSTEM
            fingerprint = normalize_fingerprint(user_input.get(CONF_API_FINGERPRINT) or "")
            token = user_input.get(CONF_API_TOKEN) or options.get(CONF_API_TOKEN) or ""
            pin = (user_input.get(CONF_ADMIN_PIN) or "").strip()
            actor = options.get(CONF_API_ACTOR)
            if problem := url_problem(url):
                errors[CONF_API_URL] = problem
            elif verify == VERIFY_FINGERPRINT and fingerprint is None:
                errors[CONF_API_FINGERPRINT] = "invalid_fingerprint"
            elif verify == VERIFY_FINGERPRINT and not url.lower().startswith("https://"):
                errors[CONF_API_URL] = "https_required"
            elif not token:
                errors[CONF_API_TOKEN] = "token_required"
            elif not pin and not actor:
                errors[CONF_ADMIN_PIN] = "pin_required"
            else:
                api = PanelApi(
                    async_get_clientsession(self.hass),
                    url,
                    token,
                    actor,
                    ssl=ssl_setting(verify, fingerprint),
                )
                try:
                    await api.info()
                    if pin:
                        admin = await api.session(pin)
                        actor, actor_name = admin["id"], admin.get("name") or ""
                    else:
                        # Still an active admin? Any actor route tells.
                        actor_name = (await api.request("GET", api_path(["users", actor])))["name"]
                except PanelApiError as err:
                    errors["base"] = _admin_error(err)
                    placeholders["detail"] = err.message
                else:
                    data = {
                        key: value
                        for key, value in options.items()
                        if key not in (CONF_API_VERIFY, CONF_API_FINGERPRINT)
                    }
                    data |= {
                        CONF_API_URL: url,
                        CONF_API_VERIFY: verify,
                        CONF_API_TOKEN: token,
                        CONF_API_ACTOR: actor,
                        CONF_API_ACTOR_NAME: actor_name,
                    }
                    if verify == VERIFY_FINGERPRINT:
                        data[CONF_API_FINGERPRINT] = fingerprint
                    return self.async_create_entry(data=data)
        placeholders.setdefault("detail", "")
        shown = user_input or options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_API_URL, description={"suggested_value": shown.get(CONF_API_URL)}
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
                vol.Required(
                    CONF_API_VERIFY, default=shown.get(CONF_API_VERIFY) or VERIFY_SYSTEM
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(VERIFY_MODES),
                        mode=SelectSelectorMode.LIST,
                        translation_key=CONF_API_VERIFY,
                    )
                ),
                vol.Optional(
                    CONF_API_FINGERPRINT,
                    description={"suggested_value": shown.get(CONF_API_FINGERPRINT)},
                ): TextSelector(),
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


def _person_name(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    return state.name if state is not None else entity_id


def _admin_error(err: PanelApiError) -> str:
    """The options form error key for a panel API failure."""
    if err.code == UNREACHABLE:
        return "cannot_connect"
    if err.code == TLS_FAILED:
        return "tls_failed"
    if err.code == FINGERPRINT_MISMATCH:
        return "fingerprint_mismatch"
    if err.code == REDIRECT:
        return "redirect"
    if err.code in ("bad-token", UNAUTHORIZED):
        return "invalid_token"
    if err.code == "wrong-pin":
        return "invalid_pin"
    if err.code == "too-many-attempts":
        return "too_many_attempts"
    if err.code == "not-admin" or err.status == 404:
        return "actor_gone"
    if err.code == FORBIDDEN or err.status == 403:
        return "forbidden"
    return "unknown"
