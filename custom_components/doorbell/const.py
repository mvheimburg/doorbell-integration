"""Constants for the Doorbell integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "doorbell"

# -- config entry keys ---------------------------------------------------------
#: Device registry id of the panel device the MQTT integration discovered.
CONF_DEVICE_ID: Final = "device_id"
#: Mapping ``panel entity_id -> real entity_id`` (options).
CONF_LINKS: Final = "links"

#: Panel entity domains that can be linked to a real entity of the same domain.
LINKABLE_DOMAINS: Final = ("lock", "cover")

# -- sync timing ---------------------------------------------------------------
#: Seconds during which a panel state we pushed ourselves is recognised as its echo.
ECHO_WINDOW_S: Final = 10.0
#: Seconds after the panel comes online during which its state changes are start-up noise.
PANEL_BOOT_GRACE_S: Final = 5.0
#: Seconds after a panel request before the panel is corrected if the real entity did not follow.
REQUEST_TIMEOUT_S: Final = 30.0
