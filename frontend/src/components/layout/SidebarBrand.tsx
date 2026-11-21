import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";

export function Brand({ to = "/dashboard" }: { to?: string }) {
  return (
    <Link to={to} className={cn("group flex items-center gap-4 rounded-lg px-2 py-2", focusRing)}>
      <span className="relative grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 font-mono text-lg font-bold text-white shadow-lg shadow-brand-900/40 transition-transform duration-300 group-hover:rotate-6 group-hover:scale-105">
        M
        <span aria-hidden="true" className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-green-400 ring-2 ring-gray-900" />
      </span>
      <span className="flex flex-col">
        <span className="text-base font-semibold tracking-tight text-gray-50">MyCTF</span>
        <span className="text-xs font-medium uppercase tracking-wider text-gray-400">
          Learn · Exploit · Capture
        </span>
      </span>
    </Link>
  );
}

export { Brand as SidebarBrand };
