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
export function parseApiDate(value: string): Date {
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

/** "just now", "5m ago", "3h ago", "2d ago", then a short date. */
export function timeAgo(value: string | null | undefined, now: number = Date.now()): string {
  if (!value) return "—";
  const date = parseApiDate(value);
  if (Number.isNaN(date.getTime())) return value;
  const seconds = Math.max(0, Math.round((now - date.getTime()) / 1000));
  if (seconds < 45) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(value);
}

/** 1,284 · 12.9K · 4.2M — compact numbers for tight spaces. */
export function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", { notation: value >= 10000 ? "compact" : "standard", maximumFractionDigits: 1 }).format(value);
}

/** Time-of-day greeting in Saudi Arabia time. */
export function greeting(now: Date = new Date()): string {
  const hour = Number(new Intl.DateTimeFormat("en-GB", { hour: "numeric", hour12: false, timeZone: APP_TIME_ZONE }).format(now));
  if (hour < 5) return "Burning the midnight oil";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}
