import { afterEach, describe, expect, it } from "vitest";
import { formatSize } from "../src/format";
import { formattingLocale, language } from "../src/localize";
import {
  $,
  $$,
  choose,
  click,
  fixtures,
  settle,
  setup,
  text,
  toast,
  type,
  wsError,
} from "./helpers";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("shell", () => {
  it("shows only Users even when the panel offers all features", async () => {
    const { el } = await setup();
    expect($$(el, "[data-tab]").map((tab) => text(tab))).toEqual(["Users"]);
    expect($(el, '[data-tab="users"]').getAttribute("aria-selected")).toBe(
      "true",
    );
    expect(text($(el, ".acting"))).toBe("Acting as root");
    expect($(el, "dm-users-tab")).toBeTruthy();
  });

  it("hides tabs the panel does not offer", async () => {
    const data = fixtures();
    data.info.info!.features = ["appearance", "future-thing"];
    const { el } = await setup({ data });
    expect($$(el, "[data-tab]")).toEqual([]);
    expect($(el, "dm-appearance-tab")).toBeNull();
    expect($(el, '[data-page="no-features"]')).toBeTruthy();
  });

  it("says when the panel offers nothing", async () => {
    const data = fixtures();
    data.info.info!.features = [];
    const { el } = await setup({ data });
    expect(text($(el, '[data-page="no-features"]'))).toBe(
      "This panel offers nothing this admin app can manage.",
    );
  });

  it("explains a missing admin connection with a way to settings", async () => {
    const data = fixtures();
    data.info = {
      entries: [{ entry_id: "e1", title: "Doorbell", configured: false }],
      entry_id: "e1",
      configured: false,
    };
    const { el } = await setup({ data });
    expect(text($(el, '[data-page="not-configured"] h2'))).toBe(
      "Admin connection not set up",
    );
    expect($(el, "[data-tab]")).toBeNull();
    const pushed: string[] = [];
    window.addEventListener(
      "location-changed",
      () => pushed.push(location.pathname),
      { once: true },
    );
    await click(el, '[data-page="not-configured"] .btn');
    expect(pushed).toEqual(["/config/integrations/integration/doormonitor"]);
    history.back();
  });

  it("shows a refused token and a lost admin as pages", async () => {
    const data = fixtures();
    data.info.error = { code: "bad-token", message: "Bad API token" };
    const { el } = await setup({ data });
    expect($(el, '[data-page="bad-token"]')).toBeTruthy();
    document.body.innerHTML = "";

    const lost = await setup({
      handlers: {
        "doormonitor/admin/users": () => {
          throw wsError("not-admin", "Not an admin");
        },
      },
    });
    expect(text($(lost.el, '[data-page="not-admin"]'))).toContain(
      "The doorbell admin this integration acts as (root) was deleted",
    );
  });

  it("offers Retry when the panel is unreachable", async () => {
    let down = true;
    const { el } = await setup({
      handlers: {
        "doormonitor/admin/users": () => {
          if (down) throw wsError("unreachable", "The panel is unreachable");
          return fixtures().users;
        },
      },
    });
    expect(text($(el, ".alert"))).toContain(
      "Couldn't load: The panel is unreachable",
    );
    down = false;
    await click(el, '[data-action="retry"]');
    expect($$(el, "[data-user]")).toHaveLength(3);
  });

  it("explains a changed certificate, in Bokmål too", async () => {
    const mismatch = () => {
      throw wsError(
        "fingerprint-mismatch",
        "fingerprint is not the pinned one",
      );
    };
    const { el } = await setup({
      handlers: { "doormonitor/admin/users": mismatch },
    });
    expect(text($(el, ".alert"))).toContain(
      "The panel's certificate has changed",
    );
    const nb = await setup({
      language: "nb-NO",
      handlers: { "doormonitor/admin/users": mismatch },
    });
    expect(text($(nb.el, ".alert"))).toContain("Panelets sertifikat er endret");
  });

  it("switches between panels when there are several", async () => {
    const data = fixtures();
    data.info.entries.push({
      entry_id: "e2",
      title: "Hytta",
      configured: true,
    });
    const { el, callWS } = await setup({ data });
    await choose(el, '[data-field="entry"]', "e2");
    expect(callWS).toHaveBeenCalledWith({
      type: "doormonitor/admin/info",
      entry_id: "e2",
    });
  });
});

