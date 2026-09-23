import { html, nothing, type TemplateResult } from "lit";
import { dateInput, midnightUtc, today } from "./format";
import { icon } from "./icons";
import { fill } from "./localize";
import { Tab } from "./tab";
import type {
  AccessLevel,
  BleId,
  BleKind,
  BleSlot,
  HaUser,
  UserRecord,
} from "./types";

const LEVELS: AccessLevel[] = ["guest", "resident", "admin"];
const SLOTS: BleSlot[] = ["phone", "watch", "misc"];
const KINDS: BleKind[] = ["ibeacon", "mac", "uuid"];

/** The user form's fields, as typed. */
interface Draft {
  id: string | null;
  name: string;
  pin: string;
  accessLevel: AccessLevel;
  start: string;
  end: string;
  ble: Record<BleSlot, { kind: BleKind; value: string }>;
  haUser: string;
  /** The stored start, kept when the date field is left empty. */
  storedStart: string | null;
}

function draftFor(user: UserRecord | null, haUser: string): Draft {
  const ble = Object.fromEntries(
    SLOTS.map((slot) => {
      const id: BleId | null | undefined = user?.bleData?.[slot];
      return [slot, { kind: id?.kind ?? "ibeacon", value: id?.value ?? "" }];
    }),
  ) as Draft["ble"];
  return user
    ? {
        id: user.id,
        name: user.name,
        pin: user.pin,
        accessLevel: user.accessLevel,
        start: dateInput(user.start),
        end: dateInput(user.end),
        ble,
        haUser,
        storedStart: user.start,
      }
    : {
        id: null,
        name: "",
        pin: "0000",
        accessLevel: "resident",
        start: today(),
        end: "",
        ble,
        haUser: "",
        storedStart: null,
      };
}

export class UsersTab extends Tab {
  static properties = {
    ...Tab.properties,
    users: { state: true },
    haUsers: { state: true },
    links: { state: true },
    draft: { state: true },
    formError: { state: true },
    saving: { state: true },
  };

  users: UserRecord[] = [];
  haUsers: HaUser[] = [];
  links: Record<string, string> = {};
  draft?: Draft;
  formError?: string;
  saving = false;

  protected async fetch(): Promise<void> {
    const result = await this.api.users();
    this.users = result.users;
    this.haUsers = result.ha_users;
    this.links = result.links;
  }

  private haUserName(id: string | undefined): string | undefined {
    return id ? this.haUsers.find((user) => user.id === id)?.name : undefined;
  }

  protected renderContent(): TemplateResult {
    const t = this.t;
    return html`<section class="card">
        <div class="card-head">
          <h2>${icon("users")}<span>${t.users}</span></h2>
          <button
            class="btn primary"
            data-action="add-user"
            @click=${() => this.open(null)}
          >
            ${icon("userPlus", "s")}${t.addUser}
          </button>
        </div>
        <ul class="rows">
          ${this.users.map((user) => this.renderUser(user))}
        </ul>
      </section>
      ${this.renderForm()}`;
  }

  private renderUser(user: UserRecord) {
    const t = this.t;
    const linked = this.haUserName(this.links[user.id]);
    const isRoot = user.name === this.info.rootName;
    return html`<li
      class="row ${user.isActive === false ? "inactive" : ""}"
      data-user=${user.id}
      title=${user.isActive === false ? t.inactive : nothing}
    >
      <div class="who">
        <span class="name">${user.name}</span>
        ${
          linked
            ? html`<span class="sub" data-linked
                >${icon("link", "s")}${fill(t.linkedTo, { name: linked })}</span
              >`
            : nothing
        }
      </div>
      <span class="badge ${user.accessLevel}" data-badge
        >${t.access[user.accessLevel] ?? user.accessLevel}</span
      >
      <button
        class="icon-btn"
        data-action="edit"
        aria-label=${fill(t.editName, { name: user.name })}
        title=${fill(t.editName, { name: user.name })}
        @click=${() => this.open(user)}
      >
        ${icon("pencil", "s")}
      </button>
      ${
        isRoot
          ? html`<span class="icon-btn spacer" aria-hidden="true"></span>`
          : html`<button
              class="icon-btn danger"
              data-action="delete"
              aria-label=${fill(t.deleteName, { name: user.name })}
              title=${fill(t.deleteName, { name: user.name })}
              @click=${() =>
                this.ask({
                  title: fill(t.deleteTitle, { name: user.name }),
                  lines: [t.cannotUndo],
                  run: () => this.deleteUser(user),
                })}
            >
              ${icon("trash", "s")}
            </button>`
      }
    </li>`;
  }

