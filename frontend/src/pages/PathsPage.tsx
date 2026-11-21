import { ArrowRight, Check, Route } from "lucide-react";
import { Link } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/PageLoader";
import { ProgressRing } from "../components/ui/ProgressRing";
import { Skeleton } from "../components/ui/Skeleton";
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
        description="Guided sequences of challenges, from the basics to advanced exploitation. Follow the line, one flag at a time."
      />
      {loading && !data ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      ) : !data ? (
        <ErrorState message={error ?? "Could not load learning paths."} onRetry={reload} />
      ) : data.length === 0 ? (
        <Card>
          <EmptyState icon={Route} title="No paths yet" description="Learning paths will appear here." />
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {data.map((path, pathIndex) => {
            const nextItem = path.items.find((item) => !item.solved);
            const complete = path.total > 0 && path.done === path.total;
            return (
              <Card
                key={path.slug}
                className={cn("flex animate-fade-up flex-col gap-6", complete && "border-green-500/30")}
                style={{ animationDelay: `${pathIndex * 80}ms` }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex flex-col items-start gap-2">
                    <Badge tone={complete ? "success" : "neutral"}>{complete ? "Completed" : path.level}</Badge>
                    <h2 className="text-lg font-semibold text-gray-50">{path.name}</h2>
                    <p className="text-sm text-gray-400">{path.description}</p>
                  </div>
                  <ProgressRing value={percent(path.done, path.total)} size={72} stroke={6} label={`${path.name} progress`}>
                    <span className="font-mono text-sm font-semibold text-gray-50">
                      {path.done}/{path.total}
                    </span>
                  </ProgressRing>
                </div>

                <ol className="relative flex flex-col">
                  {path.items.map((item, index) => {
                    const isNext = item === nextItem;
                    const last = index === path.items.length - 1;
                    return (
                      <li key={item.slug} className="relative">
                        {!last && (
                          <span
                            aria-hidden="true"
                            className={cn("absolute left-6 top-10 h-full w-px -translate-x-1/2", item.solved ? "bg-green-500/40" : "bg-gray-800")}
                          />
                        )}
                        <Link
                          to={`/challenges/${item.public_slug}`}
                          className={cn(
                            "group relative flex items-center gap-4 rounded-lg px-2 py-2 transition-colors duration-200 hover:bg-gray-800/50",
                            isNext && "bg-brand-500/5",
                            focusRing,
                          )}
                        >
                          <span
                            className={cn(
                              "relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full border-2 font-mono text-xs font-semibold transition-transform duration-200 group-hover:scale-110",
                              item.solved
                                ? "border-green-500 bg-green-500/15 text-green-400"
                                : isNext
                                  ? "border-brand-500 bg-gray-900 text-brand-300"
                                  : "border-gray-700 bg-gray-900 text-gray-400",
                            )}
                          >
                            {item.solved ? <Check aria-label="Solved" className="h-4 w-4" /> : index + 1}
                            {isNext && <span aria-hidden="true" className="absolute inset-0 animate-ping rounded-full border-2 border-brand-500/60" />}
                          </span>
                          <span className="flex min-w-0 flex-1 flex-col">
                            <span className={cn("truncate text-sm font-medium", item.solved ? "text-gray-300" : "text-gray-50")}>{item.name}</span>
                            {isNext && <span className="text-xs text-brand-300">Up next</span>}
                          </span>
                          <DifficultyBadge difficulty={item.difficulty} />
                          <span className="hidden w-14 text-right font-mono text-xs text-gray-400 sm:block">{item.points} pts</span>
                        </Link>
                      </li>
                    );
                  })}
                </ol>

                {nextItem && (
                  <Button href={`/challenges/${nextItem.public_slug}`} className="group mt-auto self-start">
                    {path.done === 0 ? "Start path" : "Continue path"}
                    <ArrowRight aria-hidden="true" className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                  </Button>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
