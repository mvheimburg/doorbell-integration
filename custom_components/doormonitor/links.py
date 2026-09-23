"""Which Home Assistant user each doorbell user stands for.

The panel API has no field for this, so the integration keeps the mapping itself, per config
entry: ``doorbell user id -> Home Assistant user id``. A Home Assistant user is linked to at most
one doorbell user. Links to users that no longer exist on either side are dropped when noticed.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1


def _store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, dict[str, str]]]:
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.user_links")


class UserLinks:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = _store(hass, entry_id)
        self._links: dict[str, str] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._links = dict(data.get("links") or {})

    @property
    def links(self) -> dict[str, str]:
        return dict(self._links)

    def owner_of(self, ha_user_id: str) -> str | None:
        """The doorbell user a Home Assistant user is linked to."""
        return next((d for d, h in self._links.items() if h == ha_user_id), None)

    async def async_set(self, doorbell_id: str, ha_user_id: str | None) -> None:
        if ha_user_id:
            if self._links.get(doorbell_id) == ha_user_id:
                return
            self._links[doorbell_id] = ha_user_id
        elif self._links.pop(doorbell_id, None) is None:
            return
        await self._save()

    async def async_prune(self, doorbell_ids: set[str], ha_user_ids: set[str]) -> None:
        kept = {d: h for d, h in self._links.items() if d in doorbell_ids and h in ha_user_ids}
        if kept != self._links:
            self._links = kept
            await self._save()

    async def _save(self) -> None:
        await self._store.async_save({"links": self._links})


async def async_remove(hass: HomeAssistant, entry_id: str) -> None:
    """Forget an entry's links when the entry is deleted."""
    await _store(hass, entry_id).async_remove()
