import type { AccessLevel, BleKind, HomeAssistant, ModeKey } from "./types";

type Lang = Pick<HomeAssistant, "language" | "locale">;

/** English follows the doorbell admin app's wording (ADMIN.md), which explains its fallbacks. */
const en = {
  title: "Doorbell",
  menu: "Open the sidebar",
  entry: "Doorbell panel",
  actingAs: "Acting as {name}",
  settings: "DoorMonitor settings",
  loading: "Loading…",
  couldNotLoad: "Couldn't load: {message}",
  retry: "Retry",
  noFeatures: "This panel offers nothing this admin app can manage.",
  notSetUpTitle: "No doorbell connected",
  notSetUpBody:
    "Add DoorMonitor under Settings → Devices & services and pick your doorbell panel. Its users, appearance and media can be managed here afterwards.",
  notConfiguredTitle: "Admin connection not set up",
  notConfiguredBody:
    "To manage the doorbell from here, open DoorMonitor's Configure → Admin connection and enter the panel API's address, its token and an admin PIN.",
  notAdminTitle: "The doorbell admin is gone",
  notAdminBody:
    "The doorbell admin this integration acts as ({name}) was deleted, demoted or deactivated. Enter an admin PIN again under Configure → Admin connection.",
  badTokenTitle: "The token was refused",
  badTokenBody:
    "The integration can't talk to the panel (API token). Check the token under Configure → Admin connection.",
  openSettings: "Open DoorMonitor settings",
  tabs: {
    users: "Users",
    appearance: "Appearance",
    "media-groups": "Sounds & videos",
    photos: "Photos",
  } as Record<string, string>,
  errors: {
    unreachable: "The panel is unreachable",
    "bad-response": "The panel sent an answer this app doesn't understand",
    "tls-failed":
      "Home Assistant did not accept the panel's certificate. Check the certificate verification setting under Configure → Admin connection.",
    "fingerprint-mismatch":
      "The panel's certificate has changed and no longer matches the pinned fingerprint. Verify it on the server before updating the fingerprint under Configure → Admin connection.",
    unauthorized: "The panel API refused the authentication",
    forbidden:
      "Access was denied. Check the reverse proxy's IP allowlist and the panel's authorization.",
    redirect:
      "The panel address answered with a redirect, which is not followed. Enter the final address under Configure → Admin connection.",
    "ha-user-linked":
      "That Home Assistant user is already linked to another doorbell user",
    "unknown-ha-user": "That Home Assistant user no longer exists",
  } as Record<string, string>,
  // Feedback
  saved: "✅ Saved",
  savedName: "✅ Saved {name}",
  deletedName: "🗑️ Deleted {name}",
  createdName: "✅ Created {name}",
  renamedTo: "✅ Renamed to {name}",
  uploaded: "✅ Uploaded {names}",
  failed: "❌ {message}",
  failedAfter: "❌ {message} (uploaded before it: {names})",
  // Users
  users: "Users",
  addUser: "Add User",
  editUser: "Edit User",
  editName: "Edit {name}",
  deleteName: "Delete {name}",
  access: { admin: "admin", resident: "resident", guest: "guest" } as Record<
    AccessLevel,
    string
  >,
  accessOption: {
    guest: "Guest",
    resident: "Resident",
    admin: "Admin",
  } as Record<AccessLevel, string>,
  inactive: "Not active now",
  linkedTo: "Home Assistant: {name}",
  haUser: "Home Assistant user",
  haUserNone: "None",
  haUserHint:
    "Picking a person fills in the name and links this doorbell user to them.",
  name: "Name",
  pin: "PIN (4 digits)",
  accessLevel: "Access level",
  activeFrom: "Active from",
  activeUntil: "Active until (optional)",
  ble: { phone: "BLE phone", watch: "BLE watch", misc: "BLE misc" } as Record<
    string,
    string
  >,
  bleKind: { ibeacon: "iBeacon", mac: "MAC", uuid: "UUID" } as Record<
    BleKind,
    string
  >,
  bleKindLabel: "{slot} kind",
  save: "Save",
  cancel: "Cancel",
  delete: "Delete",
  deleteTitle: "Delete {name}?",
  cannotUndo: "This cannot be undone.",
  // Appearance
  appearanceIntro:
    "A party mode's choices win over the house mode while the party mode is on. Groups of sounds and videos are managed on the Sounds & videos tab. Changes show on the doorbell within a second.",
  modes: {
    home: "Home",
    away: "Away",
    vacation: "Vacation",
    halloween: "Halloween",
    christmas: "Christmas",
    easter: "Easter",
    birthday: "Birthday",
  } as Record<string, string>,
  theme: "Theme",
  themeDefault: "Doorbell (default)",
  sameAsHouse: "Same as house mode",
  bellMedia: "Bell sounds or videos",
  defaultGroup: "Default: {name}",
  defaultNone: "Default: none",
  groupSounds: "{name} · {n} sounds",
  groupSound: "{name} · 1 sound",
  groupVideos: "{name} · {n} videos",
  groupVideo: "{name} · 1 video",
  hintEmpty: "This group is empty, so the doorbell plays its built-in bell.",
  hintVideo: "Plays a random video, with only the video's own sound.",
  hintSound: "Plays a random sound from the group.",
  hintParty: "Uses the house mode's group.",
  hintDefault: "Uses the oldest sound group.",
  hintNone: "Create a sound group on the Sounds & videos tab.",
  saving: "Saving…",
  // Sounds & videos
  newGroup: "New group",
  newGroupIntro:
    "A group holds bell sounds or videos. Each mode picks a group on the Appearance tab, and a bell press plays a random file from it. Videos play with their own sound only.",
  groupNamePlaceholder: "Name, for example Spooky",
  groupName: "Group name",
  kind: "Kind",
  kindSounds: "Sounds",
  kindVideos: "Videos",
  create: "Create",
  noGroups: "No groups yet, so the doorbell plays its built-in bell.",
  renameGroup: "Rename group",
  deleteGroup: "Delete group",
  defaultBadge: "Default",
  usedAndDefault: "Used by {modes}, and by modes without a group of their own.",
  used: "Used by {modes}.",
  defaultOnly: "Played by modes without a group of their own.",
  unused: "No mode uses this group yet.",
  noSounds: "No sounds yet.",
  noVideos: "No videos yet.",
  deleteGroupEmpty: "Deletes the empty group.",
  deleteGroupOne: "Deletes the group and its 1 file.",
  deleteGroupMany: "Deletes the group and its {n} files.",
  modesFallBack: "{modes} will use their default again.",
  // Files
  rename: "Rename {name}",
  saveName: "Save name",
  newName: "New name",
  replace: "Replace files with the same name",
  chooseFiles: "Files to upload",
  upload: "Upload",
  sizeNote: "Up to {n} MB per file.",
  // Photos
  photosTitle: "Family photos",
  photosIntro: "The doorbell's home screen shows these in turn.",
  noPhotos: "No photos yet.",
  close: "Close",
};

