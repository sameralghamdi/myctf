import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";

export function Brand({ to = "/dashboard" }: { to?: string }) {
  return (
    <Link to={to} className={cn("flex items-center gap-4 rounded-lg px-2 py-2", focusRing)}>
      <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-600 font-mono text-lg font-bold text-white">
        M
      </span>
      <span className="flex flex-col">
        <span className="text-base font-semibold text-gray-50">MyCTF</span>
        <span className="text-xs font-medium uppercase tracking-wider text-gray-400">
          Learn · Exploit · Capture
        </span>
      </span>
    </Link>
  );
}

export { Brand as SidebarBrand };
