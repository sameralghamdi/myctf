import { Crosshair, GraduationCap, ShieldCheck } from "lucide-react";
import { Navigate } from "react-router-dom";
import { Brand } from "../components/layout/SidebarBrand";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";
import type { PublicInfo } from "../types/api";

const features = [
  {
    icon: Crosshair,
    title: "Real targets",
    body: "Every lab is a live, exploitable app — SQLi, XSS, IDOR, path traversal, command injection and more. No multiple-choice quizzes.",
  },
  {
    icon: ShieldCheck,
    title: "Isolated and safe",
    body: "Each instance is private to you with a per-session flag. Vulnerable code never touches the platform itself.",
  },
  {
    icon: GraduationCap,
    title: "Learn the defense",
    body: "After each capture, a debrief explains the root cause and the remediation that would have stopped it.",
  },
];

export function LandingPage() {
  const { user } = useAuth();
  const { data } = useApi<PublicInfo>("/api/public");
  if (user) return <Navigate to="/dashboard" replace />;

  const stat = (value: number | undefined) => (value === undefined ? "—" : value);

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-6">
        <Brand to="/" />
        <div className="flex items-center gap-2">
          <Button href="/login" variant="ghost" size="sm">
            Sign in
          </Button>
          <Button href="/register" size="sm">
            Create account
          </Button>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-16 px-6 pb-16 pt-16">
        <section className="flex flex-col items-center gap-6 text-center">
          <p className="text-xs font-medium uppercase tracking-wider text-brand-400">
            Learn · Exploit · Capture
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-gray-50 sm:text-5xl">
            Hands-on penetration testing
            <br />
            <span className="text-brand-400">in isolated labs.</span>
          </h1>
          <p className="max-w-xl text-base text-gray-400">
            Exploit intentionally vulnerable targets, capture flags, and learn exactly why each
            attack works — then how to defend against it. From HTTP basics to multi-step web
            exploitation.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Button href="/register">Start hacking</Button>
            <Button href="/login" variant="secondary">
              I have an account
            </Button>
          </div>
        </section>

        <section aria-label="Platform stats" className="grid grid-cols-2 gap-6 lg:grid-cols-4">
          <StatCard label="Challenges" value={stat(data?.stats.challenges)} tone="brand" />
          <StatCard label="Hackers" value={stat(data?.stats.users)} tone="brand" />
          <StatCard label="Flags captured" value={stat(data?.stats.solves)} tone="success" />
          <StatCard label="Categories" value={stat(data?.stats.categories)} />
        </section>

        <section className="grid gap-6 md:grid-cols-3">
          {features.map(({ icon: Icon, title, body }) => (
            <Card key={title} className="flex flex-col gap-4">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-500/10 text-brand-400">
                <Icon aria-hidden="true" className="h-4 w-4" />
              </span>
              <h2 className="text-lg font-semibold text-gray-50">{title}</h2>
              <p className="text-sm text-gray-400">{body}</p>
            </Card>
          ))}
        </section>
      </main>
    </div>
  );
}
