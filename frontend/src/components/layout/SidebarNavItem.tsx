import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";
import type { NavItem } from "../../types/navigation";

interface SidebarNavItemProps {
  item: NavItem;
  active: boolean;
  onNavigate?: () => void;
}

export function SidebarNavItem({ item, active, onNavigate }: SidebarNavItemProps) {
  const Icon = item.icon;
  return (
    <Link
      to={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex h-10 items-center gap-4 rounded-lg px-4 text-sm font-medium transition-all duration-200",
        focusRing,
        active
          ? "bg-brand-500/10 text-brand-300"
          : "text-gray-400 hover:translate-x-1 hover:bg-gray-800/70 hover:text-gray-50",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "absolute inset-y-2 left-0 w-1 rounded-r-full bg-brand-500 transition-all duration-300",
          active ? "opacity-100" : "scale-y-0 opacity-0",
        )}
      />
      <Icon
        aria-hidden="true"
        className={cn(
          "h-4 w-4 shrink-0 transition-transform duration-200",
          active ? "text-brand-400" : "group-hover:scale-110",
        )}
      />
      {item.label}
    </Link>
  );
}
