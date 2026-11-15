import { SearchX } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { DifficultyBadge, StatusBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { SearchInput, Select } from "../components/ui/Field";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { useApi } from "../hooks/useApi";
import { cn, focusRing } from "../lib/cn";
import { DIFFICULTY_LABELS } from "../lib/format";
import type { Challenge, ChallengeStatus } from "../types/api";

const statusOf = (c: Challenge): ChallengeStatus => c.status ?? (c.solved ? "solved" : "new");

export function ChallengesPage() {
  const { data, error, loading, reload } = useApi<Challenge[]>("/api/challenges");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [difficulty, setDifficulty] = useState("all");
  const [status, setStatus] = useState("all");

  const categories = useMemo(() => {
    const seen = new Map<string, string>();
    for (const c of data ?? []) if (c.category) seen.set(c.category, c.category_name ?? c.category);
    return [...seen.entries()];
  }, [data]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (data ?? [])
      .filter(
        (c) =>
          (category === "all" || c.category === category) &&
          (difficulty === "all" || c.difficulty === difficulty) &&
          (status === "all" || statusOf(c) === status) &&
          (!q || c.name.toLowerCase().includes(q)),
      )
      .sort(
        (a, b) =>
          (a.category_name ?? "").localeCompare(b.category_name ?? "") || a.points - b.points,
      );
  }, [data, query, category, difficulty, status]);

  return (
    <PageContainer>
      <PageHeader
        title="Challenges"
        description="Pick a target, start its lab, and capture the flag."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SearchInput
          aria-label="Search challenges"
          placeholder="Search challenges…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Select
          aria-label="Category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          <option value="all">All categories</option>
          {categories.map(([slug, name]) => (
            <option key={slug} value={slug}>
              {name}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Difficulty"
          value={difficulty}
          onChange={(event) => setDifficulty(event.target.value)}
        >
          <option value="all">All difficulties</option>
          {Object.entries(DIFFICULTY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="all">All status</option>
          <option value="new">New</option>
          <option value="progress">In progress</option>
          <option value="solved">Solved</option>
        </Select>
      </div>

      {loading && !data ? (
        <PageLoader />
      ) : !data ? (
        <ErrorState message={error ?? "Could not load challenges."} onRetry={reload} />
      ) : visible.length === 0 ? (
        <Card>
          <EmptyState
            icon={SearchX}
            title="No challenges match"
            description="Try clearing a filter or search term."
          />
        </Card>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((c) => (
            <Link
              key={c.slug}
              to={`/challenges/${c.slug}`}
              className={cn("block rounded-xl", focusRing)}
            >
              <Card interactive className="flex h-full flex-col gap-4">
                <div className="flex items-center justify-between gap-2">
                  <Badge>{c.category_name ?? "General"}</Badge>
                  <StatusBadge status={statusOf(c)} />
                </div>
                <h2 className="text-base font-semibold text-gray-50">{c.name}</h2>
                <div className="mt-auto flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <DifficultyBadge difficulty={c.difficulty} />
                    {c.has_lab && <Badge tone="brand">{c.is_shell ? "Terminal" : "Live lab"}</Badge>}
                  </div>
                  <span className="font-mono text-sm text-brand-400">{c.points} pts</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