  private open(user: UserRecord | null) {
    this.formError = undefined;
    this.draft = draftFor(user, user ? (this.links[user.id] ?? "") : "");
  }

  private setDraft(patch: Partial<Draft>) {
    if (this.draft) this.draft = { ...this.draft, ...patch };
  }

  /** Picking a Home Assistant user fills the name, unless one was typed. */
  private pickHaUser(id: string) {
    const draft = this.draft!;
    const previous = this.haUserName(draft.haUser) ?? "";
    const name =
      !draft.name.trim() || draft.name === previous
        ? (this.haUserName(id) ?? draft.name)
        : draft.name;
    this.setDraft({ haUser: id, name });
  }

  private renderForm() {
    const draft = this.draft;
    if (!draft) return nothing;
    const t = this.t;
    const taken = new Set(
      Object.entries(this.links)
        .filter(([doorbellId]) => doorbellId !== draft.id)
        .map(([, haUser]) => haUser),
    );
    return html`<div class="scrim">
      <div
        class="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-title"
      >
        <h2 id="user-title">${draft.id ? t.editUser : t.addUser}</h2>
        ${
          this.formError
            ? html`<div class="alert" role="alert">
                ${icon("warning")}<span class="grow">${this.formError}</span>
              </div>`
            : nothing
        }
        <form
          class="form"
          @submit=${(e: Event) => {
            e.preventDefault();
            void this.save();
          }}
        >
          <label class="field wide">
            ${t.haUser}
            <select
              data-field="haUser"
              ?disabled=${this.saving}
              @change=${(e: Event) =>
                this.pickHaUser((e.target as HTMLSelectElement).value)}
            >
              <option value="" ?selected=${!draft.haUser}>
                ${t.haUserNone}
              </option>
              ${this.haUsers
                .filter((user) => !taken.has(user.id))
                .map(
                  (user) =>
                    html`<option
                      value=${user.id}
                      ?selected=${user.id === draft.haUser}
                    >
                      ${user.name}
                    </option>`,
                )}
            </select>
            <span class="hint">${t.haUserHint}</span>
          </label>
          <label class="field">
            ${t.name}
            <input
              type="text"
              data-field="name"
              .value=${draft.name}
              ?disabled=${this.saving}
              @input=${(e: Event) =>
                this.setDraft({ name: (e.target as HTMLInputElement).value })}
            />
          </label>
          <label class="field">
            ${t.pin}
            <input
              type="text"
              data-field="pin"
              inputmode="numeric"
              autocomplete="off"
              maxlength="4"
              .value=${draft.pin}
              ?disabled=${this.saving}
              @input=${(e: Event) => {
                const input = e.target as HTMLInputElement;
                input.value = input.value.replace(/\D/g, "").slice(0, 4);
                this.setDraft({ pin: input.value });
              }}
            />
          </label>
          <label class="field">
            ${t.accessLevel}
            <select
              data-field="accessLevel"
              ?disabled=${this.saving}
              @change=${(e: Event) =>
                this.setDraft({
                  accessLevel: (e.target as HTMLSelectElement)
                    .value as AccessLevel,
                })}
            >
              ${LEVELS.map(
                (level) =>
                  html`<option
                    value=${level}
                    ?selected=${level === draft.accessLevel}
                  >
                    ${t.accessOption[level]}
                  </option>`,
              )}
            </select>
          </label>
          <span></span>
          <label class="field">
            ${t.activeFrom}
            <input
              type="date"
              data-field="start"
              .value=${draft.start}
              ?disabled=${this.saving}
              @change=${(e: Event) =>
                this.setDraft({ start: (e.target as HTMLInputElement).value })}
            />
          </label>
          <label class="field">
            ${t.activeUntil}
            <input
              type="date"
              data-field="end"
              .value=${draft.end}
              ?disabled=${this.saving}
              @change=${(e: Event) =>
                this.setDraft({ end: (e.target as HTMLInputElement).value })}
            />
          </label>
          ${SLOTS.map((slot) => this.renderBle(slot))}
          <button type="submit" hidden></button>
        </form>
        <div class="dialog-actions">
          <button
            class="btn"
            data-action="cancel"
            ?disabled=${this.saving}
            @click=${() => (this.draft = undefined)}
          >
            ${t.cancel}
          </button>
          <button
            class="btn primary"
            data-action="save"
            ?disabled=${this.saving}
            @click=${() => this.save()}
          >
            ${this.saving ? icon("spinner", "s spin") : nothing}${t.save}
          </button>
        </div>
      </div>
    </div>`;
  }

