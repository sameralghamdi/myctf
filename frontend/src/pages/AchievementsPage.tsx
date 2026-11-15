import { Star } from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { useApi } from "../hooks/useApi";
import { cn } from "../lib/cn";
import type { Achievement } from "../types/api";

export function AchievementsPage() {
  const { data, error, loading, reload } = useApi<Achievement[]>("/api/achievements");
  const earned = data?.filter((a) => a.earned).length ?? 0;

  return (
    <PageContainer>
      <PageHeader
        title="Achievements"
        description={data ? `${earned} of ${data.length} earned.` : "Badges you earn along the way."}
      />
      {loading && !data ? (
        <PageLoader />
      ) : !data ? (
        <ErrorState message={error ?? "Could not load achievements."} onRetry={reload} />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {data.map((achievement) => (
            <Card
              key={achievement.slug}
              className={cn(
                "flex flex-col items-center gap-2 text-center",
                !achievement.earned && "opacity-60",
              )}
            >
              <Star
                aria-hidden="true"
                className={cn(
                  "h-8 w-8",
                  achievement.earned ? "fill-brand-400 text-brand-400" : "text-gray-400",
                )}
              />
              <h2 className="text-base font-semibold text-gray-50">{achievement.name}</h2>
              <p className="text-sm text-gray-400">{achievement.description}</p>
              {achievement.earned && <Badge tone="success">Earned</Badge>}
            </Card>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
