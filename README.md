# Doorbell — link a DoorMonitor panel to your real doors and gate

The [DoorMonitor](https://github.com/mvheimburg/door_monitor) wall panel (`dxbell`) announces itself
to Home Assistant through MQTT discovery: the MQTT integration creates a device with a lock per door,
a gate cover, the ring trigger, sensors and selects. Those locks and the cover only reflect what the
panel *shows*; the panel has no hardware of its own.

This integration links them to the real locks and gate in Home Assistant and keeps the two in sync:

- **Panel → real.** Pressing lock/unlock or open/close on the panel operates the real entity.
- **Real → panel.** When the real lock or gate changes, for whatever reason, the panel is told, so it
  always shows the real state.

It creates no entities of its own. Ring triggers, sensors, party mode and house state all come from
the MQTT device as they are.

## Setup

1. Make sure the panel has MQTT discovery enabled and shows up under
   *Settings → Devices & services → MQTT*.
2. *Add integration → Doorbell*, and pick the panel device.
3. For each of the panel's locks and its gate cover, pick the real `lock.*` / `cover.*` entity it
   stands for. Leave a field empty to keep that door unsynced.

Links can be changed later with **Configure** on the integration.

## How the sync works

| Event | What happens |
|-------|--------------|
| The real entity settles on a state (`locked`/`unlocked`, `open`/`closed`) the panel does not show | Lock/unlock or open/close is called on the panel entity, which sends the command to the panel. `open` on a lock counts as `unlocked`. |
| The panel entity settles on a state the real entity does not have and is not heading for | The real entity is locked/unlocked or opened/closed. This also happens when you operate the panel entity in Home Assistant. |
| The real entity has not reached the requested state 30 s later | The panel is set back to the real state. A gate that is still moving is left alone until it stops. |
| The panel comes online, or the integration starts | The panel is sent the real state of every linked entity, because it boots with every door locked. State changes during the next 5 s are treated as start-up noise, not presses. |
| The panel reports a state that was just sent to it | Treated as an echo, not a press. If the real entity has moved on meanwhile (e.g. an auto-relock), the panel is corrected. |

Moving states (`locking`, `opening`, …), `jammed`, `unknown` and `unavailable` are never pushed.
While a real entity is unavailable, presses on the panel are logged and ignored, and the panel is
corrected once the real entity reports again.

### Limitations

- **Stop on the gate is not forwarded.** The panel publishes `stopped`, but Home Assistant's MQTT
  cover turns that into `open` or `closed`, so a Stop press can't be seen from the entity state.
- The panel has no moving states for the gate. It shows the old state until the real gate has
  finished moving.

## Upgrading from 0.2

0.2 subscribed to the panel's raw MQTT topics and created a device and entities of its own.
Those config entries can't be migrated. Remove the entry, delete the leftover *Doorbell*
device if one remains, and add the integration again. If you ran the old
`doorbell.purge_mqtt_discovery` service, restart the panel so it republishes its discovery configs.

## Installation

### HACS

Add this repository as a custom repository (category *Integration*), install **Doorbell**, and
restart Home Assistant.

### Manual

Copy `custom_components/doorbell` into `<config>/custom_components/` and restart.

## Chime hardware

Ringing a physical bell over KNX (or a relay, webhook, or speaker) is done by the separate
[doorbell-bridge](https://github.com/mvheimburg/doorbell-bridge) container, which needs no Home
Assistant. To do it in Home Assistant instead, automate on the MQTT device's ring trigger.

## Development

```sh
uv sync
uv run ruff check .
uv run pytest -q
```

The tests discover a panel through the MQTT integration's test client, using the same discovery
payloads dxbell publishes, and check what reaches the panel's command topics.

## Releasing

Bump `version` in `custom_components/doorbell/manifest.json` and push to `main`. Once hassfest and
the tests pass, CI tags the commit `v<version>` and publishes a GitHub release listing the commits
since the previous tag. HACS offers that release as the update. Pushes that don't change the
version publish nothing.
