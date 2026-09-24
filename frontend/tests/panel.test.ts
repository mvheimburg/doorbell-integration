import { afterEach, describe, expect, it } from "vitest";
import { formatSize } from "../src/format";
import { formattingLocale, language } from "../src/localize";
import {
  $,
  $$,
  choose,
  click,
  fixtures,
  openTab,
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
  it("shows the panel's features as tabs and opens the first", async () => {
    const { el } = await setup();
    expect($$(el, "[data-tab]").map((tab) => text(tab))).toEqual([
      "Users",
      "Appearance",
      "Sounds & videos",
      "Photos",
    ]);
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
    expect($$(el, "[data-tab]").map((tab) => tab.dataset.tab)).toEqual([
      "appearance",
    ]);
    expect($(el, "dm-appearance-tab")).toBeTruthy();
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

describe("appearance", () => {
  it("labels the fallbacks and explains each choice", async () => {
    const { el } = await setup();
    await openTab(el, "appearance");
    expect(text($(el, ".intro"))).toContain("A party mode's choices win");
    const home = $(el, '[data-mode="house/home"]');
    expect(text(home.querySelector("h2"))).toBe("Home");
    expect(text(home.querySelector('[data-field="theme"] option'))).toBe(
      "Doorbell (default)",
    );
    expect(
      [...home.querySelectorAll('[data-field="mediaGroup"] option')].map(text),
    ).toEqual([
      "Default: Bells",
      "Bells · 2 sounds",
      "Spooky · 1 video",
      "Empty · 0 sounds",
    ]);
    expect(text(home.querySelector("[data-hint]"))).toBe(
      "Uses the oldest sound group.",
    );
    const hints = (mode: string) =>
      text($(el, `[data-mode="${mode}"] [data-hint]`));
    expect(hints("house/away")).toBe(
      "Plays a random video, with only the video's own sound.",
    );
    expect(hints("party/halloween")).toBe("Uses the house mode's group.");
    expect(hints("party/christmas")).toBe(
      "This group is empty, so the doorbell plays its built-in bell.",
    );
    expect(
      text($(el, '[data-mode="party/halloween"] [data-field="theme"] option')),
    ).toBe("Same as house mode");
  });

  it("saves the whole appearance as soon as a picker changes", async () => {
    const puts: any[] = [];
    const { el } = await setup({
      calls: {
        "PUT modes/*": (message) => {
          puts.push(message);
          return null;
        },
      },
    });
    await openTab(el, "appearance");
    await choose(
      el,
      '[data-mode="house/home"] [data-field="mediaGroup"]',
      "g-bells",
    );
    expect(puts).toEqual([
      expect.objectContaining({
        path: ["modes", "house", "home"],
        body: { theme: null, mediaGroup: "g-bells" },
      }),
    ]);
    expect(toast(el)).toBe("✅ Saved");
    expect(text($(el, '[data-mode="house/home"] [data-hint]'))).toBe(
      "Plays a random sound from the group.",
    );
  });

  it("reverts a refused change", async () => {
    const { el } = await setup({
      calls: {
        "PUT modes/*": () => {
          throw wsError("http-400", "Unknown theme");
        },
      },
    });
    await openTab(el, "appearance");
    await choose(
      el,
      '[data-mode="house/away"] [data-field="theme"]',
      "doorbell",
    );
    expect(toast(el)).toBe("❌ Unknown theme");
    expect(
      $<HTMLSelectElement>(el, '[data-mode="house/away"] [data-field="theme"]')
        .value,
    ).toBe("dark");
  });
});

describe("sounds and videos", () => {
  it("shows each group's use, files and sizes", async () => {
    const { el } = await setup();
    await openTab(el, "media-groups");
    const bells = $(el, '[data-group="g-bells"]');
    expect(text(bells.querySelector("[data-usage]"))).toBe(
      "Used by Halloween, and by modes without a group of their own.",
    );
    expect(bells.querySelector('[data-badge="default"]')).toBeTruthy();
    expect(
      [...bells.querySelectorAll(".size")].map((size) => text(size)),
    ).toEqual(["656 KB", "3.4 MB"]);
    const audio = bells.querySelector("audio")!;
    expect(audio.getAttribute("preload")).toBe("none");
    expect(audio.getAttribute("src")).toBe(
      "/api/doormonitor/e1/media/groups/g-bells/Ding%20Dong.wav?authSig=x",
    );
    expect(text($(el, '[data-group="g-video"] [data-usage]'))).toBe(
      "Used by Away, Halloween.",
    );
    expect($(el, '[data-group="g-video"] video')).toBeTruthy();
    expect(text($(el, '[data-group="g-empty"] [data-usage]'))).toBe(
      "No mode uses this group yet.",
    );
    expect(text($(el, '[data-group="g-empty"] [data-empty]'))).toBe(
      "No sounds yet.",
    );
  });

  it("creates a group", async () => {
    const posts: any[] = [];
    const { el } = await setup({
      calls: {
        "POST media-groups": (message) => {
          posts.push(message.body);
          return { id: "g-new", ...message.body };
        },
      },
    });
    await openTab(el, "media-groups");
    expect($<HTMLButtonElement>(el, '[data-action="create"]').disabled).toBe(
      true,
    );
    await type(el, '[data-field="group-name"]', "  Spooky 2 ");
    await choose(el, '[data-field="group-kind"]', "video");
    await click(el, '[data-action="create"]');
    expect(posts).toEqual([{ name: "Spooky 2", kind: "video" }]);
    expect(toast(el)).toBe("✅ Created Spooky 2");
    expect($<HTMLInputElement>(el, '[data-field="group-name"]').value).toBe("");
  });

  it("predicts what deleting a group does", async () => {
    const { el } = await setup();
    await openTab(el, "media-groups");
    await click(el, '[data-group="g-video"] [data-action="delete-group"]');
    expect($$(el, ".dialog p").map(text)).toEqual([
      "Deletes the group and its 1 file.",
      "Away, Halloween will use their default again.",
      "This cannot be undone.",
    ]);
  });

  it("renames a file keeping its extension", async () => {
    const patches: any[] = [];
    const { el } = await setup({
      calls: {
        "PATCH media/*": (message) => {
          patches.push(message);
          return { name: "Ring_.wav" };
        },
      },
    });
    await openTab(el, "media-groups");
    await click(
      el,
      '[data-group="g-bells"] [data-file="Ding Dong.wav"] [data-action="rename-file"]',
    );
    const form = $(el, "dm-rename-form");
    expect($<HTMLInputElement>(form, "input").value).toBe("Ding Dong");
    expect(text($(form, ".ext"))).toBe(".wav");
    await type(form, "input", "Ring!");
    await click(form, '[data-action="save-name"]');
    await settle(el);
    expect(patches[0]).toMatchObject({
      path: ["media", "groups", "g-bells", "Ding Dong.wav"],
      body: { name: "Ring!.wav" },
    });
    expect(toast(el)).toBe("✅ Renamed to Ring_.wav");
  });

  it("uploads files one by one and says which arrived before a failure", async () => {
    const sent: string[] = [];
    const { el, fetchWithAuth } = await setup({
      fetch: async (path) => {
        sent.push(path);
        if (sent.length === 2)
          return new Response(
            JSON.stringify({ error: "b.wav is larger than 25 MB" }),
            { status: 413 },
          );
        return new Response(JSON.stringify({ name: "a.wav" }), {
          status: 201,
        });
      },
    });
    await openTab(el, "media-groups");
    const form = $(el, '[data-group="g-bells"] dm-upload-form');
    const input = $<HTMLInputElement>(form, 'input[type="file"]');
    expect(input.accept).toBe(".wav,.mp3,.ogg");
    expect(text($(form, ".note"))).toBe("Up to 25 MB per file.");
    const files = new DataTransfer();
    for (const name of ["a.wav", "b.wav", "c.wav"])
      files.items.add(new File(["RIFF"], name, { type: "audio/wav" }));
    input.files = files.files;
    input.dispatchEvent(new Event("change"));
    await click(form, '[data-field="overwrite"]');
    await click(form, '[data-action="upload"]');
    await settle(el);
    expect(sent).toEqual([
      "/api/doormonitor/e1/media/groups/g-bells/a.wav?overwrite=true",
      "/api/doormonitor/e1/media/groups/g-bells/b.wav?overwrite=true",
    ]);
    expect(fetchWithAuth.mock.calls[0][1]).toMatchObject({ method: "PUT" });
    expect(toast(el)).toBe(
      "❌ b.wav is larger than 25 MB (uploaded before it: a.wav)",
    );
  });
});

describe("photos", () => {
  it("shows photos in the panel's order with signed previews", async () => {
    const { el } = await setup();
    await openTab(el, "photos");
    const tab = $(el, "dm-photos-tab");
    expect(text($(tab, "h2"))).toBe("Family photos");
    expect($$(el, ".photo .fname").map(text)).toEqual(["2.jpg", "10.jpg"]);
    expect($(el, ".photo .size")).toBeNull();
    expect($<HTMLImageElement>(el, ".photo img").getAttribute("src")).toBe(
      "/api/doormonitor/e1/media/photos/2.jpg?authSig=x",
    );
    expect($(tab, "dm-upload-form").getAttribute("accept")).toBe(
      ".gif,.jpeg,.jpg,.png,.webp",
    );
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
    expect($$(el, "[data-tab]").map(text)).toEqual([
      "Brukere",
      "Utseende",
      "Lyder og videoer",
      "Bilder",
    ]);
    expect(text($(el, '[data-user="u-res"] [data-badge]'))).toBe("beboer");
    await click(el, '[data-user="u-res"] [data-action="delete"]');
    expect(text($(el, "#confirm-title"))).toBe("Slette Person A?");
    await click(el, '[data-action="confirm"]');
    expect(toast(el)).toBe("❌ You can't delete your own account");

    await openTab(el, "media-groups");
    expect(
      [...$(el, '[data-group="g-bells"]').querySelectorAll(".size")].map(text),
    ).toEqual(["656 KB", "3,4 MB"]);
    expect(text($(el, '[data-group="g-bells"] [data-usage]'))).toBe(
      "Brukes av Halloween, og av moduser uten egen gruppe.",
    );
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
