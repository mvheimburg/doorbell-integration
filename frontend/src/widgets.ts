/** Small shared pieces: the inline rename form and the upload form. */

import { LitElement, html, nothing, type PropertyValues } from "lit";
import { AdminApi, toApiError, type MediaPath, type ApiError } from "./api";
import { icon } from "./icons";
import { fill, type Strings } from "./localize";
import { styles } from "./styles";

/**
 * An inline text field with Save name / Cancel. Enter saves, Escape cancels; saving is disabled
 * while the trimmed text is empty. Fires ``dm-save`` (the trimmed text) and ``dm-cancel``.
 */
export class RenameForm extends LitElement {
  static styles = styles;
  static properties = {
    t: { attribute: false },
    value: {},
    suffix: {},
    maxLength: { type: Number },
    busy: { type: Boolean },
    label: {},
    text: { state: true },
  };

  t!: Strings;
  value = "";
  suffix = "";
  maxLength = 100;
  busy = false;
  label = "";
  text = "";

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("value")) this.text = this.value;
  }

  protected firstUpdated(): void {
    const input = this.renderRoot.querySelector("input");
    input?.focus();
    input?.select();
  }

  private save() {
    const name = this.text.trim();
    if (!name || this.busy) return;
    this.dispatchEvent(new CustomEvent("dm-save", { detail: name }));
  }

  protected render() {
    const t = this.t;
    return html`<div class="rename">
      <input
        type="text"
        aria-label=${this.label || t.newName}
        maxlength=${this.maxLength}
        .value=${this.text}
        ?disabled=${this.busy}
        @input=${(e: Event) => (this.text = (e.target as HTMLInputElement).value)}
        @keydown=${(e: KeyboardEvent) => {
          if (e.key === "Enter") this.save();
          if (e.key === "Escape")
            this.dispatchEvent(new CustomEvent("dm-cancel"));
        }}
      />
      ${this.suffix ? html`<span class="ext">${this.suffix}</span>` : nothing}
      <button
        class="icon-btn"
        data-action="save-name"
        aria-label=${t.saveName}
        title=${t.saveName}
        ?disabled=${!this.text.trim() || this.busy}
        @click=${() => this.save()}
      >
        ${this.busy ? icon("spinner", "s spin") : icon("check", "s")}
      </button>
      <button
        class="icon-btn"
        data-action="cancel-name"
        aria-label=${t.cancel}
        title=${t.cancel}
        ?disabled=${this.busy}
        @click=${() => this.dispatchEvent(new CustomEvent("dm-cancel"))}
      >
        ${icon("close", "s")}
      </button>
    </div>`;
  }
}

/**
 * "Replace files with the same name", a multi-file picker and Upload. Files are sent one after
 * another; it fires ``dm-uploaded`` with the stored names, and the error that stopped it.
 */
export class UploadForm extends LitElement {
  static styles = styles;
  static properties = {
    t: { attribute: false },
    api: { attribute: false },
    target: { attribute: false },
    accept: {},
    sizeMb: { type: Number },
    files: { state: true },
    overwrite: { state: true },
    busy: { state: true },
  };

  t!: Strings;
  api!: AdminApi;
  /** Where a file of this name goes. */
  target!: (name: string) => MediaPath;
  accept = "";
  sizeMb = 25;
  files: File[] = [];
  overwrite = false;
  busy = false;

  private async upload() {
    const names: string[] = [];
    let error: ApiError | undefined;
    this.busy = true;
    for (const file of this.files) {
      try {
        names.push(
          await this.api.upload(this.target(file.name), file, this.overwrite),
        );
      } catch (err) {
        error = toApiError(err);
        break;
      }
    }
    this.busy = false;
    this.files = [];
    const input =
      this.renderRoot.querySelector<HTMLInputElement>('input[type="file"]');
    if (input) input.value = "";
    this.dispatchEvent(
      new CustomEvent("dm-uploaded", { detail: { names, error } }),
    );
  }

  protected render() {
    const t = this.t;
    return html`<div class="upload">
      <div class="line">
        <label class="check">
          <input
            type="checkbox"
            data-field="overwrite"
            .checked=${this.overwrite}
            ?disabled=${this.busy}
            @change=${(e: Event) =>
              (this.overwrite = (e.target as HTMLInputElement).checked)}
          />
          ${t.replace}
        </label>
        <input
          type="file"
          multiple
          accept=${this.accept}
          aria-label=${t.chooseFiles}
          ?disabled=${this.busy}
          @change=${(e: Event) =>
            (this.files = [...((e.target as HTMLInputElement).files ?? [])])}
        />
        <button
          class="btn primary"
          data-action="upload"
          ?disabled=${!this.files.length || this.busy}
          @click=${() => this.upload()}
        >
          ${this.busy ? icon("spinner", "s spin") : icon("upload", "s")}
          ${t.upload}
        </button>
      </div>
      <p class="note">${fill(t.sizeNote, { n: this.sizeMb })}</p>
    </div>`;
  }
}

if (!customElements.get("dm-rename-form"))
  customElements.define("dm-rename-form", RenameForm);
if (!customElements.get("dm-upload-form"))
  customElements.define("dm-upload-form", UploadForm);
