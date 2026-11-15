import type { Difficulty } from "../../../types/api";
import type { CategoryOption, CtfFormValues, StepId } from "./types";

export const STEPS: { id: StepId; label: string }[] = [
  { id: "basics", label: "Basics" },
  { id: "content", label: "Description" },
  { id: "target", label: "Target & flag" },
  { id: "hints", label: "Hints" },
  { id: "review", label: "Review" },
];

/** Mirrors DIFFICULTY_POINTS in app/config.py. */
export const DEFAULT_POINTS: Record<Difficulty, number> = {
  very_easy: 50,
  easy: 100,
  medium: 200,
  hard: 350,
  insane: 500,
};

export const PRESET_CATEGORIES: CategoryOption[] = [
  { slug: "web", name: "Web" },
  { slug: "crypto", name: "Crypto" },
  { slug: "pwn", name: "Pwn" },
  { slug: "reverse", name: "Reverse Engineering" },
  { slug: "forensics", name: "Forensics" },
  { slug: "network", name: "Network" },
  { slug: "privesc", name: "Privilege Escalation" },
  { slug: "osint", name: "OSINT" },
  { slug: "misc", name: "Misc" },
];

export const MAX_HINTS = 5;

export const INITIAL_VALUES: CtfFormValues = {
  title: "",
  slug: "",
  slugEdited: false,
  category: "web",
  difficulty: "easy",
  points: String(DEFAULT_POINTS.easy),
  pointsEdited: false,
  description: "",
  kind: "static",
  targetUrl: "",
  labKind: "",
  flag: "",
  hints: [],
  published: true,
};
