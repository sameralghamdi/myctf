import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { api, toMessage } from "../../lib/api";

export function ResetPage() {
  const { token = "" } = useParams();
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
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
      title="Set a new password"
      footer={<AuthLink to="/login">Back to sign in</AuthLink>}
    >
      {done ? (
        <Alert tone="success">Password updated. You can sign in now.</Alert>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {error && <Alert tone="danger">{error}</Alert>}
          <Input
            id="password"
            label="New password"
            type="password"
            autoComplete="new-password"
            required
            minLength={10}
            hint="At least 10 characters, mixing upper, lower, digits and symbols."
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Updating…" : "Update password"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
