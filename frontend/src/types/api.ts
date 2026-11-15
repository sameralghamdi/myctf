import type { UserRole } from "./navigation";

export type Difficulty = "very_easy" | "easy" | "medium" | "hard" | "insane";
export type ChallengeStatus = "new" | "progress" | "solved";

export interface SessionUser {
  id: number;
  username: string;
  email: string;
  display_name: string;
  role: UserRole;
  email_verified: boolean;
  two_factor: boolean;
}

export interface SessionResponse {
  user: SessionUser | null;
  score?: number;
  rank?: number | null;
}

export interface Challenge {
  id: number;
  slug: string;
  public_slug: string;
  name: string;
  category: string | null;
  category_name: string | null;
  skill: string | null;
  difficulty: Difficulty;
  points: number;
  est_minutes: number | null;
  has_lab: boolean;
  lab_kind: string;
  /**
   * Shell challenge: played in the web terminal (TerminalEmulator) against a
   * simulated machine, instead of an embedded web page. Implies `has_lab`.
   */
  is_shell: boolean;
  /** Hybrid labs provide a target page alongside the terminal. */
  has_web_ui: boolean;
  default_lab_view: "target" | "terminal";
  solved: boolean;
  status?: ChallengeStatus;
}

export interface Hint {
  id: number;
  level: number;
  cost: number;
  unlocked: boolean;
  body: string | null;
}

export interface LabInstance {
  instance_id: string;
  url: string;
  state: string;
  expires_at: string;
}

export interface ChallengeDetail extends Challenge {
  description: string;
  objectives: string[];
  references: { title: string; url: string }[];
  /** External target for static challenges, if the author set one. */
  target_url?: string | null;
  attempts: number;
  hints: Hint[];
  remediation?: string;
  walkthrough?: string;
  lab?: LabInstance | null;
}

export interface SubmitResult {
  correct: boolean;
  already_solved: boolean;
  awarded: number;
  first_blood: boolean;
  message: string;
}

export interface SkillStat {
  earned: number;
  available: number;
  solved: number;
  total: number;
}

export interface Achievement {
  slug: string;
  name: string;
  description: string;
  earned: boolean;
}

export interface DashboardData {
  score: number;
  rank: number;
  streak: number;
  completed: number;
  total: number;
  available: number;
  completion_pct: number;
  skills: Record<string, SkillStat>;
  recent: { name: string; slug: string; public_slug: string; correct: number | boolean; created_at: string }[];
  recommended: Challenge | null;
  in_progress: Challenge | null;
  achievements: { slug: string; name: string; description: string }[];
}

export interface ProfileData {
  user: SessionUser;
  score: number;
  rank: number | null;
  solves: {
    name: string;
    slug: string;
    public_slug: string;
    difficulty: Difficulty;
    skill: string | null;
    points_awarded: number;
    created_at: string;
  }[];
  skills: Record<string, SkillStat>;
  achievements: Achievement[];
}

export interface LeaderboardRow {
  rank: number;
  username: string;
  display_name: string;
  score: number;
  solves: number;
}

export interface LearningPath {
  slug: string;
  name: string;
  level: string;
  description: string;
  done: number;
  total: number;
  items: { slug: string; public_slug: string; name: string; difficulty: Difficulty; points: number; solved: boolean }[];
}

export interface PublicInfo {
  stats: { users: number; challenges: number; solves: number; categories: number };
  live_kinds: string[];
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  email_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminOverview {
  stats: { users: number; challenges: number; solves: number; running_labs: number };
  users: AdminUser[];
}

export interface AdminChallenge {
  id: number;
  slug: string;
  name: string;
  category_name: string;
  difficulty: Difficulty;
  lab_kind: string;
  points: number;
  published: boolean;
}

export interface RunningLab {
  instance_id: string;
  user: string;
  challenge: string;
  state: string;
  expires_at: string;
}

export interface AuditEntry {
  user: string | null;
  action: string;
  detail: string;
  at: string;
}

export interface Analytics {
  platform: AdminOverview["stats"];
  solves_by_category: { category: string; solves: number }[];
  least_solved: { name: string; slug: string; solves: number }[];
}

/** GET /labs/<id>/shell : what the terminal needs to draw its prompt. */
export interface ShellSession {
  user: string;
  host: string;
  home: string;
  cwd: string;
  /** One-line message shown when the terminal opens. */
  motd: string;
}

/** POST /labs/<id>/shell {command} : the result of one command. */
export interface ShellResult {
  stdout: string;
  stderr: string;
  cwd: string;
}
