# DoorMonitor admin panel design

DoorMonitor's sidebar panel currently exposes Users only. Appearance and media components are
retained for later restoration through the tab list in `frontend/src/tabs.ts`.
Preserve the existing Lit form and tab language; household configuration should feel native to
this panel. English and Bokmål labels follow Home Assistant's language without renaming user data.

## Visual owners

`frontend/src/styles.ts` owns runtime tokens and shared layout. It maps Home Assistant text,
primary, surface, divider and radius variables into `--dm-*` tokens. Use its inherited HA font,
`.field`, `.hint`, `.btn`, `.ble`, `.form` and `.dialog` patterns rather than introducing a
feature palette or separate typography. Native select controls retain platform keyboard behavior.
The two-column form collapses on narrow screens and the dialog owns overflow.

## Behavior owners

`Tab` owns loading, retry, inline API failures, confirmations and toast events; the panel shell
owns navigation, language and settings access. `AdminApi` owns service calls. `UsersTab` owns
an explicit draft: Save sends it once, Cancel discards it, and failure keeps it for correction.
The integration remains authoritative for persistent settings and validation.

## Companion BLE import

Inside the phone BLE field, a linked HA user's discovered devices can be offered using existing
select/button styles. One beacon offers an action with its device name; several require a device
choice. The action copies into the draft only and may explicitly replace an existing value.
Changing HA user resets the device choice without silently replacing BLE fields. Missing beacon
data explains how to enable Android's BLE Transmitter sensor and keeps manual entry available.
Import stores a scanner-compatible identity; automatic BLE presence login is not yet wired into
the panel. The UI must state that limit without implying login is enabled.
