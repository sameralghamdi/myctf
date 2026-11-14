import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";
import { Card } from "../ui/Card";
import { Brand } from "./SidebarBrand";

interface AuthLayoutProps {
  title: string;
  description?: string;
  children: ReactNode;
  /** Small links under the card, e.g. "Create account". */
  footer?: ReactNode;
}

/** Centered card used by sign-in, register, forgot and reset pages. */
export function AuthLayout({ title, description, children, footer }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-gray-950 px-6 py-8">
      <Brand to="/" />
      <Card className="flex w-full max-w-md flex-col gap-6 p-8">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-gray-50">{title}</h1>
          {description && <p className="text-sm text-gray-400">{description}</p>}
        </div>
        {children}
      </Card>
      {footer && <div className="flex gap-6 text-sm text-gray-400">{footer}</div>}
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
