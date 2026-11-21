import {
  ArrowRight,
  Crosshair,
  Flag,
  GraduationCap,
  Play,
  Rocket,
  ShieldCheck,
  Terminal,
  Trophy,
  Users,
} from "lucide-react";
import { Link, Navigate } from "react-router-dom";
import { Brand } from "../components/layout/SidebarBrand";
import { AnimatedNumber } from "../components/ui/AnimatedNumber";
import { Button } from "../components/ui/Button";
import { SpotlightCard } from "../components/ui/SpotlightCard";
import { TypingTerminal, type TerminalScriptLine } from "../components/ui/TypingTerminal";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";
import { reveal } from "../lib/motion";
import type { PublicInfo } from "../types/api";

const script: TerminalScriptLine[] = [
  { kind: "cmd", text: "start-lab --private" },
  { kind: "out", text: "▸ isolated instance ready · target.lab.local" },
  { kind: "cmd", text: "nmap -sV target.lab.local" },
  { kind: "out", text: "80/tcp  open  http" },
  { kind: "cmd", text: "curl -i http://target.lab.local/" },
  { kind: "out", text: "HTTP/1.1 200 OK · server banner noted" },
  { kind: "cmd", text: "# investigate · exploit · capture" },
  { kind: "ok", text: "✓ flag captured  MYCTF{••••••••••••}  +100 pts" },
];

const features = [
  {
    icon: Crosshair,
    title: "Real, exploitable targets",
    body: "Live web apps and simulated machines with genuine flaws: injection, broken access control, misconfigurations and more. No multiple-choice quizzes.",
  },
  {
    icon: ShieldCheck,
    title: "Private and isolated",
    body: "Every lab is yours alone, with a flag generated for your session. The vulnerable code never touches the platform itself.",
  },
  {
    icon: Terminal,
    title: "Browser and terminal",
    body: "Drive targets through a built-in browser with request editing, or from a full in-browser terminal with curl, ffuf, nmap and friends.",
  },
  {
    icon: GraduationCap,
    title: "Learn the defense",
    body: "Each capture unlocks the root cause and the fix, so you leave every challenge knowing how to stop the attack, too.",
  },
  {
    icon: Trophy,
    title: "Compete live",
    body: "A live scoreboard, first-blood bonuses for the fastest players, streaks and achievements keep the pressure on.",
  },
  {
    icon: Rocket,
    title: "Guided paths",
    body: "Structured learning paths take you from your first HTTP request to multi-step exploitation, one flag at a time.",
  },
];

const steps = [
  { icon: Flag, title: "Pick a challenge", body: "Filter by category and difficulty." },
  { icon: Play, title: "Launch your lab", body: "A private target spins up in seconds." },
  { icon: Crosshair, title: "Investigate & exploit", body: "Recon, find the flaw, break in." },
  { icon: Trophy, title: "Capture & climb", body: "Submit the flag and rise on the board." },
];

