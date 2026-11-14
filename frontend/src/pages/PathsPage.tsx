import { Check, Circle } from "lucide-react";
import { Link } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { useApi } from "../hooks/useApi";
import { cn, focusRing } from "../lib/cn";
import { percent } from "../lib/format";
import type { LearningPath } from "../types/api";

export function PathsPage() {
  const { data, error, loading, reload } = useApi<LearningPath[]>("/api/paths");

  return (
    <PageContainer>
      <PageHeader
        title="Learning paths"
        description="Guided sequences of challenges, from the basics to advanced exploitation."
      />
      {loading && !data ? (
        <PageLoader />
      ) : !data ? (
        <ErrorState message={error ?? "Could not load learning paths."} onRetry={reload} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {data.map((path) => (
            <Card key={path.slug} className="flex flex-col gap-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex flex-col gap-2">
                  <Badge>{path.level}</Badge>
                  <h2 className="text-lg font-semibold text-gray-50">{path.name}</h2>
                </div>
                <div className="flex flex-col items-end">
                  <span className="font-mono text-2xl font-semibold text-brand-400">
                    {path.done}/{path.total}
                  </span>
                  <span className="text-xs text-gray-400">done</span>
                </div>
              </div>
              <p className="text-sm text-gray-400">{path.description}</p>
              <ProgressBar value={percent(path.done, path.total)} label={`${path.name} progress`} />
              <ul className="flex flex-col">
                {path.items.map((item) => (
                  <li key={item.slug}>
                    <Link
                      to={`/challenges/${item.slug}`}
                      className={cn(
                        "flex h-12 items-center justify-between gap-4 rounded-lg px-2 transition-colors duration-200 hover:bg-gray-800/50",
                        focusRing,
                      )}
                    >
                      <span className="flex items-center gap-4 text-sm text-gray-300">
                        {item.solved ? (
                          <Check aria-label="Solved" className="h-4 w-4 text-green-400" />
                        ) : (
                          <Circle aria-label="Not solved" className="h-4 w-4 text-gray-400" />
                        )}
                        {item.name}
                      </span>
                      <DifficultyBadge difficulty={item.difficulty} />
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
