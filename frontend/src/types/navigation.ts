import type { ComponentType, SVGProps } from "react";

export type IconComponent = ComponentType<SVGProps<SVGSVGElement>>;

/** Mirrors the `users.role` CHECK constraint in schema.sql. */
export type UserRole = "student" | "instructor" | "administrator";

export interface UserSummary {
  username: string;
  role: UserRole;
  score: number;
  /** null when the user has no rank yet. */
  rank: number | null;
}

export interface NavItem {
  label: string;
  href: string;
  icon: IconComponent;
  /** `exact` highlights only on the same path; `prefix` also on child paths. */
  match?: "exact" | "prefix";
}

export interface NavSection {
  /** Omit for the primary, unlabeled group. */
  title?: string;
  items: NavItem[];
  adminOnly?: boolean;
}

export interface Breadcrumb {
  label: string;
  href?: string;
}
