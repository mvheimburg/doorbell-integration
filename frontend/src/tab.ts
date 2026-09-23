import { LitElement, html, nothing, type TemplateResult } from "lit";
import {
  AdminApi,
  ApiError,
  FATAL_CODES,
  toApiError,
  type MediaPath,
} from "./api";
import { formatSize, splitExtension } from "./format";
import { icon } from "./icons";
import { errorMessage, fill, type Strings } from "./localize";
import { styles } from "./styles";
import type { MediaFile, PanelInfo } from "./types";
import "./widgets";

export interface Confirm {
  title: string;
  lines: string[];
  run: () => Promise<void>;
}

/**
 * One tab: loads its data, shows a spinner or a retryable alert, and reports toasts and
 * page-level failures (a lost admin, a refused token) to the panel as events.
 */
export abstract class Tab extends LitElement {
  static styles = styles;
  static properties = {
    api: { attribute: false },
    t: { attribute: false },
    locale: { attribute: false },
    info: { attribute: false },
    loading: { state: true },
    loadError: { state: true },
    confirm: { state: true },
    confirming: { state: true },
    renaming: { state: true },
    renameBusy: { state: true },
    urls: { state: true },
  };

  api!: AdminApi;
  t!: Strings;
  locale = "en";
  info!: PanelInfo;
  loading = true;
  loadError?: string;
  confirm?: Confirm;
  confirming = false;
  /** Media URL of the file whose name is being edited. */
  renaming?: string;
  renameBusy = false;
  /** Signed preview URL per media URL. */
  urls: Record<string, string> = {};
  private loaded?: AdminApi;

  protected abstract fetch(): Promise<void>;
  protected abstract renderContent(): TemplateResult;

  protected willUpdate(): void {
    if (this.api && this.api !== this.loaded) {
      this.loaded = this.api;
      void this.load();
    }
  }

  /** Fetch again. ``quiet`` keeps what is shown while it loads (after a write). */
  async load(quiet = false): Promise<void> {
    if (!quiet) this.loading = true;
    this.loadError = undefined;
    try {
      await this.fetch();
    } catch (err) {
      const error = toApiError(err);
      if (FATAL_CODES.has(error.code)) this.fatal(error);
      else this.loadError = errorMessage(this.t, error);
    } finally {
      this.loading = false;
    }
  }

  protected toast(text: string): void {
    this.dispatchEvent(
      new CustomEvent("dm-toast", {
        detail: text,
        bubbles: true,
        composed: true,
      }),
    );
  }

  private fatal(error: ApiError): void {
    this.dispatchEvent(
      new CustomEvent("dm-fatal", {
        detail: error,
        bubbles: true,
        composed: true,
      }),
    );
  }

  /** A failed action: a toast, unless the whole panel can no longer work. */
  protected fail(err: unknown): void {
    const error = toApiError(err);
    if (FATAL_CODES.has(error.code)) this.fatal(error);
    else
      this.toast(fill(this.t.failed, { message: errorMessage(this.t, error) }));
  }

  /** The panel's message for an action shown inline (a form), or ``undefined`` if fatal. */
  protected inlineError(err: unknown): string | undefined {
    const error = toApiError(err);
    if (FATAL_CODES.has(error.code)) {
      this.fatal(error);
      return undefined;
    }
    return errorMessage(this.t, error);
  }

  protected render(): TemplateResult {
    const t = this.t;
    return html`${
      this.loading
        ? html`<div class="center" role="status" aria-label=${t.loading}>
            ${icon("spinner", "spin")}
          </div>`
        : this.loadError !== undefined
          ? html`<div class="alert" role="alert">
              ${icon("warning")}
              <span class="grow"
                >${fill(t.couldNotLoad, { message: this.loadError })}</span
              >
              <button
                class="btn"
                data-action="retry"
                @click=${() => this.load()}
              >
                ${t.retry}
              </button>
            </div>`
          : this.renderContent()
    }
    ${this.renderConfirm()}`;
  }

  // -- confirmations -------------------------------------------------------

  protected ask(confirm: Confirm): void {
    this.confirm = confirm;
  }

