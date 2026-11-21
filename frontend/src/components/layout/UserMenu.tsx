import { useCallback, useRef, useState } from "react";
import { LogOut, UserRound } from "lucide-react";
import { Link } from "react-router-dom";
import { useDismiss } from "../../hooks/useDismiss";
import { cn, focusRing } from "../../lib/cn";
import type { UserSummary } from "../../types/navigation";
import { Avatar } from "../ui/Avatar";

interface UserMenuProps {
  user: UserSummary;
  profileHref: string;
  onSignOut: () => void;
}

const itemClasses = cn(
  "flex h-10 w-full items-center gap-4 rounded-lg px-4 text-left text-sm text-gray-300",
  "transition-colors duration-200 hover:bg-gray-800 hover:text-gray-50",
  focusRing,
);

export function UserMenu({ user, profileHref, onSignOut }: UserMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const close = useCallback(() => setOpen(false), []);
  useDismiss(ref, open, close);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-label="Account menu"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className={cn("rounded-full transition-opacity duration-200 hover:opacity-80", focusRing)}
      >
        <Avatar name={user.username} src={user.avatarUrl} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 rounded-xl border border-gray-800 bg-gray-900 p-2 shadow-md"
        >
          <div className="border-b border-gray-800 px-4 pb-2 pt-2">
            <p className="truncate text-sm font-medium text-gray-50">{user.username}</p>
            <p className="text-xs capitalize text-gray-400">{user.role}</p>
          </div>
          <div className="flex flex-col pt-2">
            <Link role="menuitem" to={profileHref} onClick={close} className={itemClasses}>
              <UserRound aria-hidden="true" className="h-4 w-4" />
              Profile
            </Link>
            <button type="button" role="menuitem" onClick={onSignOut} className={itemClasses}>
              <LogOut aria-hidden="true" className="h-4 w-4" />
              Log out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
