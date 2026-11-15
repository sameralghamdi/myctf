import { isSafeUrl } from "../../../lib/format";
import { STEPS } from "./constants";
import type {
  CategoryOption,
  ChallengeManifest,
  CtfFormErrors,
  CtfFormValues,
  StepId,
} from "./types";

const SLUG = /^[a-z0-9][a-z0-9-]{1,48}$/;
const FLAG = /^(?:MYCTF|FLAG)\{[^}]+\}$/;
const WHOLE_NUMBER = /^\d+$/;

/** "My First Challenge!" -> "my-first-challenge" */
export function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 49);
}

/** A random flag in the platform's format, e.g. MYCTF{sql_login_9f2c41d07ab3}. */
export function generateFlag(slug: string): string {
  const bytes = new Uint8Array(6);
  crypto.getRandomValues(bytes);
  const random = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  const label = slug.replace(/-/g, "_") || "flag";
  return `MYCTF{${label}_${random}}`;
}

/** Same rules as app/manifest.py, checked early so the admin gets instant feedback. */
export function validateStep(step: StepId, values: CtfFormValues): CtfFormErrors {
  const errors: CtfFormErrors = {};

  if (step === "basics") {
    if (!values.title.trim()) errors.title = "Give the challenge a title.";
    else if (values.title.trim().length > 120) errors.title = "Keep the title under 120 characters.";
    if (!SLUG.test(values.slug)) {
      errors.slug = "Use 2–49 lowercase letters, digits or dashes, starting with a letter or digit.";
    }
    if (!values.category) errors.category = "Pick a category.";
    const points = Number(values.points);
    if (!WHOLE_NUMBER.test(values.points) || points < 1 || points > 10000) {
      errors.points = "Points must be a whole number from 1 to 10000.";
    }
  }

  if (step === "content") {
    if (!values.description.trim()) errors.description = "Describe what the player has to do.";
    else if (values.description.length > 20000) {
      errors.description = "Keep the description under 20000 characters.";
    }
  }

  if (step === "target") {
    if (values.kind === "static") {
      const url = values.targetUrl.trim();
      if (url && (!isSafeUrl(url) || /\s/.test(url))) {
        errors.targetUrl = "Enter a full link starting with http:// or https://";
      }
      if (!FLAG.test(values.flag.trim())) errors.flag = "The flag must look like MYCTF{something} or FLAG{something}.";
    } else if (!values.labKind) {
      errors.labKind = "Pick one of the built-in labs.";
    }
  }

  if (step === "hints") {
    values.hints.forEach((hint) => {
      if (!hint.body.trim()) errors[`hint-${hint.id}-body`] = "Write the hint or remove it.";
      if (!WHOLE_NUMBER.test(hint.cost) || Number(hint.cost) > 10000) {
        errors[`hint-${hint.id}-cost`] = "Cost must be a whole number (0 = free).";
      }
    });
  }

  return errors;
}

/** First step that still has a problem, or null when everything is valid. */
export function firstInvalidStep(
  values: CtfFormValues,
): { step: StepId; errors: CtfFormErrors } | null {
  for (const { id } of STEPS) {
    const errors = validateStep(id, values);
    if (Object.keys(errors).length > 0) return { step: id, errors };
  }
  return null;
}

export function toManifest(
  values: CtfFormValues,
  categories: CategoryOption[],
): ChallengeManifest {
  const category = categories.find((option) => option.slug === values.category);
  const isStatic = values.kind === "static";
  const targetUrl = values.targetUrl.trim();

  return {
    slug: values.slug,
    name: values.title.trim(),
    category: values.category,
    category_name: category?.name ?? values.category,
    difficulty: values.difficulty,
    points: Number(values.points),
    description: values.description.trim(),
    lab_kind: isStatic ? "static" : values.labKind,
    ...(isStatic ? { flag: values.flag.trim() } : {}),
    ...(isStatic && targetUrl ? { target_url: targetUrl } : {}),
    hints: values.hints.map((hint, index) => ({
      level: index + 1,
      cost: Number(hint.cost),
      body: hint.body.trim(),
    })),
    published: values.published,
    create_only: true,
  };
}
