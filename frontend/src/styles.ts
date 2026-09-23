import { css } from "lit";

/** The doorbell admin app's layout, on Home Assistant's theme tokens (light and dark). */
export const styles = css`
  :host {
    display: block;
    box-sizing: border-box;
    color: var(--primary-text-color);
    font-family: var(
      --ha-font-family-body,
      var(--paper-font-body1_-_font-family, inherit)
    );
    -webkit-font-smoothing: antialiased;
    --dm-text: var(--primary-text-color, #1b1b1a);
    --dm-muted: var(--secondary-text-color, #5b5a55);
    --dm-accent: var(--primary-color, #03a9f4);
    --dm-on-accent: var(--text-primary-color, #fff);
    --dm-error: var(--error-color, #c62828);
    --dm-success: var(--success-color, #2e7d32);
    --dm-warning: var(--warning-color, #f59e0b);
    --dm-info: var(--info-color, #039be5);
    --dm-surface: var(--ha-card-background, var(--card-background-color, #fff));
    --dm-pill: var(--secondary-background-color, #f3f2ee);
    --dm-line: var(--divider-color, rgba(0, 0, 0, 0.12));
    --dm-radius: var(--ha-card-border-radius, 12px);
  }
  * {
    box-sizing: border-box;
  }
  [hidden] {
    display: none !important;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }
  .i {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
  .i.s {
    width: 16px;
    height: 16px;
  }
  .spin {
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  .card {
    background: var(--dm-surface);
    border: 1px solid var(--dm-line);
    border-radius: var(--dm-radius);
    box-shadow: var(--ha-card-box-shadow, none);
    padding: 20px 24px;
  }
  .card + .card {
    margin-top: 16px;
  }
  .card-head {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 40px;
    flex-wrap: wrap;
  }
  .card-head h2 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
  }
  .card-head h2 span {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .card-head .tools {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: auto;
  }
  .intro,
  .muted {
    color: var(--dm-muted);
  }
  .intro {
    margin: 8px 0 12px;
    line-height: 1.45;
  }
  .note,
  .hint {
    color: var(--dm-muted);
    font-size: 0.8rem;
    margin: 6px 0 0;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: 40px;
    padding: 0 16px;
    border-radius: 8px;
    border: 1px solid var(--dm-line);
    background: transparent;
    color: var(--dm-text);
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
  .btn.primary {
    background: var(--dm-accent);
    border-color: var(--dm-accent);
    color: var(--dm-on-accent);
  }
  .btn.danger {
    background: var(--dm-error);
    border-color: var(--dm-error);
    color: #fff;
  }
  .btn:disabled {
    opacity: 0.45;
    cursor: default;
  }
  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: var(--dm-text);
    cursor: pointer;
    flex-shrink: 0;
  }
  .icon-btn:hover:not(:disabled) {
    background: var(--dm-pill);
  }
  .icon-btn.danger {
    color: var(--dm-error);
  }
  .icon-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .icon-btn.spacer {
    visibility: hidden;
  }
  .btn:focus-visible,
  .icon-btn:focus-visible,
  input:focus-visible,
  select:focus-visible {
    outline: 2px solid var(--dm-accent);
    outline-offset: 2px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    background: var(--dm-pill);
    color: var(--dm-text);
    white-space: nowrap;
  }
  .badge.admin {
    background: color-mix(in srgb, var(--dm-info) 25%, transparent);
  }
  .badge.resident {
    background: color-mix(in srgb, var(--dm-warning) 30%, transparent);
  }
  .badge.guest {
    background: color-mix(in srgb, var(--dm-success) 25%, transparent);
  }
  .badge.default {
    background: color-mix(in srgb, var(--dm-accent) 22%, transparent);
  }
  label.field {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    min-width: 0;
  }
  input[type="text"],
  input[type="password"],
  input[type="date"],
  select {
    font: inherit;
    font-weight: 400;
    color: var(--dm-text);
    background: var(--dm-surface);
    border: 1px solid var(--dm-line);
    border-radius: 8px;
    min-height: 40px;
    padding: 0 12px;
    width: 100%;
    min-width: 0;
  }
  input[type="date"] {
    color-scheme: light dark;
  }
  input[type="checkbox"] {
    width: 20px;
    height: 20px;
    accent-color: var(--dm-accent);
  }
  .alert {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 12px 14px;
    border-radius: 8px;
    background: color-mix(in srgb, var(--dm-error) 14%, transparent);
    color: var(--dm-text);
    margin: 8px 0;
  }
  .alert .i {
    color: var(--dm-error);
  }
  .alert .grow {
    flex: 1;
  }
  .center {
    display: flex;
    justify-content: center;
    padding: 48px 0;
    color: var(--dm-muted);
  }
  .center .i {
    width: 32px;
    height: 32px;
  }
  /* Rows */
  .rows {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 48px;
    padding: 4px 0;
    border-top: 1px solid var(--dm-line);
  }
  .row:first-child {
    border-top: none;
  }
  .row.inactive .who {
    opacity: 0.5;
  }
  .who {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }
  .who .name {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .who .sub {
    font-size: 0.8rem;
    color: var(--dm-muted);
    display: flex;
    gap: 4px;
    align-items: center;
  }
  /* Files */
  .file-row {
    display: flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
  }
  .file-row .fname {
    flex: 1;
    min-width: 0;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .file-row .size {
    color: var(--dm-muted);
    font-size: 0.8rem;
    margin-right: 4px;
    white-space: nowrap;
  }
  .sound {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    flex-wrap: wrap;
  }
  .sound .file-row {
    flex: 1 1 240px;
  }
  .sound audio {
    flex: 1 1 260px;
    min-width: 0;
    height: 40px;
  }
  .grid {
    display: grid;
    gap: 16px;
    margin-top: 8px;
  }
  .grid.videos {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .grid.photos {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  video {
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    border-radius: 8px;
    display: block;
  }
  .photo img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 8px;
    display: block;
    background: var(--dm-pill);
  }
  .rename {
    display: flex;
    align-items: center;
    gap: 4px;
    flex: 1;
    min-width: 0;
  }
  .rename input {
    flex: 1;
  }
  .rename .ext {
    color: var(--dm-muted);
  }
  .upload {
    border-top: 1px solid var(--dm-line);
    margin-top: 16px;
    padding-top: 16px;
  }
  .upload .line {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
  .upload .check {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--dm-muted);
  }
  .upload input[type="file"] {
    flex: 1 1 220px;
    min-width: 0;
    font: inherit;
    color: var(--dm-muted);
  }
  .inline-form {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .inline-form input {
    flex: 1 1 220px;
  }
  .inline-form select {
    width: auto;
  }
  /* Appearance */
  .modes {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }
  .modes .card + .card {
    margin-top: 0;
  }
  .mode label.field + label.field {
    margin-top: 16px;
  }
  /* Dialogs */
  .scrim {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 10;
  }
  .dialog {
    background: var(--dm-surface);
    color: var(--dm-text);
    border-radius: var(--dm-radius);
    width: min(560px, 100%);
    max-height: calc(100vh - 32px);
    overflow: auto;
    padding: 20px 24px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  }
  .dialog h2 {
    margin: 0 0 12px;
    font-size: 1.2rem;
  }
  .dialog p {
    margin: 6px 0;
    line-height: 1.45;
  }
  .form {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }
  .form .wide {
    grid-column: 1 / -1;
  }
  .ble {
    display: grid;
    grid-template-columns: 120px minmax(0, 1fr);
    gap: 8px;
  }
  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 20px;
  }
  @media (max-width: 700px) {
    .card {
      padding: 16px;
    }
    .modes,
    .form,
    .grid.videos {
      grid-template-columns: minmax(0, 1fr);
    }
    .grid.photos {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
  @media (min-width: 701px) and (max-width: 960px) {
    .grid.photos {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
`;
