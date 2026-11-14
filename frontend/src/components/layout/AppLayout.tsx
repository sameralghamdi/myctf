import { useCallback, useEffect, useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { navigation } from "../../config/navigation";
import { BreadcrumbContext } from "../../context/BreadcrumbContext";
import { useAuth } from "../../context/AuthContext";
import type { Breadcrumb, NavSection, UserSummary } from "../../types/navigation";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppLayoutProps {
  /** Override the default navigation (defaults to config/navigation.ts). */
  sections?: NavSection[];
}

function defaultCrumbs(pathname: string, sections: NavSection[]): Breadcrumb[] {
  const items = sections.flatMap((section) => section.items);
  const match = items.find((item) =>
    item.match === "prefix" ? pathname.startsWith(item.href) : pathname === item.href,
  );
  return [{ label: "MyCTF", href: "/dashboard" }, { label: match?.label ?? "Not found" }];
}

/**
 * Authenticated app shell: persistent sidebar (drawer below `lg`) + sticky top bar.
 * Routes render into <Outlet />; pages wrap their content in <PageContainer>.
 */
export function AppLayout({ sections = navigation }: AppLayoutProps) {
  const { user, score, rank, signOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [crumbOverride, setCrumbOverride] = useState<Breadcrumb[] | null>(null);

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const toggleDrawer = useCallback(() => setDrawerOpen((open) => !open), []);

  // New page: close the drawer and start at the top.
  useEffect(() => {
    setDrawerOpen(false);
    window.scrollTo(0, 0);
  }, [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeDrawer();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [drawerOpen, closeDrawer]);

  const handleSignOut = useCallback(() => {
    void signOut().then(() => navigate("/login", { replace: true }));
  }, [signOut, navigate]);

  const summary: UserSummary | null = useMemo(
    () => (user ? { username: user.display_name, role: user.role, score, rank } : null),
    [user, score, rank],
  );
  const breadcrumbs = crumbOverride ?? defaultCrumbs(location.pathname, sections);

  return (
    <BreadcrumbContext.Provider value={setCrumbOverride}>
      <div className="flex min-h-screen bg-gray-950">
        {drawerOpen && (
          <div
            aria-hidden="true"
            onClick={closeDrawer}
            className="fixed inset-0 z-30 bg-gray-950/70 lg:hidden"
          />
        )}

        <Sidebar
          sections={sections}
          currentPath={location.pathname}
          role={user?.role ?? "student"}
          open={drawerOpen}
          onNavigate={closeDrawer}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar
            breadcrumbs={breadcrumbs}
            user={summary}
            menuOpen={drawerOpen}
            onMenuToggle={toggleDrawer}
            onSignOut={handleSignOut}
          />
          <main className="flex flex-1 flex-col">
            <Outlet />
          </main>
        </div>
      </div>
    </BreadcrumbContext.Provider>
  );
}
