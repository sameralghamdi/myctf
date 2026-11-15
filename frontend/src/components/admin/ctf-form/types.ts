import type { Difficulty } from "../../../types/api";

export type ChallengeKind = "static" | "lab";
export type StepId = "basics" | "content" | "target" | "hints" | "review";

export interface HintDraft {
  /** Local key for React lists; never sent to the server. */
  id: string;
  body: string;
  cost: string;
}

export interface CtfFormValues {
  title: string;
  slug: string;
  /** False until the admin edits the slug by hand; until then it follows the title. */
  slugEdited: boolean;
  category: string;
  difficulty: Difficulty;
  points: string;
  /** False until the admin edits points by hand; until then it follows difficulty. */
  pointsEdited: boolean;
  description: string;
  kind: ChallengeKind;
  targetUrl: string;
  labKind: string;
  flag: string;
  hints: HintDraft[];
  published: boolean;
}

export type CtfFormErrors = Partial<Record<string, string>>;

export interface CategoryOption {
  slug: string;
  name: string;
}

/** Props shared by every step component. */
export interface StepProps {
  values: CtfFormValues;
  errors: CtfFormErrors;
  onChange: (patch: Partial<CtfFormValues>) => void;
}

/** The JSON body accepted by POST /admin/api/challenges/publish. */
export interface ChallengeManifest {
  slug: string;
  name: string;
  category: string;
  category_name: string;
  difficulty: Difficulty;
  points: number;
  description: string;
  lab_kind: string;
  flag?: string;
  target_url?: string;
  hints: { level: number; cost: number; body: string }[];
  published: boolean;
  create_only: true;
}
