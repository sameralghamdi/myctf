import { CheckCircle2, Clock, FlaskConical, Globe, SearchX, SlidersHorizontal, Terminal, X } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DifficultyBadge, StatusBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { SearchInput, Select } from "../components/ui/Field";
import { ErrorState } from "../components/ui/PageLoader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Skeleton } from "../components/ui/Skeleton";
import { useApi } from "../hooks/useApi";
import { cn, focusRing } from "../lib/cn";
import { DIFFICULTY_LABELS, percent } from "../lib/format";
import type { Challenge, ChallengeStatus, Difficulty } from "../types/api";

const statusOf = (c: Challenge): ChallengeStatus => c.status ?? (c.solved ? "solved" : "new");

const DIFFICULTY_ORDER: Difficulty[] = ["very_easy", "easy", "medium", "hard", "insane"];
const DIFFICULTY_ACCENT: Record<Difficulty, string> = {
  very_easy: "from-gray-400/60",
  easy: "from-green-400/70",
  medium: "from-yellow-400/70",
  hard: "from-red-400/80",
  insane: "from-fuchsia-400/80",
};

type Sort = "recommended" | "points-asc" | "points-desc" | "name";

function Chip({ active, onClick, children, count }: { active: boolean; onClick: () => void; children: ReactNode; count?: number }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "inline-flex h-8 shrink-0 items-center gap-2 rounded-full border px-4 text-sm font-medium transition-all duration-200 active:scale-95",
        focusRing,
        active
          ? "border-brand-500/50 bg-brand-500/15 text-brand-200 shadow-sm shadow-brand-900/30"
          : "border-gray-800 bg-gray-900 text-gray-400 hover:border-gray-700 hover:text-gray-50",
      )}
    >
      {children}
      {count !== undefined && (
        <span className={cn("rounded-full px-2 font-mono text-xs", active ? "bg-brand-500/20 text-brand-200" : "bg-gray-800 text-gray-400")}>
          {count}
        </span>
      )}
    </button>
  );
}

function LabIcon({ c }: { c: Challenge }) {
  if (!c.has_lab) return null;
  const Icon = c.has_web_ui ? FlaskConical : c.is_shell ? Terminal : Globe;
  const label = c.has_web_ui ? "Web + Terminal" : c.is_shell ? "Terminal" : "Live lab";
  return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-400" title={label}>
      <Icon aria-hidden="true" className="h-4 w-4" />
      {label}
    </span>
  );
}

