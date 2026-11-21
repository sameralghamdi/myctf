import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { CodeStep } from "../../components/auth/CodeStep";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { useAuth } from "../../context/AuthContext";
import { toMessage } from "../../lib/api";
import { secondStepFrom, type SecondStep } from "../../lib/authSteps";

export function RegisterPage() {
  const { user, signUp, signIn } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState<SecondStep>(null);

  if (user) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { verifyRequired } = await signUp(username.trim(), email.trim(), password);
      if (!verifyRequired) {
        navigate("/dashboard", { replace: true });
        return;
      }
      await requestCode();
    } catch (caught) {
      setError(toMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  /** Signing in without a code emails one; that is the "verify your email" step. */
  async function requestCode() {
    try {
      await signIn(username.trim(), password);
      navigate("/dashboard", { replace: true });
    } catch (caught) {
      const needed = secondStepFrom(caught);
      if (!needed) throw caught;
      setStep(needed);
    }
  }

  return (
    <AuthLayout
      title={step ? "Verify your email" : "Create account"}
      description={step ? "Your account is ready. Confirm it's your email to sign in." : "Start capturing flags in a few seconds."}
      footer={<AuthLink to="/login">Already have an account? Sign in</AuthLink>}
    >
      {step ? (
        <CodeStep
          kind={step.kind}
          emailHint={step.kind === "email" ? step.emailHint : undefined}
          onSubmit={async (code) => {
            await signIn(username.trim(), password, code);
            navigate("/dashboard", { replace: true });
          }}
          onResend={requestCode}
          onBack={() => navigate("/login")}
        />
      ) : (
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {error && <Alert tone="danger">{error}</Alert>}
        <Input
          id="username"
          label="Username"
          autoComplete="username"
          autoFocus
          required
          pattern={"[A-Za-z0-9_.\\-]{3,32}"}
          hint="3–32 characters: letters, digits, dot, underscore or dash."
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
        <Input
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Input
          id="password"
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          minLength={10}
          hint="At least 10 characters, mixing upper, lower, digits and symbols."
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
      )}
    </AuthLayout>
  );
}
