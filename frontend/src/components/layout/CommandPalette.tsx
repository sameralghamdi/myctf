import { CornerDownLeft, Flag, Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { cn } from "../../lib/cn";
import { DIFFICULTY_LABELS } from "../../lib/format";
import type { Challenge } from "../../types/api";
import type { NavSection, UserRole } from "../../types/navigation";
import { Kbd } from "../ui/Kbd";

interface Entry {
  id: string;
  label: string;
  hint: string;
  href: string;
  icon: NavSection["items"][number]["icon"];
  group: "Pages" | "Challenges";
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  sections: NavSection[];
  role: UserRole;
  signedIn: boolean;
}

/** ⌘K / Ctrl+K: jump to any page or challenge from the keyboard. */
export function CommandPalette({ open, onClose, sections, role, signedIn }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [challenges, setChallenges] = useState<Challenge[] | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const list = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    const id = requestAnimationFrame(() => input.current?.focus());
    if (signedIn && challenges === null) {
      api<Challenge[]>("/api/challenges").then(setChallenges).catch(() => setChallenges([]));
    }
    return () => cancelAnimationFrame(id);
  }, [open, signedIn, challenges]);

  const entries = useMemo<Entry[]>(() => {
    const pages: Entry[] = sections
      .filter((section) => !section.adminOnly || role === "administrator")
      .flatMap((section) =>
        section.items.map((item) => ({
          id: `page-${item.href}`,
          label: item.label,
          hint: section.title ?? "Go to",
          href: item.href,
          icon: item.icon,
          group: "Pages" as const,
        })),
      );
    const chals: Entry[] = (challenges ?? []).map((c) => ({
      id: `chal-${c.public_slug}`,
      label: c.name,
      hint: `${c.category_name ?? "General"} · ${DIFFICULTY_LABELS[c.difficulty]} · ${c.points} pts${c.solved ? " · solved" : ""}`,
      href: `/challenges/${c.public_slug}`,
      icon: Flag,
      group: "Challenges" as const,
    }));
    const q = query.trim().toLowerCase();
    const all = [...pages, ...chals];
    if (!q) return [...pages, ...chals.slice(0, 6)];
    return all.filter((e) => `${e.label} ${e.hint}`.toLowerCase().includes(q)).slice(0, 12);
  }, [sections, role, challenges, query]);

  useEffect(() => setActive(0), [query]);
  useEffect(() => {
    list.current?.querySelector<HTMLElement>(`[data-index="${active}"]`)?.scrollIntoView({ block: "nearest" });
  }, [active]);

  if (!open) return null;

  function go(entry: Entry | undefined) {
    if (!entry) return;
    onClose();
    navigate(entry.href);
  }

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) => Math.min(entries.length - 1, i + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => Math.max(0, i - 1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      go(entries[active]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      onClose();
    }
  }

  let lastGroup = "";
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[12vh]" onKeyDown={onKeyDown}>
      <div aria-hidden="true" className="absolute inset-0 animate-fade-in bg-gray-950/70 backdrop-blur-sm" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Search pages and challenges"
        className="relative flex w-full max-w-xl animate-scale-in flex-col overflow-hidden rounded-xl border border-gray-700 bg-gray-900 shadow-2xl shadow-black/60"
      >
        <div className="flex items-center gap-4 border-b border-gray-800 px-4">
          <Search aria-hidden="true" className="h-4 w-4 text-gray-400" />
          <input
            ref={input}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search pages and challenges…"
            aria-label="Search"
            aria-controls="palette-results"
            aria-activedescendant={entries[active] ? `palette-${entries[active].id}` : undefined}
            className="h-12 flex-1 bg-transparent text-sm text-gray-50 placeholder:text-gray-500 focus:outline-none"
          />
          <Kbd>Esc</Kbd>
        </div>
        <ul id="palette-results" ref={list} role="listbox" className="max-h-96 overflow-y-auto p-2">
          {entries.length === 0 && <li className="px-4 py-8 text-center text-sm text-gray-400">No matches for “{query}”.</li>}
          {entries.map((entry, index) => {
            const Icon = entry.icon;
            const header = entry.group !== lastGroup ? entry.group : null;
            lastGroup = entry.group;
            return (
              <li key={entry.id}>
                {header && <p className="px-4 pb-1 pt-2 text-xs font-medium uppercase tracking-wider text-gray-400">{header}</p>}
                <button
                  id={`palette-${entry.id}`}
                  type="button"
                  role="option"
                  aria-selected={index === active}
                  data-index={index}
                  onMouseMove={() => setActive(index)}
                  onClick={() => go(entry)}
                  className={cn(
                    "flex w-full items-center gap-4 rounded-lg px-4 py-2 text-left transition-colors duration-100",
                    index === active ? "bg-brand-500/10 text-gray-50" : "text-gray-300",
                  )}
                >
                  <Icon aria-hidden="true" className={cn("h-4 w-4 shrink-0", index === active ? "text-brand-400" : "text-gray-400")} />
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate text-sm font-medium">{entry.label}</span>
                    <span className="truncate text-xs text-gray-400">{entry.hint}</span>
                  </span>
                  {index === active && <CornerDownLeft aria-hidden="true" className="h-4 w-4 text-gray-400" />}
                </button>
              </li>
            );
          })}
        </ul>
        <div className="flex items-center gap-4 border-t border-gray-800 px-4 py-2 text-xs text-gray-400">
          <span className="flex items-center gap-2"><Kbd>↑</Kbd><Kbd>↓</Kbd> move</span>
          <span className="flex items-center gap-2"><Kbd>↵</Kbd> open</span>
        </div>
      </div>
    </div>
  );
}
