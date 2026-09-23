import { vi } from "vitest";
import "../src/doormonitor-admin-panel";
import type { DoorMonitorAdminPanel } from "../src/doormonitor-admin-panel";
import type {
  AppearanceResponse,
  InfoResponse,
  MediaResponse,
  UserRecord,
} from "../src/types";

export const user = (
  id: string,
  name: string,
  accessLevel: UserRecord["accessLevel"],
  extra: Partial<UserRecord> = {},
): UserRecord => ({
  id,
  name,
  pin: "1234",
  start: "2026-01-01T00:00:00Z",
  end: null,
  accessLevel,
  bleData: { phone: null, watch: null, misc: null },
  currentSource: "none",
  isActive: true,
  ...extra,
});

/** A doorbell with generic dummy data, as the integration's websocket API returns it. */
export function fixtures() {
  const info: InfoResponse = {
    entries: [{ entry_id: "e1", title: "Doorbell", configured: true }],
    entry_id: "e1",
    configured: true,
    actor_name: "root",
    info: {
      api: 1,
      version: "0.1.25",
      features: ["users", "appearance", "media-groups", "photos"],
      rootName: "root",
    },
  };
  const users = {
    users: [
      user("u-guest", "Gjest 1", "guest", { isActive: false }),
      user("u-res", "Person A", "resident"),
      user("root", "root", "admin"),
    ],
    ha_users: [
      { id: "ha-a", name: "Person A" },
      { id: "ha-b", name: "Person B" },
    ],
    links: { "u-res": "ha-a" } as Record<string, string>,
  };
  const appearance: AppearanceResponse = {
    modes: [
      {
        key: { scope: "house", mode: "home" },
        appearance: { theme: null, mediaGroup: null },
      },
      {
        key: { scope: "house", mode: "away" },
        appearance: { theme: "dark", mediaGroup: "g-video" },
      },
      {
        key: { scope: "party", mode: "halloween" },
        appearance: { theme: null, mediaGroup: null },
      },
      {
        key: { scope: "party", mode: "christmas" },
        appearance: { theme: null, mediaGroup: "g-empty" },
      },
    ],
    themes: [
      { id: "doorbell", label: "Doorbell" },
      { id: "dark", label: "Dark" },
    ],
    groups: [
      { id: "g-bells", name: "Bells", kind: "sound", files: 2 },
      { id: "g-video", name: "Spooky", kind: "video", files: 1 },
      { id: "g-empty", name: "Empty", kind: "sound", files: 0 },
    ],
    defaultGroup: "g-bells",
  };
  const media: MediaResponse = {
    photos: [
      { name: "2.jpg", size: 482113 },
      { name: "10.jpg", size: 1000 },
    ],
    groups: [
      {
        id: "g-bells",
        name: "Bells",
        kind: "sound",
        files: [
          { name: "Ding Dong.wav", size: 671000 },
          { name: "Long.mp3", size: 3565158 },
        ],
        usedBy: [{ scope: "party", mode: "halloween" }],
        isDefault: true,
      },
      {
        id: "g-video",
        name: "Spooky",
        kind: "video",
        files: [{ name: "ghost.mp4", size: 12000 }],
        usedBy: [
          { scope: "house", mode: "away" },
          { scope: "party", mode: "halloween" },
        ],
        isDefault: false,
      },
      {
        id: "g-empty",
        name: "Empty",
        kind: "sound",
        files: [],
        usedBy: [],
        isDefault: false,
      },
    ],
  };
  return { info, users, appearance, media };
}

export type WsHandler = (message: any) => unknown;

export async function setup(
  options: {
    language?: string;
    narrow?: boolean;
    handlers?: Record<string, WsHandler>;
    calls?: Record<string, WsHandler>;
    fetch?: (path: string, init?: RequestInit) => Promise<Response>;
    data?: ReturnType<typeof fixtures>;
  } = {},
) {
  const data = options.data ?? fixtures();
  const calls: Record<string, WsHandler> = {
    "GET users": () => data.users.users,
    "GET appearance": () => data.appearance,
    "GET media": () => data.media,
    ...options.calls,
  };
  const handlers: Record<string, WsHandler> = {
    "doormonitor/admin/info": () => data.info,
    "doormonitor/admin/users": () => data.users,
    "auth/sign_path": (message) => ({ path: `${message.path}?authSig=x` }),
    "doormonitor/admin/call": (message) => {
      const key = `${message.method} ${message.path.join("/")}`;
      const handler =
        calls[key] ?? calls[`${message.method} ${message.path[0]}/*`];
      if (!handler) throw new Error(`unexpected ${key}`);
      return handler(message);
    },
    ...options.handlers,
  };
  const callWS = vi.fn(async (message: any) => {
    const handler = handlers[message.type];
    if (!handler) throw new Error(`unexpected ${message.type}`);
    return handler(message);
  });
  const fetchWithAuth = vi.fn(
    options.fetch ??
      (async () =>
        new Response(JSON.stringify({ name: "x" }), { status: 201 })),
  );
  const el = document.createElement(
    "doormonitor-admin-panel",
  ) as DoorMonitorAdminPanel;
  el.narrow = !!options.narrow;
  el.hass = {
    language: options.language ?? "en",
    locale: { language: options.language ?? "en" },
    callWS: callWS as any,
    fetchWithAuth: fetchWithAuth as any,
  };
  document.body.appendChild(el);
  await settle(el);
  return { el, callWS, fetchWithAuth, data };
}

/** A websocket error as Home Assistant's frontend rejects with it. */
export const wsError = (code: string, message: string) => ({ code, message });

/** Every shadow root under the panel, so tests can query across tabs and widgets. */
function roots(root: ParentNode): ParentNode[] {
  const found: ParentNode[] = [root];
  for (const element of root.querySelectorAll("*")) {
    if (element.shadowRoot) found.push(...roots(element.shadowRoot));
  }
  return found;
}

export async function settle(el: Element) {
  for (let i = 0; i < 8; i++) {
    await new Promise((resolve) => setTimeout(resolve, 0));
    for (const root of roots(el.shadowRoot!)) {
      const host = (root as ShadowRoot).host as any;
      if (host?.updateComplete) await host.updateComplete;
    }
  }
}

export const $ = <T extends Element = HTMLElement>(
  el: Element,
  selector: string,
): T => {
  for (const root of roots(el.shadowRoot!)) {
    const found = root.querySelector(selector);
    if (found) return found as T;
  }
  return null as unknown as T;
};

export const $$ = <T extends Element = HTMLElement>(
  el: Element,
  selector: string,
): T[] =>
  roots(el.shadowRoot!).flatMap((root) => [
    ...root.querySelectorAll(selector),
  ]) as T[];

export async function click(el: Element, selector: string) {
  const target = $(el, selector);
  if (!target) throw new Error(`missing ${selector}`);
  target.click();
  await settle(el);
}

export async function type(el: Element, selector: string, value: string) {
  const input = $<HTMLInputElement>(el, selector);
  if (!input) throw new Error(`missing ${selector}`);
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  await settle(el);
}

export async function choose(el: Element, selector: string, value: string) {
  const select = $<HTMLSelectElement>(el, selector);
  if (!select) throw new Error(`missing ${selector}`);
  select.value = value;
  select.dispatchEvent(new Event("change", { bubbles: true }));
  await settle(el);
}

export async function openTab(el: Element, tab: string) {
  await click(el, `[data-tab="${tab}"]`);
}

export const text = (element: Element | null) =>
  (element?.textContent ?? "").replace(/\s+/g, " ").trim();

export const toast = (el: Element) => text($(el, ".toast"));
