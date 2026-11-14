import { DIFFICULTY_LABELS } from "../../lib/format";
import type { ChallengeStatus, Difficulty } from "../../types/api";
import { Badge, type BadgeTone } from "./Badge";

const difficultyTone: Record<Difficulty, BadgeTone> = {
  very_easy: "neutral",
  easy: "success",
  medium: "warning",
  hard: "danger",
  insane: "brand",
};

export function DifficultyBadge({ difficulty }: { difficulty: Difficulty }) {
  return <Badge tone={difficultyTone[difficulty]}>{DIFFICULTY_LABELS[difficulty]}</Badge>;
}

export function StatusBadge({ status }: { status: ChallengeStatus }) {
  if (status === "solved") return <Badge tone="success">✓ Solved</Badge>;
  if (status === "progress") return <Badge tone="warning">In progress</Badge>;
  return <Badge>New</Badge>;
}
