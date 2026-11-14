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
        "flex h-10 items-center gap-4 rounded-lg px-4 text-sm font-medium transition-colors duration-200",
        focusRing,
        active
          ? "bg-brand-500/10 text-brand-400 ring-1 ring-inset ring-brand-500/30"
          : "text-gray-400 hover:bg-gray-800 hover:text-gray-50",
      )}
    >
      <Icon aria-hidden="true" className="h-4 w-4 shrink-0" />
      {item.label}
    </Link>
  );
}