describe("users", () => {
  it("lists users with badges, links, and no delete for root", async () => {
    const { el } = await setup();
    const rows = $$(el, "[data-user]");
    expect(rows.map((row) => text(row.querySelector(".name")))).toEqual([
      "Gjest 1",
      "Person A",
      "root",
    ]);
    expect(rows[0].classList.contains("inactive")).toBe(true);
    expect(text(rows[1].querySelector("[data-badge]"))).toBe("resident");
    expect(text(rows[1].querySelector("[data-linked]"))).toBe(
      "Home Assistant: Person A",
    );
    expect(rows[2].querySelector('[data-action="delete"]')).toBeNull();
    expect(rows[2].querySelector(".spacer")).toBeTruthy();
    expect(
      rows[0].querySelector('[data-action="edit"]')!.getAttribute("aria-label"),
    ).toBe("Edit Gjest 1");
  });

  it("adds a user from a Home Assistant user", async () => {
    let saved: any;
    const { el } = await setup({
      handlers: {
        "doormonitor/admin/save_user": (message) => {
          saved = message;
          return { ...message.user, id: "new" };
        },
      },
    });
    await click(el, '[data-action="add-user"]');
    expect(text($(el, "#user-title"))).toBe("Add User");
    expect($<HTMLInputElement>(el, '[data-field="pin"]').value).toBe("0000");
    // Person A is already linked to another doorbell user.
    const options = $$<HTMLOptionElement>(el, '[data-field="haUser"] option');
    expect(options.map((option) => option.value)).toEqual(["", "ha-b"]);

    await choose(el, '[data-field="haUser"]', "ha-b");
    expect($<HTMLInputElement>(el, '[data-field="name"]').value).toBe(
      "Person B",
    );
    await type(el, '[data-field="pin"]', "12a345");
    expect($<HTMLInputElement>(el, '[data-field="pin"]').value).toBe("1234");
    await type(el, '[data-field="pin"]', "5678");
    await type(el, '[data-field="start"]', "2026-10-01");
    await type(el, '[data-field="ble-phone"]', "  AA:BB:CC:DD:EE:FF ");
    await choose(el, '[data-field="ble-phone-kind"]', "mac");
    await click(el, '[data-action="save"]');

    expect(saved).toMatchObject({
      type: "doormonitor/admin/save_user",
      entry_id: "e1",
      ha_user_id: "ha-b",
      user: {
        name: "Person B",
        pin: "5678",
        accessLevel: "resident",
        start: "2026-10-01T00:00:00Z",
        end: null,
        bleData: {
          phone: { kind: "mac", value: "AA:BB:CC:DD:EE:FF" },
          watch: null,
          misc: null,
        },
      },
    });
    expect(saved.user_id).toBeUndefined();
    expect($(el, "#user-title")).toBeNull();
    expect(toast(el)).toBe("✅ Saved Person B");
  });

  it("keeps the form open with the panel's error inside", async () => {
    const { el } = await setup({
      handlers: {
        "doormonitor/admin/save_user": () => {
          throw wsError("http-409", "PIN already in use");
        },
      },
    });
    await click(el, '[data-user="u-res"] [data-action="edit"]');
    expect(text($(el, "#user-title"))).toBe("Edit User");
    expect($<HTMLSelectElement>(el, '[data-field="haUser"]').value).toBe(
      "ha-a",
    );
    await type(el, '[data-field="start"]', "");
    await click(el, '[data-action="save"]');
    expect(text($(el, ".dialog .alert"))).toBe("PIN already in use");
    expect($(el, "#user-title")).toBeTruthy();
    await click(el, '.dialog [data-action="cancel"]');
    expect($(el, "#user-title")).toBeNull();
  });

  it("keeps the stored start when the date is cleared, and unlinks", async () => {
    let saved: any;
    const { el } = await setup({
      handlers: {
        "doormonitor/admin/save_user": (message) => {
          saved = message;
          return { ...message.user, id: message.user_id };
        },
      },
    });
    await click(el, '[data-user="u-res"] [data-action="edit"]');
    await type(el, '[data-field="start"]', "");
    await choose(el, '[data-field="haUser"]', "");
    await click(el, '[data-action="save"]');
    expect(saved.user_id).toBe("u-res");
    expect(saved.user.start).toBe("2026-01-01T00:00:00Z");
    expect(saved.ha_user_id).toBeNull();
  });

  it("deletes after confirmation", async () => {
    const deleted: string[] = [];
    const { el } = await setup({
      calls: {
        "DELETE users/*": (message) => {
          deleted.push(message.path[1]);
          return null;
        },
      },
    });
    await click(el, '[data-user="u-guest"] [data-action="delete"]');
    expect(text($(el, "#confirm-title"))).toBe("Delete Gjest 1?");
    expect(text($(el, ".dialog p"))).toBe("This cannot be undone.");
    await click(el, '[data-action="confirm"]');
    expect(deleted).toEqual(["u-guest"]);
    expect(toast(el)).toBe("🗑️ Deleted Gjest 1");
  });

  it("toasts a refused delete as it is", async () => {
    const { el } = await setup({
      calls: {
        "DELETE users/*": () => {
          throw wsError("http-403", "You can't delete your own account");
        },
      },
    });
    await click(el, '[data-user="u-res"] [data-action="delete"]');
    await click(el, '[data-action="confirm"]');
    expect(toast(el)).toBe("❌ You can't delete your own account");
  });
});

describe("languages", () => {
  it("renders Bokmål and keeps the panel's own sentences", async () => {
    const { el } = await setup({
      language: "nb-NO",
      calls: {
        "DELETE users/*": () => {
          throw wsError("http-403", "You can't delete your own account");
        },
      },
    });
    expect($$(el, "[data-tab]").map(text)).toEqual(["Brukere"]);
    expect(text($(el, '[data-user="u-res"] [data-badge]'))).toBe("beboer");
    await click(el, '[data-user="u-res"] [data-action="delete"]');
    expect(text($(el, "#confirm-title"))).toBe("Slette Person A?");
    await click(el, '[data-action="confirm"]');
    expect(toast(el)).toBe("❌ You can't delete your own account");
  });

  it("follows a language change", async () => {
    const { el } = await setup();
    el.hass = { ...el.hass!, language: "no" };
    await settle(el);
    expect(text($(el, '[data-tab="users"]'))).toBe("Brukere");
  });

  it("normalizes language tags and keeps regional formats", () => {
    expect(language({ language: "nb_NO" })).toBe("nb");
    expect(language({ language: "nn" })).toBe("nb");
    expect(language({ language: "de" })).toBe("en");
    expect(formattingLocale({ language: "no" })).toBe("nb");
    expect(formattingLocale({ language: "en-GB" })).toBe(
      "en-gb".replace("gb", "GB"),
    );
    expect(formattingLocale({ language: "@@" })).toBe("en");
    expect(formatSize(1024 * 1024 * 3.44, "de")).toBe("3,4 MB");
    expect(formatSize(1, "en")).toBe("1 KB");
  });
});
