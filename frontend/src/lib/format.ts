import type { Difficulty } from "../types/api";

export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  very_easy: "Very Easy",
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
  insane: "Insane",
};

/** All times are shown in Saudi Arabia time (AST, UTC+3). */
export const APP_TIME_ZONE = "Asia/Riyadh";

/**
 * The API sends UTC timestamps as "YYYY-MM-DD HH:MM:SS" with no zone marker, which
 * `new Date()` would read as the browser's local time. Treat zone-less values as UTC.
 */
function parseApiDate(value: string): Date {
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value);
  const iso = value.includes("T") ? value : value.replace(" ", "T");
  return new Date(hasZone ? iso : `${iso}Z`);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = parseApiDate(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short", timeZone: APP_TIME_ZONE });
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = parseApiDate(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, { dateStyle: "medium", timeZone: APP_TIME_ZONE });
}

/** Only allow http(s) links from challenge data (blocks javascript: URLs). */
export function isSafeUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

export function percent(part: number, whole: number): number {
  return whole > 0 ? Math.min(100, Math.round((100 * part) / whole)) : 0;
}
