/** Retained tabs run against an explicit test-only list, never the shipped navigation. */
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  $,
  $$,
  choose,
  click,
  openTab,
  settle,
  setup,
  text,
  toast,
  type,
  wsError,
} from "./helpers";

vi.mock("../src/tabs", () => ({
  TABS: ["users", "appearance", "media-groups", "photos"],
}));

afterEach(() => {
  document.body.innerHTML = "";
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

it("retains Bokmål media labels and regional number formatting", async () => {
  const { el } = await setup({ language: "nb-NO" });
  await openTab(el, "media-groups");
  expect(
    [...$(el, '[data-group="g-bells"]').querySelectorAll(".size")].map(text),
  ).toEqual(["656 KB", "3,4 MB"]);
  expect(text($(el, '[data-group="g-bells"] [data-usage]'))).toBe(
    "Brukes av Halloween, og av moduser uten egen gruppe.",
  );
});
