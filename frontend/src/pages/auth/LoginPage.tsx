import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { CodeStep } from "../../components/auth/CodeStep";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { useAuth } from "../../context/AuthContext";
import { toMessage } from "../../lib/api";
import { secondStepFrom, type SecondStep } from "../../lib/authSteps";

/** Only same-site relative paths, so ?next= can't redirect off-site. */
function safeNext(value: string | null): string {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [step, setStep] = useState<SecondStep>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = safeNext(params.get("next"));
  if (user) return <Navigate to={next} replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(identifier.trim(), password);
      navigate(next, { replace: true });
    } catch (caught) {
      const needed = secondStepFrom(caught);
      if (needed) setStep(needed);
      else setError(toMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  // Asking again without a code makes the server email a fresh one.
  async function resend() {
    try {
      await signIn(identifier.trim(), password);
    } catch (caught) {
      const needed = secondStepFrom(caught);
      if (needed?.kind === "email") {
        setStep(needed);
        return;
      }
      throw caught;
    }
  }

  return (
    <AuthLayout
      title={step ? "Check your code" : "Sign in"}
      description={step ? undefined : "Welcome back. Pick up where you left off."}
      footer={
        <>
          <AuthLink to="/register">Create account</AuthLink>
          <AuthLink to="/forgot">Forgot password?</AuthLink>
        </>
      }
    >
      {step ? (
        <CodeStep
          kind={step.kind}
          emailHint={step.kind === "email" ? step.emailHint : undefined}
          onSubmit={async (code) => {
            await signIn(identifier.trim(), password, code);
            navigate(next, { replace: true });
          }}
          onResend={step.kind === "email" ? resend : undefined}
          onBack={() => setStep(null)}
        />
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {error && <Alert tone="danger">{error}</Alert>}
          <Input
            id="identifier"
            label="Username or email"
            autoComplete="username"
            autoFocus
            required
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
          />
          <Input
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
