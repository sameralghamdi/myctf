import { Lock, Star } from "lucide-react";
import { useState } from "react";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { ErrorState } from "../components/ui/PageLoader";
import { ProgressRing } from "../components/ui/ProgressRing";
import { SegmentedControl } from "../components/ui/SegmentedControl";
import { Skeleton } from "../components/ui/Skeleton";
import { useApi } from "../hooks/useApi";
import { cn } from "../lib/cn";
import { percent } from "../lib/format";
import type { Achievement } from "../types/api";

type Filter = "all" | "earned" | "locked";

export function AchievementsPage() {
  const { data, error, loading, reload } = useApi<Achievement[]>("/api/achievements");
  const [filter, setFilter] = useState<Filter>("all");
  const earned = data?.filter((a) => a.earned).length ?? 0;
  const shown = (data ?? []).filter((a) => filter === "all" || (filter === "earned" ? a.earned : !a.earned));

  return (
    <PageContainer>
      <PageHeader title="Achievements" description="Badges you earn along the way. Collect them all." />
      {loading && !data ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : !data ? (
        <ErrorState message={error ?? "Could not load achievements."} onRetry={reload} />
      ) : (
        <>
          <Card className="flex flex-col items-center gap-6 sm:flex-row">
            <ProgressRing value={percent(earned, data.length)} size={112} label="Achievements earned">
              <span className="font-mono text-2xl font-semibold text-gray-50">
                {earned}
                <span className="text-sm text-gray-400">/{data.length}</span>
              </span>
            </ProgressRing>
            <div className="flex flex-1 flex-col gap-2 text-center sm:text-left">
              <p className="text-lg font-semibold text-gray-50">
                {earned === data.length ? "Collection complete!" : `${data.length - earned} badges left to unlock`}
              </p>
              <p className="text-sm text-gray-400">Solve challenges, keep a streak and grab first bloods to earn more.</p>
            </div>
            <div className="w-full sm:w-auto">
              <SegmentedControl
                label="Show"
                value={filter}
                onChange={setFilter}
                options={[
                  { value: "all", label: "All" },
                  { value: "earned", label: "Earned" },
                  { value: "locked", label: "Locked" },
                ]}
              />
            </div>
          </Card>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {shown.map((achievement, index) => (
              <div
                key={achievement.slug}
                className={cn(
                  "group relative flex animate-fade-up flex-col items-center gap-2 overflow-hidden rounded-xl border p-6 text-center transition-all duration-300 hover:-translate-y-1",
                  achievement.earned
                    ? "border-brand-500/30 bg-gradient-to-b from-brand-500/10 to-gray-900 hover:shadow-lg hover:shadow-brand-900/30"
                    : "border-gray-800 bg-gray-900 hover:border-gray-700",
                )}
                style={{ animationDelay: `${Math.min(index, 12) * 50}ms` }}
              >
                <span
                  className={cn(
                    "grid h-16 w-16 place-items-center rounded-full transition-transform duration-500",
                    achievement.earned
                      ? "bg-brand-500/15 text-brand-300 group-hover:rotate-[360deg]"
                      : "bg-gray-800 text-gray-400 group-hover:scale-105",
                  )}
                >
                  {achievement.earned ? (
                    <Star aria-hidden="true" className="h-8 w-8 fill-current" />
                  ) : (
                    <Lock aria-hidden="true" className="h-6 w-6" />
                  )}
                </span>
                <h2 className="text-base font-semibold text-gray-50">{achievement.name}</h2>
                <p className="text-sm text-gray-400">{achievement.description}</p>
                <span
                  className={cn(
                    "mt-auto rounded-full px-2 text-xs font-medium",
                    achievement.earned ? "bg-green-500/10 text-green-400" : "bg-gray-800 text-gray-400",
                  )}
                >
                  {achievement.earned ? "Earned" : "Locked"}
                </span>
              </div>
            ))}
          </div>
          {shown.length === 0 && <p className="text-center text-sm text-gray-400">Nothing here yet.</p>}
        </>
      )}
    </PageContainer>
  );
}
