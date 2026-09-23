import { html, nothing, type TemplateResult } from "lit";
import type { MediaPath } from "./api";
import { icon } from "./icons";
import { fill, modeName, type Strings } from "./localize";
import { Tab } from "./tab";
import type {
  GroupKind,
  MediaGroupListing,
  MediaResponse,
  ModeKey,
} from "./types";

const ACCEPT: Record<GroupKind, string> = {
  sound: ".wav,.mp3,.ogg",
  video: ".mp4,.webm,.mkv",
};
const SIZE_MB: Record<GroupKind, number> = { sound: 25, video: 200 };

const modeList = (t: Strings, modes: ModeKey[]) =>
  modes.map((key) => modeName(t, key)).join(", ");

export function usageLine(t: Strings, group: MediaGroupListing): string {
  const modes = modeList(t, group.usedBy);
  if (group.usedBy.length && group.isDefault)
    return fill(t.usedAndDefault, { modes });
  if (group.usedBy.length) return fill(t.used, { modes });
  if (group.isDefault) return t.defaultOnly;
  return t.unused;
}

export function deleteGroupLines(
  t: Strings,
  group: MediaGroupListing,
): string[] {
  const count = group.files.length;
  const lines = [
    count === 0
      ? t.deleteGroupEmpty
      : count === 1
        ? t.deleteGroupOne
        : fill(t.deleteGroupMany, { n: count }),
  ];
  if (group.usedBy.length)
    lines.push(fill(t.modesFallBack, { modes: modeList(t, group.usedBy) }));
  lines.push(t.cannotUndo);
  return lines;
}

export class MediaTab extends Tab {
  static properties = {
    ...Tab.properties,
    groups: { state: true },
    newName: { state: true },
    newKind: { state: true },
    creating: { state: true },
    renamingGroup: { state: true },
    groupBusy: { state: true },
  };

  groups: MediaGroupListing[] = [];
  newName = "";
  newKind: GroupKind = "sound";
  creating = false;
  renamingGroup?: string;
  groupBusy = false;

  protected async fetch(): Promise<void> {
    const media = await this.api.call<MediaResponse>("GET", ["media"]);
    this.groups = media.groups;
    await this.signAll(
      media.groups.flatMap((group) =>
        group.files.map((file) => this.path(group, file.name)),
      ),
    );
  }

  private path(group: MediaGroupListing, name: string): MediaPath {
    return ["groups", group.id, name];
  }

  protected renderContent(): TemplateResult {
    const t = this.t;
    return html`${this.renderNewGroup()}
    ${
      this.groups.length
        ? this.groups.map((group) => this.renderGroup(group))
        : html`<section class="card">
            <p class="muted" data-empty>${t.noGroups}</p>
          </section>`
    }`;
  }

  private renderNewGroup() {
    const t = this.t;
    return html`<section class="card">
      <div class="card-head">
        <h2>${icon("folderPlus")}<span>${t.newGroup}</span></h2>
      </div>
      <p class="intro">${t.newGroupIntro}</p>
      <form
        class="inline-form"
        @submit=${(e: Event) => {
          e.preventDefault();
          void this.create();
        }}
      >
        <input
          type="text"
          data-field="group-name"
          maxlength="64"
          aria-label=${t.groupName}
          placeholder=${t.groupNamePlaceholder}
          .value=${this.newName}
          ?disabled=${this.creating}
          @input=${(e: Event) =>
            (this.newName = (e.target as HTMLInputElement).value)}
        />
        <select
          data-field="group-kind"
          aria-label=${t.kind}
          ?disabled=${this.creating}
          @change=${(e: Event) =>
            (this.newKind = (e.target as HTMLSelectElement).value as GroupKind)}
        >
          <option value="sound" ?selected=${this.newKind === "sound"}>
            ${t.kindSounds}
          </option>
          <option value="video" ?selected=${this.newKind === "video"}>
            ${t.kindVideos}
          </option>
        </select>
        <button
          class="btn primary"
          type="submit"
          data-action="create"
          ?disabled=${!this.newName.trim() || this.creating}
        >
          ${this.creating ? icon("spinner", "s spin") : icon("plus", "s")}
          ${t.create}
        </button>
      </form>
    </section>`;
  }

