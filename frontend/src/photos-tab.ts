import { html, nothing, type TemplateResult } from "lit";
import type { MediaPath } from "./api";
import { icon } from "./icons";
import { Tab } from "./tab";
import type { MediaFile, MediaResponse } from "./types";

const path = (name: string): MediaPath => ["photos", name];

export class PhotosTab extends Tab {
  static properties = { ...Tab.properties, photos: { state: true } };

  photos: MediaFile[] = [];

  protected async fetch(): Promise<void> {
    const media = await this.api.call<MediaResponse>("GET", ["media"]);
    this.photos = media.photos;
    await this.signAll(media.photos.map((photo) => path(photo.name)));
  }

  protected renderContent(): TemplateResult {
    const t = this.t;
    return html`<section class="card">
      <div class="card-head">
        <h2>${icon("image")}<span>${t.photosTitle}</span></h2>
      </div>
      <p class="intro">${t.photosIntro}</p>
      ${
        this.photos.length
          ? html`<div class="grid photos">
              ${this.photos.map((photo) => {
                const url = this.previewUrl(path(photo.name));
                return html`<div class="photo">
                  ${
                    url
                      ? html`<img
                          src=${url}
                          alt=${photo.name}
                          loading="lazy"
                        />`
                      : nothing
                  }
                  ${this.fileRow(path(photo.name), photo, false)}
                </div>`;
              })}
            </div>`
          : html`<p class="muted" data-empty>${t.noPhotos}</p>`
      }
      <dm-upload-form
        .t=${t}
        .api=${this.api}
        .target=${path}
        accept=".gif,.jpeg,.jpg,.png,.webp"
        .sizeMb=${25}
        @dm-uploaded=${(e: CustomEvent) => this.uploaded(e)}
      ></dm-upload-form>
    </section>`;
  }
}

if (!customElements.get("dm-photos-tab"))
  customElements.define("dm-photos-tab", PhotosTab);
