/** The integration's admin API: websocket commands, and HTTP for media files. */

import type { HomeAssistant, UserRecord, UsersResponse } from "./types";

/** Codes that no single action can fix: the panel shows a page-level message instead. */
export const FATAL_CODES = new Set([
  "not-admin",
  "bad-token",
  "not-configured",
]);

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
  ) {
    super(message);
  }
}

export const toApiError = (err: unknown): ApiError =>
  err instanceof ApiError
    ? err
    : new ApiError(
        (err as { message?: string })?.message || String(err),
        (err as { code?: string })?.code || "unknown",
      );

/** The segments of a media path: ``groups/<id>/<name>`` or ``photos/<name>``. */
export type MediaPath = ["groups", string, string] | ["photos", string];

export class AdminApi {
  constructor(
    public hass: HomeAssistant,
    readonly entryId: string,
  ) {}

  private async ws<T>(message: Record<string, unknown>): Promise<T> {
    try {
      return await this.hass.callWS<T>({ entry_id: this.entryId, ...message });
    } catch (err) {
      throw toApiError(err);
    }
  }

  call<T = unknown>(
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
    path: string[],
    body?: unknown,
  ): Promise<T> {
    return this.ws<T>({
      type: "doormonitor/admin/call",
      method,
      path,
      ...(body === undefined ? {} : { body }),
    });
  }

  users(): Promise<UsersResponse> {
    return this.ws({ type: "doormonitor/admin/users" });
  }

  saveUser(
    userId: string | null,
    user: Omit<UserRecord, "id">,
    haUserId: string | null,
  ): Promise<UserRecord> {
    return this.ws({
      type: "doormonitor/admin/save_user",
      ...(userId ? { user_id: userId } : {}),
      user,
      ha_user_id: haUserId,
    });
  }

  mediaUrl(path: MediaPath): string {
    return `/api/doormonitor/${this.entryId}/media/${path.map(encodeURIComponent).join("/")}`;
  }

  /** A URL the browser can load without the auth header (audio, video, img). */
  async signedUrl(path: MediaPath): Promise<string> {
    const result = await this.hass.callWS<{ path: string }>({
      type: "auth/sign_path",
      path: this.mediaUrl(path),
      expires: 3600,
    });
    return result.path;
  }

  /** Upload one file; resolves to the name the panel stored it under. */
  async upload(
    path: MediaPath,
    file: File,
    overwrite: boolean,
  ): Promise<string> {
    let response: Response;
    try {
      response = await this.hass.fetchWithAuth(
        this.mediaUrl(path) + (overwrite ? "?overwrite=true" : ""),
        {
          method: "PUT",
          body: file,
          headers: {
            "Content-Type": file.type || "application/octet-stream",
          },
        },
      );
    } catch {
      throw new ApiError("The panel is unreachable", "unreachable");
    }
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(
        body?.error || `HTTP ${response.status}`,
        body?.code || `http-${response.status}`,
      );
    }
    return body?.name ?? file.name;
  }
}