export function LandingPage() {
  const { user } = useAuth();
  const { data } = useApi<PublicInfo>("/api/public");
  if (user) return <Navigate to="/dashboard" replace />;

  const stats = [
    { label: "Challenges", value: data?.stats.challenges, icon: Flag },
    { label: "Hackers", value: data?.stats.users, icon: Users },
    { label: "Flags captured", value: data?.stats.solves, icon: Trophy },
    { label: "Categories", value: data?.stats.categories, icon: Crosshair },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-gray-950">
      <div aria-hidden="true" className="bg-grid pointer-events-none absolute inset-x-0 top-0 h-[720px] [mask-image:linear-gradient(to_bottom,black,transparent)]" />
      <div aria-hidden="true" className="pointer-events-none absolute left-1/2 top-0 h-[480px] w-[960px] -translate-x-1/2 rounded-full bg-brand-600/20 blur-3xl" />

      <header className="relative mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-6">
        <Brand to="/" />
        <nav className="flex items-center gap-2">
          <Button href="/docs" variant="ghost" size="sm" className="hidden sm:inline-flex">
            Docs
          </Button>
          <Button href="/login" variant="ghost" size="sm">
            Sign in
          </Button>
          <Button href="/register" size="sm">
            Create account
          </Button>
        </nav>
      </header>

      <main className="relative mx-auto flex max-w-6xl flex-col gap-24 px-6 pb-24 pt-12">
        <section className="grid items-center gap-12 lg:grid-cols-2">
          <div className="flex flex-col gap-6">
            <p {...reveal(0)} className="inline-flex w-fit animate-fade-up items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1 text-xs font-medium uppercase tracking-wider text-brand-300">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-400" />
              </span>
              Learn · Exploit · Capture
            </p>
            <h1 {...reveal(1)} className="animate-fade-up text-4xl font-semibold tracking-tight text-gray-50 sm:text-6xl">
              Break things.
              <br />
              <span className="text-gradient">Learn why they break.</span>
            </h1>
            <p {...reveal(2)} className="max-w-xl animate-fade-up text-base text-gray-300 sm:text-lg">
              Hands-on penetration testing in private, isolated labs. Exploit real vulnerable targets, capture flags,
              and walk away knowing exactly how to defend against each attack.
            </p>
            <div {...reveal(3)} className="flex animate-fade-up flex-wrap items-center gap-4">
              <Button href="/register" className="group h-12 px-8 text-base">
                Start hacking free
                <ArrowRight aria-hidden="true" className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Button>
              <Button href="/login" variant="secondary" className="h-12 px-8 text-base">
                I have an account
              </Button>
            </div>
          </div>
          <div {...reveal(3)} className="animate-fade-up lg:pl-8">
            <div className="animate-float">
              <TypingTerminal script={script} />
            </div>
          </div>
        </section>

        <section aria-label="Platform stats" className="grid grid-cols-2 gap-4 rounded-2xl border border-gray-800 bg-gray-900/60 p-6 backdrop-blur lg:grid-cols-4">
          {stats.map(({ label, value, icon: Icon }, index) => (
            <div key={label} {...reveal(4 + index)} className="flex animate-fade-up items-center gap-4">
              <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand-500/10 text-brand-400">
                <Icon aria-hidden="true" className="h-6 w-6" />
              </span>
              <span className="flex flex-col">
                <span className="font-mono text-2xl font-semibold text-gray-50">
                  {value === undefined ? "—" : <AnimatedNumber value={value} duration={1400} />}
                </span>
                <span className="text-xs uppercase tracking-wider text-gray-400">{label}</span>
              </span>
            </div>
          ))}
        </section>

        <section className="flex flex-col gap-10">
          <div className="flex flex-col items-center gap-2 text-center">
            <p className="text-xs font-medium uppercase tracking-wider text-brand-400">How it works</p>
            <h2 className="text-3xl font-semibold tracking-tight text-gray-50">From zero to flag in four steps</h2>
          </div>
          <ol className="relative grid gap-6 md:grid-cols-4">
            <span aria-hidden="true" className="absolute left-0 right-0 top-6 hidden h-px bg-gradient-to-r from-transparent via-gray-700 to-transparent md:block" />
            {steps.map(({ icon: Icon, title, body }, index) => (
              <li key={title} className="group relative flex flex-col items-center gap-4 text-center">
                <span className="relative grid h-12 w-12 place-items-center rounded-full border border-gray-700 bg-gray-900 text-brand-400 transition-all duration-300 group-hover:scale-110 group-hover:border-brand-500/60 group-hover:shadow-lg group-hover:shadow-brand-900/40">
                  <Icon aria-hidden="true" className="h-6 w-6" />
                  <span className="absolute -right-1 -top-1 grid h-6 w-6 place-items-center rounded-full bg-brand-600 font-mono text-xs font-bold text-white">
                    {index + 1}
                  </span>
                </span>
                <h3 className="text-base font-semibold text-gray-50">{title}</h3>
                <p className="text-sm text-gray-400">{body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="flex flex-col gap-10">
          <div className="flex flex-col items-center gap-2 text-center">
            <p className="text-xs font-medium uppercase tracking-wider text-brand-400">Why MyCTF</p>
            <h2 className="text-3xl font-semibold tracking-tight text-gray-50">Built for learning by doing</h2>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, body }) => (
              <SpotlightCard key={title} className="flex flex-col gap-4">
                <span className="mb-4 grid h-12 w-12 place-items-center rounded-xl bg-brand-500/10 text-brand-400 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110">
                  <Icon aria-hidden="true" className="h-6 w-6" />
                </span>
                <h3 className="pb-2 text-lg font-semibold text-gray-50">{title}</h3>
                <p className="text-sm text-gray-400">{body}</p>
              </SpotlightCard>
            ))}
          </div>
        </section>

        <section className="relative overflow-hidden rounded-2xl border border-brand-500/30 bg-gradient-to-br from-brand-600/20 via-gray-900 to-gray-900 p-10 text-center">
          <div aria-hidden="true" className="bg-grid absolute inset-0 opacity-60 [mask-image:radial-gradient(circle,black,transparent_70%)]" />
          <div className="relative flex flex-col items-center gap-6">
            <h2 className="text-3xl font-semibold tracking-tight text-gray-50">Your first flag is waiting.</h2>
            <p className="max-w-lg text-gray-300">Create a free account, launch a lab and capture it in minutes.</p>
            <Button href="/register" className="group h-12 px-8 text-base">
              Create free account
              <ArrowRight aria-hidden="true" className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Button>
          </div>
        </section>
      </main>

      <footer className="relative border-t border-gray-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 text-xs text-gray-400 sm:flex-row">
          <span>© {new Date().getFullYear()} MyCTF · Training targets only. Never test systems you don't own.</span>
          <span className="flex gap-6">
            <Link to="/docs" className="hover:text-gray-200">Docs</Link>
            <Link to="/login" className="hover:text-gray-200">Sign in</Link>
          </span>
        </div>
      </footer>
    </div>
  );
}