export function ChallengesPage() {
  const { data, error, loading, reload } = useApi<Challenge[]>("/api/challenges");
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const category = params.get("category") ?? "all";
  const difficulty = params.get("difficulty") ?? "all";
  const status = params.get("status") ?? "all";
  const [sort, setSort] = useState<Sort>("recommended");

  // Filters live in the URL so a filtered view can be shared and survives back/forward.
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value === "all") next.delete(key);
    else next.set(key, value);
    setParams(next, { replace: true });
  };

  const all = data ?? [];
  const solvedCount = all.filter((c) => statusOf(c) === "solved").length;

  const categories = useMemo(() => {
    const seen = new Map<string, { name: string; count: number }>();
    for (const c of all) {
      if (!c.category) continue;
      const entry = seen.get(c.category) ?? { name: c.category_name ?? c.category, count: 0 };
      entry.count += 1;
      seen.set(c.category, entry);
    }
    return [...seen.entries()];
  }, [all]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = all.filter(
      (c) =>
        (category === "all" || c.category === category) &&
        (difficulty === "all" || c.difficulty === difficulty) &&
        (status === "all" || statusOf(c) === status) &&
        (!q || `${c.name} ${c.category_name ?? ""}`.toLowerCase().includes(q)),
    );
    const byDifficulty = (c: Challenge) => DIFFICULTY_ORDER.indexOf(c.difficulty);
    return list.sort((a, b) => {
      if (sort === "points-asc") return a.points - b.points;
      if (sort === "points-desc") return b.points - a.points;
      if (sort === "name") return a.name.localeCompare(b.name);
      // Recommended: unsolved first, then easiest, then cheapest.
      return Number(a.solved) - Number(b.solved) || byDifficulty(a) - byDifficulty(b) || a.points - b.points;
    });
  }, [all, query, category, difficulty, status, sort]);

  const filtered = category !== "all" || difficulty !== "all" || status !== "all" || query.trim() !== "";
  const clearAll = () => {
    setQuery("");
    setParams(new URLSearchParams(), { replace: true });
  };

  return (
    <PageContainer>
      <PageHeader title="Challenges" description="Pick a target, start its lab, and capture the flag." />

      {data && (
        <Card className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <span className="grid h-12 w-12 place-items-center rounded-xl bg-green-500/10 text-green-400">
              <CheckCircle2 aria-hidden="true" className="h-6 w-6" />
            </span>
            <div className="flex flex-col">
              <span className="text-sm text-gray-400">Your progress</span>
              <span className="text-lg font-semibold text-gray-50">
                {solvedCount} <span className="text-gray-400">of</span> {all.length} solved
              </span>
            </div>
          </div>
          <div className="w-full sm:w-72">
            <ProgressBar value={percent(solvedCount, all.length)} tone="success" label="Challenges solved" />
          </div>
        </Card>
      )}

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="relative flex-1">
            <SlidersHorizontal aria-hidden="true" className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <SearchInput
              aria-label="Search challenges"
              placeholder="Search by name or category…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="pl-10"
            />
          </div>
          <Select aria-label="Sort" value={sort} onChange={(event) => setSort(event.target.value as Sort)} className="sm:w-56">
            <option value="recommended">Sort: Recommended</option>
            <option value="points-asc">Sort: Points (low → high)</option>
            <option value="points-desc">Sort: Points (high → low)</option>
            <option value="name">Sort: Name</option>
          </Select>
        </div>

        <div className="-mx-6 flex gap-2 overflow-x-auto px-6 pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0" role="group" aria-label="Category">
          <Chip active={category === "all"} onClick={() => setFilter("category", "all")} count={all.length}>
            All
          </Chip>
          {categories.map(([slug, { name, count }]) => (
            <Chip key={slug} active={category === slug} onClick={() => setFilter("category", category === slug ? "all" : slug)} count={count}>
              {name}
            </Chip>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex flex-wrap gap-2" role="group" aria-label="Difficulty">
            {DIFFICULTY_ORDER.filter((d) => all.some((c) => c.difficulty === d)).map((d) => (
              <Chip key={d} active={difficulty === d} onClick={() => setFilter("difficulty", difficulty === d ? "all" : d)}>
                {DIFFICULTY_LABELS[d]}
              </Chip>
            ))}
          </div>
          <span aria-hidden="true" className="mx-2 hidden h-6 w-px bg-gray-800 sm:block" />
          <div className="flex flex-wrap gap-2" role="group" aria-label="Status">
            {(
              [
                ["new", "New"],
                ["progress", "In progress"],
                ["solved", "Solved"],
              ] as const
            ).map(([value, label]) => (
              <Chip key={value} active={status === value} onClick={() => setFilter("status", status === value ? "all" : value)}>
                {label}
              </Chip>
            ))}
          </div>
          {filtered && (
            <button
              type="button"
              onClick={clearAll}
              className={cn("ml-auto inline-flex items-center gap-1 rounded text-sm text-gray-400 transition-colors hover:text-brand-400", focusRing)}
            >
              <X aria-hidden="true" className="h-4 w-4" /> Clear filters
            </button>
          )}
        </div>
      </div>

      {loading && !data ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : !data ? (
        <ErrorState message={error ?? "Could not load challenges."} onRetry={reload} />
      ) : visible.length === 0 ? (
        <Card>
          <EmptyState
            icon={SearchX}
            title="No challenges match"
            description="Try another search term or loosen a filter."
            action={<Button variant="secondary" size="sm" onClick={clearAll}>Clear filters</Button>}
          />
        </Card>
      ) : (
        <>
          <p className="-mb-4 text-xs text-gray-400" aria-live="polite">
            Showing {visible.length} of {all.length}
          </p>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((c, index) => {
              const solved = statusOf(c) === "solved";
              return (
                <Link
                  key={c.slug}
                  to={`/challenges/${c.public_slug}`}
                  className={cn("group block animate-fade-up rounded-xl", focusRing)}
                  style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}
                >
                  <Card
                    interactive
                    className={cn(
                      "relative flex h-full flex-col gap-4 overflow-hidden",
                      solved && "border-green-500/20",
                    )}
                  >
                    <span
                      aria-hidden="true"
                      className={cn("absolute inset-x-0 top-0 h-1 bg-gradient-to-r to-transparent", DIFFICULTY_ACCENT[c.difficulty])}
                    />
                    {solved && (
                      <span aria-hidden="true" className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-green-500/10 blur-xl" />
                    )}
                    <div className="flex items-center justify-between gap-2">
                      <Badge>{c.category_name ?? "General"}</Badge>
                      <StatusBadge status={statusOf(c)} />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-50 transition-colors duration-200 group-hover:text-brand-300">
                      {c.name}
                    </h2>
                    <div className="flex flex-wrap items-center gap-4">
                      <LabIcon c={c} />
                      {c.est_minutes ? (
                        <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                          <Clock aria-hidden="true" className="h-4 w-4" />~{c.est_minutes} min
                        </span>
                      ) : null}
                    </div>
                    <div className="mt-auto flex items-center justify-between gap-2 border-t border-gray-800 pt-4">
                      <DifficultyBadge difficulty={c.difficulty} />
                      <span className="font-mono text-base font-semibold text-brand-400 transition-transform duration-200 group-hover:scale-110">
                        {c.points} pts
                      </span>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        </>
      )}
    </PageContainer>
  );
}
