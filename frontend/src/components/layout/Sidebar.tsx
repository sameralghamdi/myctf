import { Search, Trophy } from "lucide-react";
import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";
import type { NavItem, NavSection, UserRole, UserSummary } from "../../types/navigation";
import { AnimatedNumber } from "../ui/AnimatedNumber";
import { Kbd } from "../ui/Kbd";
import { SidebarBrand } from "./SidebarBrand";
import { SidebarNavItem } from "./SidebarNavItem";

interface SidebarProps {
  sections: NavSection[];
  currentPath: string;
  role: UserRole;
  /** Mobile drawer state; ignored on large screens where the sidebar is always visible. */
  open: boolean;
  onNavigate: () => void;
  user?: UserSummary | null;
  onSearch?: () => void;
}

function isActive(item: NavItem, path: string): boolean {
  return item.match === "prefix" ? path.startsWith(item.href) : path === item.href;
}

export function Sidebar({ sections, currentPath, role, open, onNavigate, user, onSearch }: SidebarProps) {
  const visible = sections.filter((section) => !section.adminOnly || role === "administrator");

  return (
    <aside
      id="app-sidebar"
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex w-64 flex-col gap-6 overflow-y-auto border-r border-gray-800 bg-gray-900/95 p-4 backdrop-blur transition-transform duration-300 ease-out",
        "lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <SidebarBrand />

      {onSearch && (
        <button
          type="button"
          onClick={() => {
            onNavigate();
            onSearch();
          }}
          className={cn(
            "flex h-10 items-center gap-4 rounded-lg border border-gray-800 bg-gray-950 px-4 text-sm text-gray-400 transition-colors duration-200 hover:border-gray-700 hover:text-gray-200",
            focusRing,
          )}
        >
          <Search aria-hidden="true" className="h-4 w-4" />
          <span className="flex-1 text-left">Quick search</span>
          <Kbd>⌘K</Kbd>
        </button>
      )}

      <nav aria-label="Main" className="flex flex-col gap-6">
        {visible.map((section, index) => (
          <div key={section.title ?? index} className="flex flex-col gap-1">
            {section.title && (
              <h2 className="px-4 pb-1 text-xs font-medium uppercase tracking-wider text-gray-400">
                {section.title}
              </h2>
            )}
            {section.items.map((item) => (
              <SidebarNavItem
                key={item.href}
                item={item}
                active={isActive(item, currentPath)}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        ))}
      </nav>

      {user && (
        <Link
          to="/leaderboard"
          onClick={onNavigate}
          className={cn(
            "group mt-auto flex flex-col gap-2 rounded-xl border border-gray-800 bg-gradient-to-br from-brand-500/10 via-gray-900 to-gray-900 p-4 transition-colors duration-200 hover:border-brand-500/40",
            focusRing,
          )}
        >
          <span className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-gray-400">
            Your standing
            <Trophy aria-hidden="true" className="h-4 w-4 text-brand-400 transition-transform duration-200 group-hover:-rotate-12 group-hover:scale-110" />
          </span>
          <span className="flex items-baseline justify-between">
            <span className="font-mono text-2xl font-semibold text-gray-50">
              <AnimatedNumber value={user.score} />
              <span className="pl-1 text-xs font-normal text-gray-400">pts</span>
            </span>
            <span className="font-mono text-sm text-brand-400">{user.rank ? `#${user.rank}` : "unranked"}</span>
          </span>
        </Link>
      )}
    </aside>
  );
}
