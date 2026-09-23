import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { AdminApi, ApiError, toApiError } from "./api";
import { icon } from "./icons";
import {
  errorMessage,
  fill,
  formattingLocale,
  localize,
  type Strings,
} from "./localize";
import { styles } from "./styles";
import type { HomeAssistant, InfoResponse } from "./types";
import "./users-tab";
import "./appearance-tab";
import "./media-tab";
import "./photos-tab";

/** The tabs, in order, each shown only when the panel lists its feature. */
export const TABS = ["users", "appearance", "media-groups", "photos"] as const;
export type TabId = (typeof TABS)[number];

const TOAST_MS = 2200;
const SETTINGS_PATH = "/config/integrations/integration/doormonitor";

/** A state the whole page shows instead of the tabs. */
type PageState =
  | { kind: "no-entries" }
  | { kind: "not-configured" }
  | { kind: "not-admin" }
  | { kind: "bad-token" };

export class DoorMonitorAdminPanel extends LitElement {
  static styles = [
    styles,
    css`
      :host {
        min-height: 100%;
        background: var(--primary-background-color);
      }
      .bar {
        position: sticky;
        top: 0;
        z-index: 2;
        background: var(
          --app-header-background-color,
          var(--primary-background-color)
        );
        color: var(--app-header-text-color, var(--primary-text-color));
        border-bottom: 1px solid var(--dm-line);
      }
      .bar-top {
        display: flex;
        align-items: center;
        gap: 10px;
        min-height: 56px;
        padding: 0 12px 0 16px;
        max-width: 1048px;
        margin: 0 auto;
      }
      .bar-top h1 {
        font-size: 1.25rem;
        font-weight: 500;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;
      }
      .bar .icon-btn {
        color: inherit;
      }
      .acting {
        color: var(--dm-muted);
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      :host([narrow]) .acting {
        display: none;
      }
      .bar select {
        width: auto;
        max-width: 40vw;
      }
      .cog {
        width: 44px;
        height: 44px;
      }
      nav {
        display: flex;
        gap: 4px;
        overflow-x: auto;
        max-width: 1048px;
        margin: 0 auto;
        padding: 0 12px;
      }
      nav button {
        font: inherit;
        color: var(--dm-muted);
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 12px;
        cursor: pointer;
        white-space: nowrap;
      }
      nav button[aria-selected="true"] {
        color: var(--dm-text);
        border-bottom-color: var(--dm-accent);
      }
      main {
        max-width: 1048px;
        margin: 0 auto;
        padding: 16px 24px 96px;
      }
      :host([narrow]) main {
        padding: 12px 12px 96px;
      }
      .page {
        max-width: 560px;
        margin: 32px auto;
      }
      .page h2 {
        margin: 0 0 8px;
        font-size: 1.2rem;
      }
      .page p {
        line-height: 1.5;
        color: var(--dm-muted);
      }
      .toast {
        position: fixed;
        left: 50%;
        bottom: 24px;
        transform: translateX(-50%);
        z-index: 20;
        background: var(--dm-text);
        color: var(--primary-background-color, #fff);
        padding: 10px 18px;
        border-radius: 999px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
        max-width: calc(100vw - 32px);
      }
    `,
  ];

  static properties = {
    hass: { attribute: false },
    narrow: { type: Boolean, reflect: true },
    route: { attribute: false },
    panel: { attribute: false },
    info: { state: true },
    loading: { state: true },
    loadError: { state: true },
    page: { state: true },
    tab: { state: true },
    toastText: { state: true },
    api: { state: true },
  };

  hass?: HomeAssistant;
  narrow = false;
  route?: unknown;
  panel?: unknown;
  info?: InfoResponse;
  loading = true;
  loadError?: string;
  page?: PageState;
  tab?: TabId;
  toastText?: string;
  api?: AdminApi;
  private toastTimer?: number;
  private started = false;

  private get t(): Strings {
    return localize(this.hass);
  }

