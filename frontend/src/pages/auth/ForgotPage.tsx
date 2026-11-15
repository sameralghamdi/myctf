import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthLayout, AuthLink } from "../../components/layout/AuthLayout";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Field";
import { api, toMessage } from "../../lib/api";

interface ForgotResponse {
  message: string;
  /** Present only when the server runs with MYCTF_EXPOSE_DEV_LINKS (local dev). */
  reset_link?: string | null;
}

export function ForgotPage() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<ForgotResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setResult(
        await api<ForgotResponse>("/api/auth/password/forgot", {
          method: "POST",
          body: { email: email.trim() },
        }),
      );
    } catch (caught) {
      setError(toMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Reset your password"
      description="Enter your email and we'll send a reset link."
      footer={<AuthLink to="/login">Back to sign in</AuthLink>}
    >
      {result ? (
        <div className="flex flex-col gap-4">
          <Alert tone="success">{result.message}</Alert>
          {result.reset_link && (
            <p className="text-sm text-gray-400">
              Dev mode link:{" "}
              <Link className="text-brand-400 hover:underline" to={result.reset_link}>
                open reset page
              </Link>
            </p>
          )}
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
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
