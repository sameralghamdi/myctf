import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { useAuth } from "../../context/AuthContext";
import { toMessage } from "../../lib/api";

export function RegisterPage() {
  const { user, signUp } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signUp(username.trim(), email.trim(), password);
      navigate("/dashboard", { replace: true });
    } catch (caught) {
      setError(toMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Create account"
      description="Start capturing flags in a few seconds."
      footer={<AuthLink to="/login">Already have an account? Sign in</AuthLink>}
    >
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
    </AuthLayout>
  );
}
