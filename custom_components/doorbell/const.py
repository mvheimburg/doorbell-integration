"""Constants for the Doorbell integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "doorbell"

MANUFACTURER: Final = "Martin von Heimburg"
MODEL: Final = "DoorMonitor panel"

# -- config entry keys ---------------------------------------------------------
CONF_NAME: Final = "name"
CONF_BASE_TOPIC: Final = "base_topic"
CONF_DISCOVERY_PREFIX: Final = "discovery_prefix"
CONF_DOORS: Final = "doors"
CONF_GATE_ID: Final = "gate_id"
#: Mapping ``door_id -> lock entity_id`` for real locks that follow the panel.
CONF_LOCK_MAP: Final = "lock_map"
#: Real cover entity that follows the panel's gate.
CONF_GATE_ENTITY: Final = "gate_entity"

DEFAULT_NAME: Final = "Doorbell"
DEFAULT_BASE_TOPIC: Final = "doorbell"
DEFAULT_DISCOVERY_PREFIX: Final = "homeassistant"
DEFAULT_DOORS: Final = ["front", "workshop", "garage"]
DEFAULT_GATE_ID: Final = "gate"

# -- wire vocabulary (must match dxbell doorbell-core / mqtt_parity.rs) --------
PAYLOAD_RING: Final = "pressed"
PAYLOAD_ON: Final = "ON"
PAYLOAD_OFF: Final = "OFF"
PAYLOAD_ONLINE: Final = "online"
PAYLOAD_OFFLINE: Final = "offline"
PAYLOAD_LOCK: Final = "LOCK"
PAYLOAD_UNLOCK: Final = "UNLOCK"
PAYLOAD_OPEN: Final = "OPEN"
PAYLOAD_CLOSE: Final = "CLOSE"
PAYLOAD_STOP: Final = "STOP"

PARTY_MODES: Final = ["normal", "halloween", "christmas", "easter", "birthday"]
HOUSE_STATES: Final = ["home", "away", "vacation"]
LOGIN_METHODS: Final = ["none", "code", "ble"]
ACTIVE_PAGES: Final = ["home", "control", "admin"]

LOCK_STATES: Final = ["locked", "unlocked", "locking", "unlocking", "jammed", "unknown"]
COVER_STATES: Final = ["open", "opening", "closed", "closing", "stopped", "unknown"]

# -- events fired on the Home Assistant bus ------------------------------------
EVENT_RING: Final = f"{DOMAIN}_ring"
EVENT_LOCK_REQUEST: Final = f"{DOMAIN}_lock_request"
EVENT_GATE_REQUEST: Final = f"{DOMAIN}_gate_request"
EVENT_LOGIN: Final = f"{DOMAIN}_login"
EVENT_LOGOUT: Final = f"{DOMAIN}_logout"

# -- services ------------------------------------------------------------------
SERVICE_SET_PARTY_MODE: Final = "set_party_mode"
SERVICE_SET_HOUSE_STATE: Final = "set_house_state"
SERVICE_PURGE_MQTT_DISCOVERY: Final = "purge_mqtt_discovery"
ATTR_MODE: Final = "mode"
ATTR_STATE: Final = "state"
ATTR_DEVICE_ID: Final = "device_id"

#: Seconds during which a command we published ourselves is recognised as an echo.
OWN_COMMAND_WINDOW_S: Final = 3.0
