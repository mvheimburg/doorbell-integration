# Doorbell — Home Assistant integration for the DoorMonitor panel

A custom integration that represents a [DoorMonitor](https://github.com/mvheimburg/door_monitor)
wall panel (the `dxbell` Rust/Dioxus kiosk) as a single Home Assistant device. It talks to the
panel over the MQTT broker Home Assistant is already connected to.

Everything the panel publishes becomes an entity, everything the panel accepts becomes a
control, and every user action on the panel becomes an event you can automate on.

## What you get

One device with these entities (entity ids assume the default name "Doorbell"):

| Entity                              | Type          | Source / effect |
|-------------------------------------|---------------|-----------------|
| `event.doorbell_ring`               | event (doorbell) | `{base}/device_trigger/bell` = `pressed` |
| `binary_sensor.doorbell_bell_pressed` | binary sensor | `{base}/binary_sensor/bell_pressed/state` (1.5 s pulse) |
| `binary_sensor.doorbell_connectivity` | connectivity | `{base}/availability` (LWT) |
| `sensor.doorbell_last_ring`         | timestamp     | `{base}/sensor/last_ring/state` |
| `sensor.doorbell_logged_in_user`    | sensor        | `{base}/sensor/logged_in_user/state` |
| `sensor.doorbell_login_method`      | enum (none/code/ble) | `{base}/sensor/login_method/state` |
| `sensor.doorbell_active_page`       | enum (home/control/admin) | `{base}/sensor/active_page/state` |
| `select.doorbell_party_mode`        | select        | state from `select/partymode/state`, choosing publishes to `select/partymode/command` |
| `select.doorbell_house_state`       | select        | same for `select/house_state` |
| `lock.doorbell_<door>` (one per door) | lock        | state from `lock/<door>/state`, lock/unlock publishes `LOCK`/`UNLOCK` to `lock/<door>/command` |
| `cover.doorbell_gate`               | cover (gate)  | state from `cover/gate/state`, open/close/stop publishes to `cover/gate/command` |

All entities become unavailable when the panel's availability topic says `offline`.

### Events on the bus

| Event                   | When                                   | Data |
|-------------------------|----------------------------------------|------|
| `doorbell_ring`         | bell pressed                            | `device_id`, `entry_id`, `name`, `topic`, `timestamp` |
| `doorbell_login`        | someone logged in on the panel          | `user`, `method`, `page` |
| `doorbell_logout`       | panel returned to the home screen       | `page` |
| `doorbell_lock_request` | lock/unlock pressed on the panel        | `door`, `action`, `entity_id` (mapped real lock or null) |
| `doorbell_gate_request` | open/close/stop pressed on the panel    | `gate`, `action`, `entity_id` |

The same five show up as **device triggers** in the automation editor ("Doorbell rang", …).

### Services

| Service                          | Fields |
|----------------------------------|--------|
| `doorbell.set_party_mode`        | `mode`: normal / halloween / christmas / easter / birthday |
| `doorbell.set_house_state`       | `state`: home / away / vacation |
| `doorbell.purge_mqtt_discovery`  | – (see below) |

Each takes an optional `device_id` when more than one panel is configured.

## Mapping panel doors to real locks and the gate

The panel shows doors and a gate but has no hardware of its own. In the integration
**options** you can map each panel door to a real `lock.*` entity and the gate to a real
`cover.*` entity. With a mapping in place:

- A press on the panel (`doorbell_lock_request` / `doorbell_gate_request`) calls the real
  entity's service.
- Locking `lock.doorbell_front` in Home Assistant publishes the command to the panel **and**
  locks the real lock.
- When the real lock or gate changes state, the integration pushes the settled state
  (`locked`/`unlocked`, `open`/`closed`) to the panel so the display stays truthful.
  Transitional states (`locking`, `opening`, …) are ignored until they settle.

Commands the integration publishes itself are recognised when the broker echoes them back
and are not reported as panel requests, so there are no feedback loops.

Without a mapping the entities still work: they mirror the panel and let you write your own
automations from the events.

## Installation

### HACS

Add this repository as a custom repository (category *Integration*), install **Doorbell**,
restart Home Assistant.

### Manual

Copy `custom_components/doorbell` into `<config>/custom_components/` and restart.

## Setup

*Settings → Devices & services → Add integration → Doorbell.*

| Field                  | Meaning |
|------------------------|---------|
| Name                   | Device name; entity ids derive from it. |
| MQTT base topic        | `mqtt.base_topic` in the panel's `config.json` (default `doorbell`). |
| MQTT discovery prefix  | `mqtt.discovery_prefix` in the panel config; only used by the purge service. |
| Door ids               | The `[[doors]]` ids from the panel config, comma separated. |
| Gate id                | The `[gate]` id from the panel config. |

Then open **Configure** on the integration to map doors and the gate to real entities.
Changing doors adds/removes the corresponding lock entities.

### Avoiding duplicate entities

The panel also announces itself through MQTT discovery, so the MQTT integration will create
its own copies of these entities. Once this integration is set up, call
`doorbell.purge_mqtt_discovery` to delete the retained discovery configs, and turn discovery off
on the panel (or leave it; the purge service can be run again after the panel reconnects).

## Chime hardware

Ringing a physical bell over KNX (or a relay, webhook, or speaker) is done by the separate
[doorbell-bridge](https://github.com/mvheimburg/doorbell-bridge) container, which needs no Home
Assistant. If you prefer to do it in Home Assistant, an automation on the `Doorbell rang`
device trigger does the same job.

## Development

```sh
uv sync                 # installs pytest-homeassistant-custom-component
uv run pytest -q
uv run ruff check .
```

Tests run against a real Home Assistant core with the MQTT integration's test broker; no
external services are needed.

## Wire protocol

Topic layout is `{base_topic}/component/id/role` as implemented by `doorbell-core` and pinned by
its `mqtt_parity.rs` tests. The legacy Python/Qt panel uses `ha-mqtt-discoverable` topics
(`hmd/...`) and is not supported by this integration.
