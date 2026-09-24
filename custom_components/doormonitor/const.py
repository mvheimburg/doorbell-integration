"""Constants for the DoorMonitor integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "doormonitor"
#: The integration that discovers the panel and owns its entities.
MQTT_DOMAIN: Final = "mqtt"

# -- config entry keys ---------------------------------------------------------
#: Device registry id of the panel device the MQTT integration discovered.
CONF_DEVICE_ID: Final = "device_id"
#: Mapping ``panel entity_id -> real entity_id`` (options).
CONF_LINKS: Final = "links"

#: Base URL of the panel API, e.g. ``http://doorbell-panel:8081`` (options).
CONF_API_URL: Final = "api_url"
#: The panel's ``DOORBELL_API_TOKEN`` (options).
CONF_API_TOKEN: Final = "api_token"
#: User id of the doorbell admin the integration acts as (options); obtained from an admin PIN.
CONF_API_ACTOR: Final = "api_actor"
#: That admin's name when it was chosen, for display (options).
CONF_API_ACTOR_NAME: Final = "api_actor_name"
#: How the panel's certificate is checked: ``system``, ``fingerprint`` or ``disabled`` (options).
CONF_API_VERIFY: Final = "api_verify"
#: SHA-256 fingerprint of the panel's certificate, 64 lower-case hex digits (options, pinning only).
CONF_API_FINGERPRINT: Final = "api_fingerprint"
#: Only used in the options form; never stored.
CONF_ADMIN_PIN: Final = "admin_pin"

#: Panel entity domains that can be linked to a real entity of the same domain.
LINKABLE_DOMAINS: Final = ("lock", "cover")

# -- sync timing ---------------------------------------------------------------
#: Seconds during which a panel state we pushed ourselves is recognised as its echo.
ECHO_WINDOW_S: Final = 10.0
#: Seconds after the panel comes online during which its state changes are start-up noise.
PANEL_BOOT_GRACE_S: Final = 5.0
#: Seconds after a panel request before the panel is corrected if the real entity did not follow.
REQUEST_TIMEOUT_S: Final = 30.0
