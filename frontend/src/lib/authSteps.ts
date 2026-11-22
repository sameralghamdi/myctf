import { ApiError } from "./api";

export type SecondStep = { kind: "email"; emailHint?: string } | { kind: "app" } | null;

/** Which second sign-in step (if any) a login error is asking for. */
export function secondStepFrom(error: unknown): SecondStep {
  if (!(error instanceof ApiError)) return null;
  if (error.message === "otp_required") return { kind: "app" };
  if (error.message === "email_otp_required") {
    const data = error.data as { email_hint?: unknown } | null;
    return { kind: "email", emailHint: typeof data?.email_hint === "string" ? data.email_hint : undefined };
  }
  return null;
}