  private renderConfirm() {
    const confirm = this.confirm;
    if (!confirm) return nothing;
    const t = this.t;
    const close = () => {
      if (!this.confirming) this.confirm = undefined;
    };
    return html`<div class="scrim">
      <div
        class="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        @keydown=${(e: KeyboardEvent) => e.key === "Escape" && close()}
      >
        <h2 id="confirm-title">${confirm.title}</h2>
        ${confirm.lines.map((line) => html`<p>${line}</p>`)}
        <div class="dialog-actions">
          <button
            class="btn"
            data-action="cancel"
            ?disabled=${this.confirming}
            @click=${close}
          >
            ${t.cancel}
          </button>
          <button
            class="btn danger"
            data-action="confirm"
            ?disabled=${this.confirming}
            @click=${async () => {
              this.confirming = true;
              try {
                await confirm.run();
              } finally {
                this.confirming = false;
                this.confirm = undefined;
              }
            }}
          >
            ${this.confirming ? icon("spinner", "s spin") : nothing}${t.delete}
          </button>
        </div>
      </div>
    </div>`;
  }

  // -- media files ---------------------------------------------------------

  /** Sign every preview URL; a file whose URL can't be signed shows no preview. */
  protected async signAll(paths: MediaPath[]): Promise<void> {
    const entries = await Promise.all(
      paths.map(async (path) => {
        try {
          return [this.api.mediaUrl(path), await this.api.signedUrl(path)];
        } catch {
          return [this.api.mediaUrl(path), ""];
        }
      }),
    );
    this.urls = Object.fromEntries(entries);
  }

  protected previewUrl(path: MediaPath): string | undefined {
    return this.urls[this.api.mediaUrl(path)] || undefined;
  }

  /** Name, size, and rename and delete buttons; or the rename form in its place. */
  protected fileRow(
    path: MediaPath,
    file: MediaFile,
    showSize: boolean,
  ): TemplateResult {
    const t = this.t;
    const key = this.api.mediaUrl(path);
    if (this.renaming === key) {
      const [base, ext] = splitExtension(file.name);
      return html`<dm-rename-form
        class="file-row"
        .t=${t}
        .value=${base}
        .suffix=${ext}
        .maxLength=${100}
        .busy=${this.renameBusy}
        @dm-save=${(e: CustomEvent<string>) =>
          this.renameFile(path, e.detail + ext)}
        @dm-cancel=${() => (this.renaming = undefined)}
      ></dm-rename-form>`;
    }
    return html`<div class="file-row" data-file=${file.name}>
      <span class="fname" title=${file.name}>${file.name}</span>
      ${
        showSize
          ? html`<span class="size"
              >${formatSize(file.size, this.locale)}</span
            >`
          : nothing
      }
      <button
        class="icon-btn"
        data-action="rename-file"
        aria-label=${fill(t.rename, { name: file.name })}
        title=${fill(t.rename, { name: file.name })}
        @click=${() => (this.renaming = key)}
      >
        ${icon("pencil", "s")}
      </button>
      <button
        class="icon-btn danger"
        data-action="delete-file"
        aria-label=${fill(t.deleteName, { name: file.name })}
        title=${fill(t.deleteName, { name: file.name })}
        @click=${() =>
          this.ask({
            title: fill(t.deleteTitle, { name: file.name }),
            lines: [t.cannotUndo],
            run: () => this.deleteFile(path, file.name),
          })}
      >
        ${icon("trash", "s")}
      </button>
    </div>`;
  }

  private async renameFile(path: MediaPath, name: string): Promise<void> {
    this.renameBusy = true;
    try {
      const result = await this.api.call<{ name: string }>(
        "PATCH",
        ["media", ...path],
        {
          name,
        },
      );
      this.renaming = undefined;
      if (result.name !== name)
        this.toast(fill(this.t.renamedTo, { name: result.name }));
      await this.load(true);
    } catch (err) {
      this.fail(err);
    } finally {
      this.renameBusy = false;
    }
  }

  private async deleteFile(path: MediaPath, name: string): Promise<void> {
    try {
      await this.api.call("DELETE", ["media", ...path]);
      this.toast(fill(this.t.deletedName, { name }));
      await this.load(true);
    } catch (err) {
      this.fail(err);
    }
  }

  /** After an upload: what arrived, and the error that stopped it, if any. */
  protected async uploaded(
    e: CustomEvent<{ names: string[]; error?: ApiError }>,
  ): Promise<void> {
    const { names, error } = e.detail;
    if (!error) {
      this.toast(fill(this.t.uploaded, { names: names.join(", ") }));
    } else if (FATAL_CODES.has(error.code)) {
      this.fail(error);
      return;
    } else {
      const message = errorMessage(this.t, error);
      this.toast(
        names.length
          ? fill(this.t.failedAfter, { message, names: names.join(", ") })
          : fill(this.t.failed, { message }),
      );
    }
    await this.load(true);
  }
}
