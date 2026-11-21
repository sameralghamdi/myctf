import { CheckCircle2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { SecretInput } from "../../components/ui/SecretInput";
import { api, toMessage } from "../../lib/api";
import { cn } from "../../lib/cn";

const RULES: { label: string; test: (pw: string) => boolean }[] = [
  { label: "At least 10 characters", test: (pw) => pw.length >= 10 },
  {
    label: "3 of: lowercase, uppercase, digit, symbol",
    test: (pw) => [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((re) => re.test(pw)).length >= 3,
  },
];

export function ResetPage() {
  const { token = "" } = useParams();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const mismatch = confirm.length > 0 && confirm !== password;
  const ready = RULES.every((rule) => rule.test(password)) && confirm === password;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!ready) return;
    setBusy(true);
    setError(null);
    try {
      await api("/api/auth/password/reset", { method: "POST", body: { token, password } });
      setDone(true);
    } catch (caught) {
      setError(toMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title={done ? "Password updated" : "Choose a new password"}
      footer={<AuthLink to="/forgot">Need a new link?</AuthLink>}
    >
      {done ? (
        <div className="flex animate-fade-up flex-col gap-6">
          <div className="flex items-start gap-4">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-green-500/10 text-green-400">
              <CheckCircle2 aria-hidden="true" className="h-6 w-6" />
            </span>
            <p className="text-sm text-gray-300">
              Your password was changed and every other session was signed out. Sign in with the new password.
            </p>
          </div>
          <Button href="/login" className="w-full">
            Sign in
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {error && <Alert tone="danger">{error}</Alert>}
          <SecretInput
            id="password"
            label="New password"
            autoComplete="new-password"
            autoFocus
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <ul className="-mt-4 flex flex-col gap-1 text-xs">
            {RULES.map((rule) => {
              const ok = rule.test(password);
              return (
                <li key={rule.label} className={cn("flex items-center gap-2 transition-colors", ok ? "text-green-400" : "text-gray-400")}>
                  <CheckCircle2 aria-hidden="true" className={cn("h-3 w-3", !ok && "opacity-40")} />
                  {rule.label}
                </li>
              );
            })}
          </ul>
          <SecretInput
            id="confirm"
            label="Confirm new password"
            autoComplete="new-password"
            required
            value={confirm}
            error={mismatch ? "The passwords don't match." : undefined}
            onChange={(event) => setConfirm(event.target.value)}
          />
          <Button type="submit" disabled={busy || !ready} className="w-full">
            {busy ? "Updating…" : "Update password"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