export type Strings = typeof en;

const nb: Strings = {
  title: "Ringeklokke",
  menu: "Åpne sidepanelet",
  entry: "Ringeklokkepanel",
  actingAs: "Handler som {name}",
  settings: "DoorMonitor-innstillinger",
  loading: "Laster …",
  couldNotLoad: "Kunne ikke laste: {message}",
  retry: "Prøv igjen",
  noFeatures:
    "Dette panelet tilbyr ingenting denne administrasjonen kan styre.",
  notSetUpTitle: "Ingen ringeklokke er koblet til",
  notSetUpBody:
    "Legg til DoorMonitor under Innstillinger → Enheter og tjenester og velg ringeklokkepanelet. Brukere, utseende og medier kan deretter styres her.",
  notConfiguredTitle: "Administratortilkoblingen er ikke satt opp",
  notConfiguredBody:
    "For å styre ringeklokken herfra åpner du Konfigurer → Administratortilkobling for DoorMonitor og skriver inn adressen til panel-API-et, tokenet og en administrator-PIN.",
  notAdminTitle: "Ringeklokke-administratoren finnes ikke lenger",
  notAdminBody:
    "Administratoren denne integrasjonen handler som ({name}), er slettet, nedgradert eller deaktivert. Skriv inn en administrator-PIN på nytt under Konfigurer → Administratortilkobling.",
  badTokenTitle: "Tokenet ble avvist",
  badTokenBody:
    "Integrasjonen får ikke snakke med panelet (API-token). Sjekk tokenet under Konfigurer → Administratortilkobling.",
  openSettings: "Åpne DoorMonitor-innstillingene",
  tabs: {
    users: "Brukere",
    appearance: "Utseende",
    "media-groups": "Lyder og videoer",
    photos: "Bilder",
  },
  errors: {
    unreachable: "Får ikke kontakt med panelet",
    "bad-response": "Panelet sendte et svar denne appen ikke forstår",
    "tls-failed":
      "Home Assistant godtok ikke panelets sertifikat. Sjekk sertifikatkontrollen under Konfigurer → Administratortilkobling.",
    "fingerprint-mismatch":
      "Panelets sertifikat er endret og stemmer ikke lenger med det festede fingeravtrykket. Kontroller det på serveren før du oppdaterer fingeravtrykket under Konfigurer → Administratortilkobling.",
    unauthorized: "Panel-API-et avviste autentiseringen",
    forbidden:
      "Tilgang nektet. Sjekk IP-tillatelseslisten i den omvendte proxyen og panelets tilgangskontroll.",
    redirect:
      "Paneladressen svarte med en videresending, som ikke følges. Skriv inn den endelige adressen under Konfigurer → Administratortilkobling.",
    "ha-user-linked":
      "Denne Home Assistant-brukeren er allerede koblet til en annen ringeklokkebruker",
    "unknown-ha-user": "Denne Home Assistant-brukeren finnes ikke lenger",
  },
  saved: "✅ Lagret",
  savedName: "✅ Lagret {name}",
  deletedName: "🗑️ Slettet {name}",
  createdName: "✅ Opprettet {name}",
  renamedTo: "✅ Omdøpt til {name}",
  uploaded: "✅ Lastet opp {names}",
  failed: "❌ {message}",
  failedAfter: "❌ {message} (lastet opp før dette: {names})",
  users: "Brukere",
  addUser: "Legg til bruker",
  editUser: "Rediger bruker",
  editName: "Rediger {name}",
  deleteName: "Slett {name}",
  access: { admin: "administrator", resident: "beboer", guest: "gjest" },
  accessOption: {
    guest: "Gjest",
    resident: "Beboer",
    admin: "Administrator",
  },
  inactive: "Ikke aktiv nå",
  linkedTo: "Home Assistant: {name}",
  haUser: "Home Assistant-bruker",
  haUserNone: "Ingen",
  haUserHint:
    "Velger du en person, fylles navnet inn og ringeklokkebrukeren kobles til personen.",
  name: "Navn",
  pin: "PIN (4 sifre)",
  accessLevel: "Tilgangsnivå",
  activeFrom: "Aktiv fra",
  activeUntil: "Aktiv til (valgfritt)",
  ble: { phone: "BLE telefon", watch: "BLE klokke", misc: "BLE annet" },
  bleKind: { ibeacon: "iBeacon", mac: "MAC", uuid: "UUID" },
  bleKindLabel: "Type for {slot}",
  save: "Lagre",
  cancel: "Avbryt",
  delete: "Slett",
  deleteTitle: "Slette {name}?",
  cannotUndo: "Dette kan ikke angres.",
  appearanceIntro:
    "Valgene for en festmodus vinner over husmodusen mens festmodusen er på. Grupper med lyder og videoer styres på fanen Lyder og videoer. Endringer vises på ringeklokken innen et sekund.",
  modes: {
    home: "Hjemme",
    away: "Borte",
    vacation: "Ferie",
    halloween: "Halloween",
    christmas: "Jul",
    easter: "Påske",
    birthday: "Bursdag",
  },
  theme: "Tema",
  themeDefault: "Doorbell (standard)",
  sameAsHouse: "Samme som husmodus",
  bellMedia: "Ringelyder eller videoer",
  defaultGroup: "Standard: {name}",
  defaultNone: "Standard: ingen",
  groupSounds: "{name} · {n} lyder",
  groupSound: "{name} · 1 lyd",
  groupVideos: "{name} · {n} videoer",
  groupVideo: "{name} · 1 video",
  hintEmpty:
    "Denne gruppen er tom, så ringeklokken spiller den innebygde ringelyden.",
  hintVideo: "Spiller en tilfeldig video, bare med videoens egen lyd.",
  hintSound: "Spiller en tilfeldig lyd fra gruppen.",
  hintParty: "Bruker gruppen til husmodusen.",
  hintDefault: "Bruker den eldste lydgruppen.",
  hintNone: "Lag en lydgruppe på fanen Lyder og videoer.",
  saving: "Lagrer …",
  newGroup: "Ny gruppe",
  newGroupIntro:
    "En gruppe inneholder ringelyder eller videoer. Hver modus velger en gruppe på fanen Utseende, og et trykk på ringeklokken spiller en tilfeldig fil fra den. Videoer spilles bare med sin egen lyd.",
  groupNamePlaceholder: "Navn, for eksempel Skummelt",
  groupName: "Gruppenavn",
  kind: "Type",
  kindSounds: "Lyder",
  kindVideos: "Videoer",
  create: "Opprett",
  noGroups:
    "Ingen grupper ennå, så ringeklokken spiller den innebygde ringelyden.",
  renameGroup: "Gi gruppen nytt navn",
  deleteGroup: "Slett gruppen",
  defaultBadge: "Standard",
  usedAndDefault: "Brukes av {modes}, og av moduser uten egen gruppe.",
  used: "Brukes av {modes}.",
  defaultOnly: "Spilles av moduser uten egen gruppe.",
  unused: "Ingen modus bruker denne gruppen ennå.",
  noSounds: "Ingen lyder ennå.",
  noVideos: "Ingen videoer ennå.",
  deleteGroupEmpty: "Sletter den tomme gruppen.",
  deleteGroupOne: "Sletter gruppen og den ene filen i den.",
  deleteGroupMany: "Sletter gruppen og de {n} filene i den.",
  modesFallBack: "{modes} bruker standardvalget sitt igjen.",
  rename: "Gi {name} nytt navn",
  saveName: "Lagre navnet",
  newName: "Nytt navn",
  replace: "Erstatt filer med samme navn",
  chooseFiles: "Filer som skal lastes opp",
  upload: "Last opp",
  sizeNote: "Opptil {n} MB per fil.",
  photosTitle: "Familiebilder",
  photosIntro: "Startskjermen på ringeklokken viser disse etter tur.",
  noPhotos: "Ingen bilder ennå.",
  close: "Lukk",
};

