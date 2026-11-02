import { afterEach, expect, it } from "vitest";
import { page, userEvent } from "vitest/browser";
import {
  $,
  $$,
  choose,
  click,
  fixtures,
  settle,
  setup,
  text,
  type,
} from "./helpers";

const first = "00112233445566778899aabbccddeeff_1_513";
const second = "ffeeddccbbaa99887766554433221100_0_65535";

function dataWithBeacons(ids = [first]) {
  const data = fixtures();
  data.users.ha_users = [
    { id: "ha-a", name: "Person A" },
    {
      id: "ha-b",
      name: "Person B",
      beacons: ids.map((id, i) => ({ id, name: `Phone ${i + 1}` })),
    },
  ];
  return data;
}

afterEach(async () => {
  document.body.innerHTML = "";
  document.body.removeAttribute("style");
  await page.viewport(1280, 720);
});

it("offers a beacon explicitly and saves the exact panel payload", async () => {
  let saved: any;
  const { el, callWS } = await setup({
    data: dataWithBeacons(),
    handlers: {
      "doormonitor/admin/save_user": (message) => {
        saved = message;
        return { ...message.user, id: "new" };
      },
    },
  });
  await click(el, '[data-action="add-user"]');
  expect($(el, '[data-action="use-beacon"]')).toBeNull();
  await choose(el, '[data-field="haUser"]', "ha-b");
  expect(text($(el, '[data-action="use-beacon"]'))).toBe("Use phone beacon");
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe("");
  expect(text($(el, "[data-beacon-offer]"))).toContain("Phone 1");
  await click(el, '[data-action="use-beacon"]');
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(first);
  expect(
    callWS.mock.calls.filter(
      ([msg]) => msg.type === "doormonitor/admin/save_user",
    ),
  ).toHaveLength(0);
  await click(el, '[data-action="save"]');
  expect(saved.ha_user_id).toBe("ha-b");
  expect(saved.user.bleData).toEqual({
    phone: { kind: "ibeacon", value: first },
    watch: null,
    misc: null,
  });
});

it("requires choosing between devices and resets the choice when HA user changes", async () => {
  const { el } = await setup({ data: dataWithBeacons([first, second]) });
  await click(el, '[data-user="u-res"] [data-action="edit"]');
  await choose(el, '[data-field="haUser"]', "ha-b");
  const button = () => $<HTMLButtonElement>(el, '[data-action="use-beacon"]');
  expect(button().disabled).toBe(true);
  expect($$(el, '[data-field="beacon"] option').map((o) => text(o))).toEqual([
    "Choose a device",
    "Phone 1",
    "Phone 2",
  ]);
  await choose(el, '[data-field="beacon"]', second);
  await click(el, '[data-action="use-beacon"]');
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(
    second,
  );
  await choose(el, '[data-field="haUser"]', "ha-a");
  expect($(el, '[data-action="use-beacon"]')).toBeNull();
  await choose(el, '[data-field="haUser"]', "ha-b");
  expect(button().disabled).toBe(true);
  expect($<HTMLSelectElement>(el, '[data-field="beacon"]').value).toBe("");
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(
    second,
  );
});

it("preserves manual values and Cancel leaves the saved user untouched", async () => {
  const data = dataWithBeacons();
  data.users.users[1].bleData.phone = {
    kind: "mac",
    value: "AA:BB:CC:DD:EE:FF",
  };
  const { el, callWS } = await setup({ data });
  await click(el, '[data-user="u-res"] [data-action="edit"]');
  await choose(el, '[data-field="haUser"]', "ha-b");
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(
    "AA:BB:CC:DD:EE:FF",
  );
  expect($<HTMLSelectElement>(el, '[data-field="ble-phone-kind"]').value).toBe(
    "mac",
  );
  await click(el, '[data-action="use-beacon"]');
  expect($<HTMLSelectElement>(el, '[data-field="ble-phone-kind"]').value).toBe(
    "ibeacon",
  );
  await click(el, '.dialog [data-action="cancel"]');
  expect(
    callWS.mock.calls.filter(
      ([msg]) => msg.type === "doormonitor/admin/save_user",
    ),
  ).toHaveLength(0);
  await click(el, '[data-user="u-res"] [data-action="edit"]');
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(
    "AA:BB:CC:DD:EE:FF",
  );
});

