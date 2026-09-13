"""MQTT topic layout of the DoorMonitor panel (``{base_topic}/component/id/role``)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Topics:
    base: str

    # -- panel → HA ----------------------------------------------------------
    @property
    def wildcard(self) -> str:
        return f"{self.base}/#"

    @property
    def availability(self) -> str:
        return f"{self.base}/availability"

    @property
    def ring(self) -> str:
        return f"{self.base}/device_trigger/bell"

    @property
    def bell_pressed(self) -> str:
        return f"{self.base}/binary_sensor/bell_pressed/state"

    @property
    def last_ring(self) -> str:
        return f"{self.base}/sensor/last_ring/state"

    @property
    def logged_in_user(self) -> str:
        return f"{self.base}/sensor/logged_in_user/state"

    @property
    def login_method(self) -> str:
        return f"{self.base}/sensor/login_method/state"

    @property
    def active_page(self) -> str:
        return f"{self.base}/sensor/active_page/state"

    @property
    def party_mode_state(self) -> str:
        return f"{self.base}/select/partymode/state"

    @property
    def house_state_state(self) -> str:
        return f"{self.base}/select/house_state/state"

    def lock_state(self, door_id: str) -> str:
        return f"{self.base}/lock/{door_id}/state"

    def cover_state(self, gate_id: str) -> str:
        return f"{self.base}/cover/{gate_id}/state"

    # -- HA → panel (and panel → HA when a user presses on the panel) --------
    @property
    def party_mode_command(self) -> str:
        return f"{self.base}/select/partymode/command"

    @property
    def house_state_command(self) -> str:
        return f"{self.base}/select/house_state/command"

    def lock_command(self, door_id: str) -> str:
        return f"{self.base}/lock/{door_id}/command"

    def cover_command(self, gate_id: str) -> str:
        return f"{self.base}/cover/{gate_id}/command"

    # -- parsing -------------------------------------------------------------
    def relative(self, topic: str) -> list[str] | None:
        """Split ``topic`` below ``base`` into segments, or ``None`` if outside."""
        prefix = f"{self.base}/"
        if not topic.startswith(prefix):
            return None
        return topic[len(prefix) :].split("/")


def discovery_config_topics(
    prefix: str, client_id: str, doors: list[str], gate_id: str
) -> list[str]:
    """Retained discovery topics the panel publishes; used by ``purge_mqtt_discovery``."""
    topics = [
        f"{prefix}/device_trigger/{client_id}/config",
        f"{prefix}/sensor/last_ring/config",
        f"{prefix}/binary_sensor/bell_pressed/config",
        f"{prefix}/sensor/logged_in_user/config",
        f"{prefix}/sensor/login_method/config",
        f"{prefix}/sensor/active_page/config",
        f"{prefix}/cover/{gate_id}/config",
        f"{prefix}/select/partymode/config",
        f"{prefix}/select/house_state/config",
    ]
    topics.extend(f"{prefix}/lock/{door}/config" for door in doors)
    return topics