  private renderGroup(group: MediaGroupListing) {
    const t = this.t;
    const video = group.kind === "video";
    return html`<section class="card" data-group=${group.id}>
      <div class="card-head">
        ${
          this.renamingGroup === group.id
            ? html`${icon(video ? "film" : "music")}
                <dm-rename-form
                  style="flex:1"
                  .t=${t}
                  .value=${group.name}
                  .maxLength=${64}
                  .label=${t.groupName}
                  .busy=${this.groupBusy}
                  @dm-save=${(e: CustomEvent<string>) =>
                    this.renameGroup(group, e.detail)}
                  @dm-cancel=${() => (this.renamingGroup = undefined)}
                ></dm-rename-form>`
            : html`<h2>
                  ${icon(video ? "film" : "music")}<span>${group.name}</span>
                </h2>
                <div class="tools">
                  ${
                    group.isDefault
                      ? html`<span class="badge default" data-badge="default"
                          >${t.defaultBadge}</span
                        >`
                      : nothing
                  }
                  <span class="badge" data-badge="kind"
                    >${video ? t.kindVideos : t.kindSounds}</span
                  >
                  <button
                    class="icon-btn"
                    data-action="rename-group"
                    aria-label=${t.renameGroup}
                    title=${t.renameGroup}
                    @click=${() => (this.renamingGroup = group.id)}
                  >
                    ${icon("pencil", "s")}
                  </button>
                  <button
                    class="icon-btn danger"
                    data-action="delete-group"
                    aria-label=${t.deleteGroup}
                    title=${t.deleteGroup}
                    @click=${() =>
                      this.ask({
                        title: fill(t.deleteTitle, { name: group.name }),
                        lines: deleteGroupLines(t, group),
                        run: () => this.deleteGroup(group),
                      })}
                  >
                    ${icon("trash", "s")}
                  </button>
                </div>`
        }
      </div>
      <p class="intro" data-usage>${usageLine(t, group)}</p>
      ${
        !group.files.length
          ? html`<p class="muted" data-empty>
              ${video ? t.noVideos : t.noSounds}
            </p>`
          : video
            ? html`<div class="grid videos">
                ${group.files.map((file) => {
                  const path = this.path(group, file.name);
                  const url = this.previewUrl(path);
                  return html`<div>
                    ${
                      url
                        ? html`<video
                            controls
                            preload="metadata"
                            src=${url}
                          ></video>`
                        : nothing
                    }
                    ${this.fileRow(path, file, true)}
                  </div>`;
                })}
              </div>`
            : html`<div>
                ${group.files.map((file) => {
                  const path = this.path(group, file.name);
                  const url = this.previewUrl(path);
                  return html`<div class="sound">
                    ${this.fileRow(path, file, true)}
                    ${
                      url
                        ? html`<audio
                            controls
                            preload="none"
                            src=${url}
                          ></audio>`
                        : nothing
                    }
                  </div>`;
                })}
              </div>`
      }
      <dm-upload-form
        .t=${t}
        .api=${this.api}
        .target=${(name: string) => this.path(group, name)}
        accept=${ACCEPT[group.kind]}
        .sizeMb=${SIZE_MB[group.kind]}
        @dm-uploaded=${(e: CustomEvent) => this.uploaded(e)}
      ></dm-upload-form>
    </section>`;
  }

  private async create() {
    const name = this.newName.trim();
    if (!name || this.creating) return;
    this.creating = true;
    try {
      const group = await this.api.call<{ name: string }>(
        "POST",
        ["media-groups"],
        { name, kind: this.newKind },
      );
      this.newName = "";
      this.toast(fill(this.t.createdName, { name: group.name }));
      await this.load(true);
    } catch (err) {
      this.fail(err);
    } finally {
      this.creating = false;
    }
  }

  private async renameGroup(group: MediaGroupListing, name: string) {
    this.groupBusy = true;
    try {
      await this.api.call("PATCH", ["media-groups", group.id], { name });
      this.renamingGroup = undefined;
      await this.load(true);
    } catch (err) {
      this.fail(err);
    } finally {
      this.groupBusy = false;
    }
  }

  private async deleteGroup(group: MediaGroupListing) {
    try {
      await this.api.call("DELETE", ["media-groups", group.id]);
      this.toast(fill(this.t.deletedName, { name: group.name }));
      await this.load(true);
    } catch (err) {
      this.fail(err);
    }
  }
}

if (!customElements.get("dm-media-tab"))
  customElements.define("dm-media-tab", MediaTab);
