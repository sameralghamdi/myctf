import { Menu, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";
import type { Breadcrumb, UserSummary } from "../../types/navigation";
import { Button } from "../ui/Button";
import { Kbd } from "../ui/Kbd";
import { ScoreChip } from "../ui/ScoreChip";
import { UserMenu } from "./UserMenu";

interface TopbarProps {
  breadcrumbs: Breadcrumb[];
  user: UserSummary | null;
  menuOpen: boolean;
  onMenuToggle: () => void;
  onSignOut: () => void;
  onSearch?: () => void;
}

export function Topbar({ breadcrumbs, user, menuOpen, onMenuToggle, onSignOut, onSearch }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-gray-800 bg-gray-950/80 px-6 backdrop-blur lg:px-8">
      <div className="flex items-center gap-4">
        <button
          type="button"
          aria-label="Toggle navigation"
          aria-controls="app-sidebar"
          aria-expanded={menuOpen}
          onClick={onMenuToggle}
          className={cn(
            "grid h-10 w-10 place-items-center rounded-lg text-gray-300 transition-colors duration-200 hover:bg-gray-800 hover:text-gray-50 lg:hidden",
            focusRing,
          )}
        >
          <Menu aria-hidden="true" className="h-6 w-6" />
        </button>

        <nav aria-label="Breadcrumb">
          <ol className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-400">
            {breadcrumbs.map((crumb, index) => {
              const last = index === breadcrumbs.length - 1;
              return (
                <li key={`${crumb.label}-${index}`} className="flex items-center gap-2">
                  {index > 0 && <span aria-hidden="true">/</span>}
                  {crumb.href && !last ? (
                    <Link
                      to={crumb.href}
                      className={cn(
                        "rounded transition-colors duration-200 hover:text-gray-50",
                        focusRing,
                      )}
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span aria-current={last ? "page" : undefined} className={last ? "text-gray-300" : undefined}>
                      {crumb.label}
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {onSearch && (
          <button
            type="button"
            onClick={onSearch}
            aria-label="Search pages and challenges"
            className={cn(
              "flex h-8 items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-2 text-sm text-gray-400 transition-colors duration-200 hover:border-gray-700 hover:text-gray-200 md:pl-4",
              focusRing,
            )}
          >
            <Search aria-hidden="true" className="h-4 w-4" />
            <span className="hidden md:inline">Search</span>
            <span className="hidden md:inline-flex"><Kbd>⌘K</Kbd></span>
          </button>
        )}
        {user ? (
          <>
            <ScoreChip score={user.score} rank={user.rank} />
            <UserMenu user={user} profileHref="/profile" onSignOut={onSignOut} />
          </>
        ) : (
          <Button href="/login" size="sm">
            Sign in
          </Button>
        )}
      </div>
    </header>
  );
}
