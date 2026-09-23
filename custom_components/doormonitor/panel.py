"""The doorbell admin panel: a sidebar page served by the integration, for administrators."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

from .const import DOMAIN

URL_PATH = "doormonitor"
ELEMENT = "doormonitor-admin-panel"
STATIC_URL = "/doormonitor_static"
BUNDLE = Path(__file__).parent / "frontend" / "doormonitor-admin-panel.js"
_STATIC = (DOMAIN, "panel_static")
_PANEL = (DOMAIN, "panel")


def _version() -> str:
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    return manifest["version"]


async def async_register(hass: HomeAssistant) -> None:
    """Serve the bundle once and show the panel while an entry is set up."""
    if hass.data.get(_PANEL):
        return
    if not hass.data.get(_STATIC) and hass.http is not None:
        from homeassistant.components.http import StaticPathConfig

        # Versioned URL, so an update is never served from the browser cache.
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(BUNDLE.parent), cache_headers=True)]
        )
        hass.data[_STATIC] = True
    version = await hass.async_add_executor_job(_version)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=URL_PATH,
        webcomponent_name=ELEMENT,
        # Static metadata without a language context, like a card picker entry.
        sidebar_title="Doorbell",
        sidebar_icon="mdi:doorbell-video",
        module_url=f"{STATIC_URL}/{BUNDLE.name}?v={version}",
        require_admin=True,
        config={},
    )
    hass.data[_PANEL] = True


def async_unregister(hass: HomeAssistant) -> None:
    """Remove the panel when the last entry is unloaded."""
    if hass.data.pop(_PANEL, False):
        frontend.async_remove_panel(hass, URL_PATH)