/** Translation language: nb, nb-NO, no and the nn fallback give Bokmål. */
export function language(hass?: Lang): "nb" | "en" {
  const value = String(hass?.language || hass?.locale?.language || "en")
    .toLowerCase()
    .replace(/_/g, "-");
  return /^(nb|no|nn)(-|$)/.test(value) ? "nb" : "en";
}

/** Formatting locale stays regional (en-GB keeps its format) and never throws. */
export function formattingLocale(hass?: Lang): string {
  const requested = String(hass?.language || hass?.locale?.language || "en")
    .toLowerCase()
    .replace(/_/g, "-")
    .replace(/^(no|nn)(-|$)/, "nb$2");
  try {
    return Intl.getCanonicalLocales(requested)[0] || "en";
  } catch {
    return "en";
  }
}

export function localize(hass?: Lang): Strings {
  return language(hass) === "nb" ? nb : en;
}

export function fill(
  text: string,
  values: Record<string, string | number>,
): string {
  return text.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? ""));
}

/** A mode's display name; an unknown mode stays recognizable. */
export function modeName(t: Strings, key: ModeKey): string {
  return t.modes[key.mode] ?? key.mode;
}

/** Our own error codes are translated; the panel's sentences are shown as they are. */
export function errorMessage(
  t: Strings,
  err: { code?: string; message: string },
): string {
  return (err.code && t.errors[err.code]) || err.message;
}
