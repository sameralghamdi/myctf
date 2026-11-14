import { cn } from "../../lib/cn";
import type { NavItem, NavSection, UserRole } from "../../types/navigation";
import { SidebarBrand } from "./SidebarBrand";
import { SidebarNavItem } from "./SidebarNavItem";

interface SidebarProps {
  sections: NavSection[];
  currentPath: string;
  role: UserRole;
  /** Mobile drawer state; ignored on large screens where the sidebar is always visible. */
  open: boolean;
  onNavigate: () => void;
}

function isActive(item: NavItem, path: string): boolean {
  return item.match === "prefix" ? path.startsWith(item.href) : path === item.href;
}

export function Sidebar({ sections, currentPath, role, open, onNavigate }: SidebarProps) {
  const visible = sections.filter((section) => !section.adminOnly || role === "administrator");

  return (
    <aside
      id="app-sidebar"
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex w-64 flex-col gap-6 overflow-y-auto border-r border-gray-800 bg-gray-900 p-4 transition-transform duration-200",
        "lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <SidebarBrand />
      <nav aria-label="Main" className="flex flex-col gap-6">
        {visible.map((section, index) => (
          <div key={section.title ?? index} className="flex flex-col gap-2">
            {section.title && (
              <h2 className="px-4 text-xs font-medium uppercase tracking-wider text-gray-400">
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
    </aside>
  );
}
