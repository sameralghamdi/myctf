import { MailCheck } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { api, toMessage } from "../../lib/api";
import { cn, focusRing } from "../../lib/cn";

interface ForgotResponse {
  message: string;
  /** Present only when the server runs with MYCTF_EXPOSE_DEV_LINKS (local dev). */
  reset_link?: string | null;
}

const RESEND_AFTER = 60;

export function ForgotPage() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<ForgotResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [wait, setWait] = useState(0);

  useEffect(() => {
    if (wait <= 0) return;
    const id = window.setTimeout(() => setWait((w) => w - 1), 1000);
    return () => window.clearTimeout(id);
  }, [wait]);

  async function send() {
    setBusy(true);
    setError(null);
    try {
      setResult(
        await api<ForgotResponse>("/api/auth/password/forgot", {
          method: "POST",
          body: { email: email.trim() },
        }),
      );
      setWait(RESEND_AFTER);
    } catch (caught) {
      setError(toMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title={result ? "Check your email" : "Forgot your password?"}
      description={result ? undefined : "Enter the email on your account and we'll send you a link to choose a new password."}
      footer={<AuthLink to="/login">Back to sign in</AuthLink>}
    >
      {result ? (
        <div className="flex animate-fade-up flex-col gap-6">
          <div className="flex items-start gap-4">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-green-500/10 text-green-400">
              <MailCheck aria-hidden="true" className="h-6 w-6" />
            </span>
            <div className="flex flex-col gap-1 text-sm text-gray-300">
              <p>
                If an account uses <span className="font-medium text-gray-50">{email.trim()}</span>, a reset link is on
                its way. It works once and expires in 30 minutes.
              </p>
              <p className="text-xs text-gray-400">Can't find it? Check your spam or junk folder.</p>
            </div>
          </div>
          {error && <Alert tone="danger">{error}</Alert>}
          {result.reset_link && (
            <Alert>
              Dev mode:{" "}
              <Link className="text-brand-400 hover:underline" to={result.reset_link}>
                open the reset page
              </Link>
            </Alert>
          )}
          <div className="flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={() => {
                setResult(null);
                setError(null);
              }}
              className={cn("rounded text-gray-400 hover:text-gray-50", focusRing)}
            >
              Use a different email
            </button>
            <button
              type="button"
              disabled={wait > 0 || busy}
              onClick={() => void send()}
              className={cn("rounded text-brand-400 hover:text-brand-300 disabled:cursor-default disabled:text-gray-500", focusRing)}
            >
              {wait > 0 ? `Resend in ${wait}s` : "Resend link"}
            </button>
          </div>
        </div>
      ) : (
        <form
          onSubmit={(event: FormEvent) => {
            event.preventDefault();
            void send();
          }}
          className="flex flex-col gap-6"
        >
          {error && <Alert tone="danger">{error}</Alert>}
          <Input
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            autoFocus
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Sending…" : "Send reset link"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
