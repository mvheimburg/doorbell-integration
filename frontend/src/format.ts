/** Display formatting. Values sent to the panel are never formatted. */

const MIB = 1024 * 1024;

/** From 1 MiB one decimal and "MB" ("3.4 MB", "3,4 MB"); below, whole kilobytes rounded up. */
export function formatSize(bytes: number, locale: string): string {
  if (bytes >= MIB) {
    const value = new Intl.NumberFormat(locale, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(bytes / MIB);
    return `${value} MB`;
  }
  const kb = new Intl.NumberFormat(locale).format(Math.ceil(bytes / 1024));
  return `${kb} KB`;
}

/** ``2026-09-23T00:00:00Z`` → ``2026-09-23`` for a date input: the UTC day it starts. */
export function dateInput(time: string | null | undefined): string {
  return time ? time.slice(0, 10) : "";
}

/** A date input's day as midnight UTC, the way the panel stores active windows. */
export function midnightUtc(day: string): string {
  return `${day}T00:00:00Z`;
}

/** Today in the browser's time zone, for a new user's "Active from". */
export function today(now = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** ``Ding Dong.wav`` → ``["Ding Dong", ".wav"]``; a name without extension keeps it all. */
export function splitExtension(name: string): [string, string] {
  const dot = name.lastIndexOf(".");
  return dot > 0 ? [name.slice(0, dot), name.slice(dot)] : [name, ""];
}
