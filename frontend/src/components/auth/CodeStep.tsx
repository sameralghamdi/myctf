import { ArrowLeft, Mail, ShieldCheck } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toMessage } from "../../lib/api";
import { cn, focusRing } from "../../lib/cn";
import { useToast } from "../feedback/Toast";
import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import { OtpInput } from "../ui/OtpInput";

interface CodeStepProps {
  /** "email": we emailed a code; "app": authenticator-app code. */
  kind: "email" | "app";
  emailHint?: string;
  onSubmit: (code: string) => Promise<void>;
  /** Email only: ask for a fresh code. */
  onResend?: () => Promise<void>;
  onBack: () => void;
}

const RESEND_AFTER = 30;

/** Second sign-in step: type the 6-digit code. Submits by itself when the last digit lands. */
export function CodeStep({ kind, emailHint, onSubmit, onResend, onBack }: CodeStepProps) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [wait, setWait] = useState(kind === "email" ? RESEND_AFTER : 0);
  const toast = useToast();

  useEffect(() => {
    if (wait <= 0) return;
    const id = window.setTimeout(() => setWait((w) => w - 1), 1000);
    return () => window.clearTimeout(id);
  }, [wait]);

  async function verify(value: string) {
    if (value.length !== 6 || busy) return;
    setBusy(true);
    setError(null);
    try {
      await onSubmit(value);
    } catch (caught) {
      setError(toMessage(caught));
      setCode("");
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    if (!onResend) return;
    setError(null);
    try {
      await onResend();
      setWait(RESEND_AFTER);
      setCode("");
      toast({ tone: "success", title: "New code sent", description: emailHint ? `Check ${emailHint}` : undefined });
    } catch (caught) {
      setError(toMessage(caught));
    }
  }

  const Icon = kind === "email" ? Mail : ShieldCheck;
  return (
    <form
      className="flex animate-fade-up flex-col gap-6"
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        void verify(code);
      }}
    >
      <div className="flex items-start gap-4">
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-brand-400">
          <Icon aria-hidden="true" className="h-6 w-6" />
        </span>
        <p className="text-sm text-gray-300">
          {kind === "email" ? (
            <>
              We sent a 6-digit code to <span className="font-medium text-gray-50">{emailHint ?? "your email"}</span>. It
              expires in 10 minutes.
            </>
          ) : (
            "Enter the 6-digit code from your authenticator app."
          )}
        </p>
      </div>
      {error && <Alert tone="danger">{error}</Alert>}
      <OtpInput value={code} onChange={setCode} onComplete={(value) => void verify(value)} disabled={busy} invalid={Boolean(error)} />
      <Button type="submit" disabled={busy || code.length !== 6} className="w-full">
        {busy ? "Verifying…" : "Verify and sign in"}
      </Button>
      <div className="flex items-center justify-between text-sm">
        <button type="button" onClick={onBack} className={cn("inline-flex items-center gap-1 rounded text-gray-400 hover:text-gray-50", focusRing)}>
          <ArrowLeft aria-hidden="true" className="h-4 w-4" /> Back
        </button>
        {kind === "email" && onResend && (
          <button
            type="button"
            onClick={() => void resend()}
            disabled={wait > 0}
            className={cn("rounded text-brand-400 hover:text-brand-300 disabled:cursor-default disabled:text-gray-500", focusRing)}
          >
            {wait > 0 ? `Resend code in ${wait}s` : "Resend code"}
          </button>
        )}
      </div>
      {kind === "email" && <p className="text-xs text-gray-400">Can't find it? Check your spam or junk folder.</p>}
    </form>
  );
}
