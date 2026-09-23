<img src="custom_components/doormonitor/brand/icon.png" alt="" width="96" align="right">

# DoorMonitor for Home Assistant — link the panel to your real doors and gate

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

From 0.5 it also adds a **Doorbell** page to the sidebar, where Home Assistant administrators manage
the panel's users, per-mode appearance, bell sounds and videos, and family photos. See
[Admin panel](#admin-panel).

## Setup

1. Make sure the panel has MQTT discovery enabled and shows up under
   *Settings → Devices & services → MQTT*.
2. *Add integration → DoorMonitor*, and pick the panel device.
3. For each of the panel's locks and its gate cover, pick the real `lock.*` / `cover.*` entity it
   stands for. Leave a field empty to keep that door unsynced.

Links can be changed later with **Configure → Link doors and gate** on the integration.

## Admin panel

The **Doorbell** sidebar page does what the panel's own admin app (`doorbell-admin`) does, inside
Home Assistant. It is only shown to Home Assistant administrators.

| Tab | What you do there |
|-----|-------------------|
| Users | Add, edit and delete the people who can open the door: PIN, access level (guest, resident, admin), active dates and BLE ids. A user can be linked to a Home Assistant user: pick them in the form and the name is filled in. |
| Appearance | Pick the theme and the bell sounds or videos for each house mode (home, away, vacation) and party mode. Changes are saved as you pick and show on the doorbell within a second. |
| Sounds & videos | Create, rename and delete groups of bell sounds or videos; upload, play, rename and delete their files. |
| Photos | The photos the doorbell's home screen shows in turn. |

Tabs appear only for what the panel offers (`GET /info`), so an older panel shows fewer tabs. Every
rule (PIN format and uniqueness, who may be deleted, file types and sizes) is checked by the panel,
and its messages are shown as it words them, in English. The page itself is in English and
Norwegian Bokmål, following your Home Assistant language.

### Setting up the admin connection

The page talks to the panel API (API v1) through this integration, so the API token never reaches a
browser. The panel must run with `DOORBELL_API_TOKEN` set, and Home Assistant must be able to reach
its API port (8081 by default; keep that port off the LAN).

1. **Settings → Devices & services → DoorMonitor → Configure → Admin connection.**
2. Enter the API's address (for example `http://doorbell-panel:8081`), the token, and the PIN of an
   active doorbell admin, for example root.

The integration checks the PIN once and remembers **which admin** it belongs to, not the PIN. From
then on every change is made as that admin, and the panel's admin guard applies to it: for example,
the page cannot remove that admin's own admin access. Anyone who is a Home Assistant administrator
can therefore manage the doorbell.

- Leave the token or the PIN empty to keep the stored one. Clear the address to remove the
  connection.
- If that admin is later deleted, demoted or deactivated at the doorbell, the page says so. Enter an
  admin PIN again under Configure.

### Home Assistant user links

The panel API has no field for Home Assistant users, so the integration stores the links itself, per
panel. A Home Assistant user is linked to at most one doorbell user. Links are dropped when either
user is deleted, and are removed with the integration entry. Linking changes nothing at the doorbell.

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

## Upgrading from 0.2 or 0.3

Up to 0.3 the integration's domain was `doorbell`. Home Assistant now has a built-in integration with
that domain (it provides the *Doorbell rang* trigger), which the old folder overrides. From 0.4 the
domain is `doormonitor`. After updating in HACS:

1. Remove the old *Doorbell* entry under *Settings → Devices & services*. If a *Doorbell* device
   is left over from 0.2, delete it too.
2. Delete `<config>/custom_components/doorbell` if it is still there, and restart Home Assistant.
3. Add **DoorMonitor** and link the doors and gate again.

If you ran the old `doorbell.purge_mqtt_discovery` service, restart the panel so it republishes its
discovery configs.

## Installation

### HACS

Add this repository as a custom repository (category *Integration*), install **DoorMonitor**, and
restart Home Assistant.

### Manual

Copy `custom_components/doormonitor` into `<config>/custom_components/` and restart.

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
payloads dxbell publishes, and check what reaches the panel's command topics. The admin tests run a
small fake of the panel API on a localhost port (`tests/fake_panel.py`).

The admin page is a Lit app in `frontend/`, built into one committed file,
`custom_components/doormonitor/frontend/doormonitor-admin-panel.js`:

```sh
cd frontend
npm ci
npx playwright install --with-deps chromium   # once, for the browser tests
npm run lint && npm run typecheck && npm test
npm run build   # commit the rebuilt bundle with the source change
```

CI fails when the committed bundle does not match the source.

## Releasing

Bump `version` in `custom_components/doormonitor/manifest.json` and push to `main`. Once hassfest and
the tests pass, CI tags the commit `v<version>` and publishes a GitHub release listing the commits
since the previous tag. HACS offers that release as the update. Pushes that don't change the
version publish nothing.
