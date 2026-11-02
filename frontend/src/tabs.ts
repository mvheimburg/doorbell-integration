/** Retain all tab IDs so the inactive components can be restored unchanged. */
export type TabId = "users" | "appearance" | "media-groups" | "photos";

/** Visible tabs, still filtered by the doorbell's advertised features. */
export const TABS: readonly TabId[] = [
  "users",
  // Temporarily hidden. Uncomment to restore these tabs; their code and tests remain.
  // "appearance",
  // "media-groups",
  // "photos",
];