  private renderBle(slot: BleSlot) {
    const t = this.t;
    const value = this.draft!.ble[slot];
    const set = (patch: Partial<typeof value>) =>
      this.setDraft({
        ble: { ...this.draft!.ble, [slot]: { ...value, ...patch } },
      });
    return html`<div class="field wide">
      <label class="field" for="ble-${slot}">${t.ble[slot]}</label>
      <div class="ble">
        <select
          data-field="ble-${slot}-kind"
          aria-label=${fill(t.bleKindLabel, { slot: t.ble[slot] })}
          ?disabled=${this.saving}
          @change=${(e: Event) =>
            set({ kind: (e.target as HTMLSelectElement).value as BleKind })}
        >
          ${KINDS.map(
            (kind) =>
              html`<option value=${kind} ?selected=${kind === value.kind}>
                ${t.bleKind[kind]}
              </option>`,
          )}
        </select>
        <input
          id="ble-${slot}"
          type="text"
          data-field="ble-${slot}"
          .value=${value.value}
          ?disabled=${this.saving}
          @input=${(e: Event) =>
            set({ value: (e.target as HTMLInputElement).value })}
        />
      </div>
    </div>`;
  }

  /** The record the panel gets; it checks everything but the input masks. */
  private record(draft: Draft): Omit<UserRecord, "id"> {
    const bleData = Object.fromEntries(
      SLOTS.map((slot) => {
        const value = draft.ble[slot].value.trim();
        return [slot, value ? { kind: draft.ble[slot].kind, value } : null];
      }),
    ) as UserRecord["bleData"];
    return {
      name: draft.name,
      pin: draft.pin,
      accessLevel: draft.accessLevel,
      start: draft.start
        ? midnightUtc(draft.start)
        : (draft.storedStart ?? midnightUtc(today())),
      end: draft.end ? midnightUtc(draft.end) : null,
      bleData,
    };
  }

  private async save() {
    const draft = this.draft;
    if (!draft || this.saving) return;
    this.saving = true;
    this.formError = undefined;
    try {
      const stored = await this.api.saveUser(
        draft.id,
        this.record(draft),
        draft.haUser || null,
      );
      this.draft = undefined;
      this.toast(fill(this.t.savedName, { name: stored.name }));
      await this.load(true);
    } catch (err) {
      const message = this.inlineError(err);
      if (message === undefined) this.draft = undefined;
      else this.formError = message;
    } finally {
      this.saving = false;
    }
  }

  private async deleteUser(user: UserRecord) {
    try {
      await this.api.call("DELETE", ["users", user.id]);
      this.toast(fill(this.t.deletedName, { name: user.name }));
      await this.load(true);
    } catch (err) {
      this.fail(err);
    }
  }
}

if (!customElements.get("dm-users-tab"))
  customElements.define("dm-users-tab", UsersTab);
