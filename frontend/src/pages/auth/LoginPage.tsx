import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { useAuth } from "../../context/AuthContext";
import { ApiError, toMessage } from "../../lib/api";

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
  const [otp, setOtp] = useState("");
  const [needOtp, setNeedOtp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = safeNext(params.get("next"));
  if (user) return <Navigate to={next} replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(identifier.trim(), password, needOtp ? otp.trim() : undefined);
      navigate(next, { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError && caught.message === "otp_required") {
        setNeedOtp(true);
      } else {
        setError(toMessage(caught));
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Sign in"
      description="Welcome back. Pick up where you left off."
      footer={
        <>
          <AuthLink to="/register">Create account</AuthLink>
          <AuthLink to="/forgot">Forgot password?</AuthLink>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {error && <Alert tone="danger">{error}</Alert>}
        {needOtp && <Alert>Enter the 6-digit code from your authenticator app.</Alert>}
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
        {needOtp && (
          <Input
            id="otp"
            label="2FA code"
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="123456"
            required
            value={otp}
            onChange={(event) => setOtp(event.target.value)}
          />
        )}
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthLayout>
  );
}