  private get tabs(): TabId[] {
    const features = this.info?.info?.features ?? [];
    return TABS.filter((tab) => features.includes(tab));
  }

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass) {
      if (this.api) this.api.hass = this.hass;
      if (!this.started) {
        this.started = true;
        void this.loadInfo();
      }
    }
  }

  /** Read the entry and the panel's ``GET /info``, afresh, so the tabs match the panel now. */
  async loadInfo(entryId?: string): Promise<void> {
    this.loading = true;
    this.loadError = undefined;
    this.page = undefined;
    try {
      const info = await this.hass!.callWS<InfoResponse>({
        type: "doormonitor/admin/info",
        ...(entryId ? { entry_id: entryId } : {}),
      });
      this.info = info;
      if (!info.entry_id) {
        this.page = { kind: "no-entries" };
      } else if (!info.configured) {
        this.page = { kind: "not-configured" };
      } else if (info.error) {
        this.onError(new ApiError(info.error.message, info.error.code));
      } else {
        if (this.api?.entryId !== info.entry_id)
          this.api = new AdminApi(this.hass!, info.entry_id);
        if (!this.tab || !this.tabs.includes(this.tab)) this.tab = this.tabs[0];
      }
    } catch (err) {
      this.loadError = errorMessage(this.t, toApiError(err));
    } finally {
      this.loading = false;
    }
  }

  private onError(error: ApiError) {
    if (error.code === "not-admin") this.page = { kind: "not-admin" };
    else if (error.code === "bad-token") this.page = { kind: "bad-token" };
    else if (error.code === "not-configured")
      this.page = { kind: "not-configured" };
    else this.loadError = errorMessage(this.t, error);
  }

  private showToast(text: string) {
    this.toastText = text;
    window.clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(
      () => (this.toastText = undefined),
      TOAST_MS,
    );
  }

  private openSettings() {
    history.pushState(null, "", SETTINGS_PATH);
    window.dispatchEvent(
      new CustomEvent("location-changed", { detail: { replace: false } }),
    );
  }

  private toggleMenu() {
    this.dispatchEvent(
      new Event("hass-toggle-menu", { bubbles: true, composed: true }),
    );
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.clearTimeout(this.toastTimer);
  }

  protected render() {
    const t = this.t;
    return html`${this.renderBar()}
      <main
        @dm-toast=${(e: CustomEvent<string>) => this.showToast(e.detail)}
        @dm-fatal=${(e: CustomEvent<ApiError>) => this.onError(e.detail)}
      >
        ${
          this.loading
            ? html`<div class="center" role="status" aria-label=${t.loading}>
                ${icon("spinner", "spin")}
              </div>`
            : this.page
              ? this.renderPage(this.page)
              : this.loadError !== undefined
                ? html`<div class="alert" role="alert">
                    ${icon("warning")}
                    <span class="grow"
                      >${fill(t.couldNotLoad, { message: this.loadError })}</span
                    >
                    <button
                      class="btn"
                      data-action="retry"
                      @click=${() => this.loadInfo(this.info?.entry_id)}
                    >
                      ${t.retry}
                    </button>
                  </div>`
                : this.renderTab()
        }
      </main>
      ${
        this.toastText
          ? html`<div class="toast" role="status" aria-live="polite">
              ${this.toastText}
            </div>`
          : nothing
      }`;
  }

  private renderBar() {
    const t = this.t;
    const entries = this.info?.entries ?? [];
    const showTabs =
      !this.loading && !this.page && this.loadError === undefined;
    return html`<header class="bar">
      <div class="bar-top">
        ${
          this.narrow
            ? html`<button
                class="icon-btn"
                aria-label=${t.menu}
                @click=${this.toggleMenu}
              >
                ${icon("menu")}
              </button>`
            : nothing
        }
        <h1>${icon("bell")}<span>${t.title}</span></h1>
        ${
          entries.length > 1
            ? html`<select
                aria-label=${t.entry}
                data-field="entry"
                .value=${this.info?.entry_id ?? ""}
                @change=${(e: Event) =>
                  this.loadInfo((e.target as HTMLSelectElement).value)}
              >
                ${entries.map(
                  (entry) =>
                    html`<option
                      value=${entry.entry_id}
                      ?selected=${entry.entry_id === this.info?.entry_id}
                    >
                      ${entry.title}
                    </option>`,
                )}
              </select>`
            : nothing
        }
        ${
          this.info?.actor_name && showTabs
            ? html`<span class="acting"
                >${fill(t.actingAs, { name: this.info.actor_name })}</span
              >`
            : nothing
        }
        <button
          class="icon-btn cog"
          data-action="settings"
          aria-label=${t.settings}
          title=${t.settings}
          @click=${this.openSettings}
        >
          ${icon("cog")}
        </button>
      </div>
      ${
        showTabs && this.tabs.length
          ? html`<nav role="tablist">
              ${this.tabs.map(
                (tab) =>
                  html`<button
                    role="tab"
                    data-tab=${tab}
                    aria-selected=${tab === this.tab ? "true" : "false"}
                    @click=${() => (this.tab = tab)}
                  >
                    ${t.tabs[tab]}
                  </button>`,
              )}
            </nav>`
          : nothing
      }
    </header>`;
  }

  private renderPage(page: PageState) {
    const t = this.t;
    const [title, body] = {
      "no-entries": [t.notSetUpTitle, t.notSetUpBody],
      "not-configured": [t.notConfiguredTitle, t.notConfiguredBody],
      "not-admin": [
        t.notAdminTitle,
        fill(t.notAdminBody, { name: this.info?.actor_name || "–" }),
      ],
      "bad-token": [t.badTokenTitle, t.badTokenBody],
    }[page.kind];
    return html`<section class="card page" data-page=${page.kind}>
      <h2>${title}</h2>
      <p>${body}</p>
      ${
        page.kind === "no-entries"
          ? nothing
          : html`<button class="btn primary" @click=${this.openSettings}>
              ${icon("cog", "s")}${t.openSettings}
            </button>`
      }
    </section>`;
  }

  private renderTab() {
    const t = this.t;
    if (!this.tabs.length)
      return html`<p class="muted" data-page="no-features">${t.noFeatures}</p>`;
    const props = {
      api: this.api,
      t,
      locale: formattingLocale(this.hass),
      info: this.info!.info,
    };
    switch (this.tab) {
      case "users":
        return html`<dm-users-tab
          .api=${props.api}
          .t=${props.t}
          .locale=${props.locale}
          .info=${props.info}
        ></dm-users-tab>`;
      case "appearance":
        return html`<dm-appearance-tab
          .api=${props.api}
          .t=${props.t}
          .locale=${props.locale}
          .info=${props.info}
        ></dm-appearance-tab>`;
      case "media-groups":
        return html`<dm-media-tab
          .api=${props.api}
          .t=${props.t}
          .locale=${props.locale}
          .info=${props.info}
        ></dm-media-tab>`;
      case "photos":
        return html`<dm-photos-tab
          .api=${props.api}
          .t=${props.t}
          .locale=${props.locale}
          .info=${props.info}
        ></dm-photos-tab>`;
      default:
        return nothing;
    }
  }
}

if (!customElements.get("doormonitor-admin-panel"))
  customElements.define("doormonitor-admin-panel", DoorMonitorAdminPanel);
