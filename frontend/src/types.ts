/** Shapes of the panel API v1 (see the panel's API.md), as the integration passes them on. */

export interface HomeAssistant {
  language?: string;
  locale?: { language?: string };
  user?: { is_admin?: boolean; name?: string };
  callWS<T = any>(message: Record<string, unknown>): Promise<T>;
  fetchWithAuth(path: string, init?: RequestInit): Promise<Response>;
}

export type AccessLevel = "guest" | "resident" | "admin";
export type BleKind = "ibeacon" | "mac" | "uuid";
export interface BleId {
  kind: BleKind;
  value: string;
}
export type BleSlot = "phone" | "watch" | "misc";

export interface UserRecord {
  id: string;
  name: string;
  pin: string;
  start: string;
  end: string | null;
  accessLevel: AccessLevel;
  bleData: Record<BleSlot, BleId | null>;
  currentSource?: string;
  isActive?: boolean;
}

export interface HaUser {
  id: string;
  name: string;
}

export interface UsersResponse {
  users: UserRecord[];
  ha_users: HaUser[];
  /** Doorbell user id → Home Assistant user id. */
  links: Record<string, string>;
}

export interface ModeKey {
  scope: "house" | "party";
  mode: string;
}

export interface ModeAppearance {
  theme: string | null;
  mediaGroup: string | null;
}

export type GroupKind = "sound" | "video";

export interface AppearanceResponse {
  modes: { key: ModeKey; appearance: ModeAppearance }[];
  themes: { id: string; label: string }[];
  groups: { id: string; name: string; kind: GroupKind; files: number }[];
  defaultGroup: string | null;
}

export interface MediaFile {
  name: string;
  size: number;
  url?: string;
}

export interface MediaGroupListing {
  id: string;
  name: string;
  kind: GroupKind;
  files: MediaFile[];
  usedBy: ModeKey[];
  isDefault: boolean;
}

export interface MediaResponse {
  photos: MediaFile[];
  groups: MediaGroupListing[];
}

export interface PanelInfo {
  api: number;
  version: string;
  features: string[];
  rootName: string;
}

export interface InfoResponse {
  entries: { entry_id: string; title: string; configured: boolean }[];
  entry_id?: string;
  configured?: boolean;
  actor_name?: string;
  info?: PanelInfo;
  error?: { code: string; message: string };
}
