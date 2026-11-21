import { CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";
import { TypingTerminal } from "../ui/TypingTerminal";
import { Brand } from "./SidebarBrand";

interface AuthLayoutProps {
  title: string;
  description?: string;
  children: ReactNode;
  /** Small links under the card, e.g. "Create account". */
  footer?: ReactNode;
}

const perks = [
  "Private, isolated labs with per-session flags",
  "Browser target + in-browser terminal",
  "Live scoreboard, first bloods and achievements",
];

/** Split screen: brand panel on the left (large screens), form on the right. */
export function AuthLayout({ title, description, children, footer }: AuthLayoutProps) {
  return (
    <div className="grid min-h-screen bg-gray-950 lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden border-r border-gray-800 bg-gray-900 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div aria-hidden="true" className="bg-grid absolute inset-0 [mask-image:linear-gradient(to_bottom,black,transparent)]" />
        <div aria-hidden="true" className="absolute -left-24 top-1/3 h-96 w-96 rounded-full bg-brand-600/20 blur-3xl" />
        <div className="relative">
          <Brand to="/" />
        </div>
        <div className="relative flex flex-col gap-8">
          <h2 className="text-3xl font-semibold tracking-tight text-gray-50">
            Hack legally.
            <br />
            <span className="text-gradient">Learn for real.</span>
          </h2>
          <ul className="flex flex-col gap-4">
            {perks.map((perk, index) => (
              <li key={perk} className="flex animate-fade-up items-center gap-4 text-sm text-gray-300" style={{ animationDelay: `${index * 100}ms` }}>
                <CheckCircle2 aria-hidden="true" className="h-4 w-4 shrink-0 text-green-400" />
                {perk}
              </li>
            ))}
          </ul>
          <TypingTerminal
            compact
            script={[
              { kind: "cmd", text: "whoami" },
              { kind: "out", text: "future-pentester" },
              { kind: "cmd", text: "start-lab" },
              { kind: "ok", text: "✓ ready when you are" },
            ]}
          />
        </div>
        <p className="relative text-xs text-gray-400">Training targets only. Never test systems you don't own.</p>
      </aside>

      <div className="flex flex-col items-center justify-center gap-8 px-6 py-12">
        <div className="lg:hidden">
          <Brand to="/" />
        </div>
        <div className="flex w-full max-w-md animate-fade-up flex-col gap-6 rounded-2xl border border-gray-800 bg-gray-900/80 p-8 shadow-xl shadow-black/40 backdrop-blur">
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-gray-50">{title}</h1>
            {description && <p className="text-sm text-gray-400">{description}</p>}
          </div>
          {children}
        </div>
        {footer && <div className="flex gap-6 text-sm text-gray-400">{footer}</div>}
      </div>
    </div>
  );
}

export function AuthLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className={cn(
        "rounded text-gray-300 transition-colors duration-200 hover:text-brand-400",
        focusRing,
      )}
    >
      {children}
    </Link>
  );
}