it.each(["en", "nb", "nb-NO", "no", "nn"])(
  "localizes the offer and empty guidance for %s",
  async (language) => {
    const { el } = await setup({
      data: dataWithBeacons(),
      language,
      narrow: true,
    });
    await click(el, '[data-user="u-res"] [data-action="edit"]');
    expect(text($(el, "[data-beacon-empty]"))).toContain("BLE Transmitter");
    expect($(el, '[data-field="ble-phone"]')).toBeTruthy();
    await choose(el, '[data-field="haUser"]', "ha-b");
    expect(text($(el, '[data-action="use-beacon"]'))).toBe(
      language === "en" ? "Use phone beacon" : "Bruk telefonens signal",
    );
    expect(text($(el, "[data-beacon-offer]")).toLowerCase()).toContain(
      language === "en" ? "automatic login" : "automatisk innlogging",
    );
    el.hass = { ...el.hass!, language: language === "en" ? "nb" : "en" };
    await settle(el);
    expect(text($(el, '[data-action="use-beacon"]'))).toBe(
      language === "en" ? "Bruk telefonens signal" : "Use phone beacon",
    );
  },
);

it("retains the imported draft and shows a failed save without repeating requests", async () => {
  let rejectSave!: (error: unknown) => void;
  const { el, callWS } = await setup({
    data: dataWithBeacons(),
    handlers: {
      "doormonitor/admin/save_user": () =>
        new Promise((_, reject) => {
          rejectSave = reject;
        }),
    },
  });
  await click(el, '[data-action="add-user"]');
  await choose(el, '[data-field="haUser"]', "ha-b");
  await click(el, '[data-action="use-beacon"]');
  await type(el, '[data-field="pin"]', "5678");
  await click(el, '[data-action="save"]');
  expect($<HTMLButtonElement>(el, '[data-action="use-beacon"]').disabled).toBe(
    true,
  );
  await click(el, '[data-action="save"]');
  expect(
    callWS.mock.calls.filter(
      ([msg]) => msg.type === "doormonitor/admin/save_user",
    ),
  ).toHaveLength(1);
  rejectSave({ code: "http-409", message: "PIN already in use" });
  await settle(el);
  expect(text($(el, ".dialog .alert"))).toBe("PIN already in use");
  expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(first);
});

it.each(["light", "dark"])(
  "keeps the device choice usable on a narrow %s screen",
  async (theme) => {
    await page.viewport(390, 844);
    document.body.style.cssText =
      theme === "dark"
        ? "--primary-text-color:#eee;--secondary-text-color:#bbb;--card-background-color:#202124;--primary-color:#bb86fc;--divider-color:#555;--text-primary-color:#151515;"
        : "--primary-text-color:#222;--secondary-text-color:#555;--card-background-color:#fff;--primary-color:#6750a4;--divider-color:#ccc;--text-primary-color:#fff;";
    const { el } = await setup({
      data: dataWithBeacons([first, second]),
      language: "nb",
      narrow: true,
    });
    await click(el, '[data-user="u-res"] [data-action="edit"]');
    await choose(el, '[data-field="haUser"]', "ha-b");
    await choose(el, '[data-field="beacon"]', second);
    const select = $<HTMLSelectElement>(el, '[data-field="beacon"]');
    select.focus();
    await userEvent.tab();
    const button = $<HTMLButtonElement>(el, '[data-action="use-beacon"]');
    expect(button.getRootNode() instanceof ShadowRoot).toBe(true);
    expect((button.getRootNode() as ShadowRoot).activeElement).toBe(button);
    await userEvent.keyboard("{Enter}");
    await settle(el);
    expect($<HTMLInputElement>(el, '[data-field="ble-phone"]').value).toBe(
      second,
    );
    const dialog = $(el, ".dialog");
    expect(dialog.scrollWidth).toBeLessThanOrEqual(dialog.clientWidth);
    const bounds = dialog.getBoundingClientRect();
    expect(bounds.left).toBeGreaterThanOrEqual(0);
    expect(bounds.right).toBeLessThanOrEqual(390);
    expect(bounds.height).toBeLessThanOrEqual(844);
    await page.screenshot({
      path: `__screenshots__/beacon-import-${theme}.png`,
    });
  },
);
