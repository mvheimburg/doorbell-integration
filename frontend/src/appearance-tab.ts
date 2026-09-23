import { html, nothing, type TemplateResult } from "lit";
import { icon } from "./icons";
import { fill, modeName, type Strings } from "./localize";
import { Tab } from "./tab";
import type { AppearanceResponse, ModeAppearance, ModeKey } from "./types";

const keyOf = (key: ModeKey) => `${key.scope}/${key.mode}`;

type Group = AppearanceResponse["groups"][number];

export function groupLabel(t: Strings, group: Group): string {
  const one = group.files === 1;
  const text =
    group.kind === "video"
      ? one
        ? t.groupVideo
        : t.groupVideos
      : one
        ? t.groupSound
        : t.groupSounds;
  return fill(text, { name: group.name, n: group.files });
}

/** The one hint under a group picker: the first that applies. */
export function groupHint(
  t: Strings,
  data: AppearanceResponse,
  key: ModeKey,
  chosen: string | null,
): string {
  const group = data.groups.find((item) => item.id === chosen);
  if (group) {
    if (group.files === 0) return t.hintEmpty;
    return group.kind === "video" ? t.hintVideo : t.hintSound;
  }
  if (key.scope === "party") return t.hintParty;
  if (data.defaultGroup) return t.hintDefault;
  return t.hintNone;
}

export class AppearanceTab extends Tab {
  static properties = {
    ...Tab.properties,
    data: { state: true },
    savingKeys: { state: true },
  };

  data?: AppearanceResponse;
  savingKeys = new Set<string>();

  protected async fetch(): Promise<void> {
    this.data = await this.api.call<AppearanceResponse>("GET", ["appearance"]);
  }

  protected renderContent(): TemplateResult {
    const data = this.data!;
    return html`<p class="intro">${this.t.appearanceIntro}</p>
      <div class="modes">
        ${data.modes.map(({ key, appearance }) =>
          this.renderMode(key, appearance),
        )}
      </div>`;
  }

  private renderMode(key: ModeKey, appearance: ModeAppearance) {
    const t = this.t;
    const data = this.data!;
    const house = key.scope === "house";
    const saving = this.savingKeys.has(keyOf(key));
    const defaultGroup = data.groups.find(
      (group) => group.id === data.defaultGroup,
    );
    const none = house
      ? defaultGroup
        ? fill(t.defaultGroup, { name: defaultGroup.name })
        : t.defaultNone
      : t.sameAsHouse;
    return html`<section class="card mode" data-mode=${keyOf(key)}>
      <div class="card-head">
        <h2>
          ${icon(house ? "home" : "party")}<span>${modeName(t, key)}</span>
        </h2>
        ${
          saving
            ? html`<span class="tools" role="status" aria-label=${t.saving}
                >${icon("spinner", "s spin")}</span
              >`
            : nothing
        }
      </div>
      <label class="field">
        ${t.theme}
        <select
          data-field="theme"
          .value=${appearance.theme ?? ""}
          ?disabled=${saving}
          @change=${(e: Event) =>
            this.pick(key, {
              ...appearance,
              theme: (e.target as HTMLSelectElement).value || null,
            })}
        >
          <option value="" ?selected=${appearance.theme === null}>
            ${house ? t.themeDefault : t.sameAsHouse}
          </option>
          ${data.themes.map(
            (theme) =>
              html`<option
                value=${theme.id}
                ?selected=${theme.id === appearance.theme}
              >
                ${theme.label}
              </option>`,
          )}
        </select>
      </label>
      <label class="field">
        ${t.bellMedia}
        <select
          data-field="mediaGroup"
          .value=${appearance.mediaGroup ?? ""}
          ?disabled=${saving}
          @change=${(e: Event) =>
            this.pick(key, {
              ...appearance,
              mediaGroup: (e.target as HTMLSelectElement).value || null,
            })}
        >
          <option value="" ?selected=${appearance.mediaGroup === null}>
            ${none}
          </option>
          ${data.groups.map(
            (group) =>
              html`<option
                value=${group.id}
                ?selected=${group.id === appearance.mediaGroup}
              >
                ${groupLabel(t, group)}
              </option>`,
          )}
        </select>
        <span class="hint" data-hint
          >${groupHint(t, data, key, appearance.mediaGroup)}</span
        >
      </label>
    </section>`;
  }

  private setMode(key: ModeKey, appearance: ModeAppearance) {
    this.data = {
      ...this.data!,
      modes: this.data!.modes.map((mode) =>
        keyOf(mode.key) === keyOf(key) ? { key, appearance } : mode,
      ),
    };
  }

  /** Saves as soon as a picker changes: shown at once, reverted if the panel refuses. */
  private async pick(key: ModeKey, appearance: ModeAppearance) {
    const before = this.data!.modes.find(
      (mode) => keyOf(mode.key) === keyOf(key),
    )!.appearance;
    this.setMode(key, appearance);
    this.savingKeys = new Set(this.savingKeys).add(keyOf(key));
    try {
      await this.api.call("PUT", ["modes", key.scope, key.mode], appearance);
      this.toast(this.t.saved);
    } catch (err) {
      this.setMode(key, before);
      this.fail(err);
    } finally {
      const saving = new Set(this.savingKeys);
      saving.delete(keyOf(key));
      this.savingKeys = saving;
    }
  }
}

if (!customElements.get("dm-appearance-tab"))
  customElements.define("dm-appearance-tab", AppearanceTab);
