import type { Difficulty } from "../types/api";

export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  very_easy: "Very Easy",
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
  insane: "Insane",
};

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, { dateStyle: "medium" });
}

/** Only allow http(s) links from challenge data (blocks javascript: URLs). */
export function isSafeUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

export function percent(part: number, whole: number): number {
  return whole > 0 ? Math.min(100, Math.round((100 * part) / whole)) : 0;
}
