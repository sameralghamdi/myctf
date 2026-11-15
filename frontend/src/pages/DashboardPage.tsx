import { Flag } from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionLabel } from "../components/ui/SectionLabel";
import { StatCard } from "../components/ui/StatCard";
import { Table, Td, Tr } from "../components/ui/Table";
import { useApi } from "../hooks/useApi";
import { formatDate, percent } from "../lib/format";
import type { DashboardData } from "../types/api";
import { Link } from "react-router-dom";

export function DashboardPage() {
  const { data, error, loading, reload } = useApi<DashboardData>("/api/dashboard");

  if (loading && !data) {
    return (
      <PageContainer>
        <PageLoader />
      </PageContainer>
    );
  }
  if (!data) {
    return (
      <PageContainer>
        <ErrorState message={error ?? "Could not load the dashboard."} onRetry={reload} />
      </PageContainer>
    );
  }

  const next = data.in_progress ?? data.recommended;
  const solves = data.recent.filter((entry) => Boolean(entry.correct));

  return (
    <PageContainer>
      <PageHeader
        title="Dashboard"
        description="Track your progress, pick up where you left off, and see how you rank."
        actions={<Button href="/challenges">Browse challenges</Button>}
      />

      <section aria-label="Your stats" className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total score" value={data.score} tone="brand" />
        <StatCard label="Global rank" value={data.rank ? `#${data.rank}` : "—"} />
        <StatCard
          label="Challenges solved"
          value={`${data.completed} / ${data.total}`}
          tone="success"
          sub={`${data.completion_pct}% complete`}
        />
        <StatCard
          label="Day streak"
          value={data.streak}
          sub={data.streak ? "Keep it going" : "Solve one today"}
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <SectionLabel>Continue where you left off</SectionLabel>
          {next ? (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-col gap-2">
                <p className="text-lg font-semibold text-gray-50">{next.name}</p>
                <div className="flex flex-wrap items-center gap-2">
                  <DifficultyBadge difficulty={next.difficulty} />
                  {next.category_name && <Badge>{next.category_name}</Badge>}
                  <span className="font-mono text-sm text-brand-400">{next.points} pts</span>
                </div>
              </div>
              <Button href={`/challenges/${next.slug}`}>
                {data.in_progress ? "Resume" : "Start"}
              </Button>
            </div>
          ) : (
            <EmptyState
              icon={Flag}
              title="All caught up"
              description="You have solved every published challenge."
            />
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <SectionLabel>Recent solves</SectionLabel>
          {solves.length > 0 ? (
            <Table>
              <tbody>
                {solves.map((entry) => (
                  <Tr key={`${entry.slug}-${entry.created_at}`}>
                    <Td>
                      <Link
                        to={`/challenges/${entry.slug}`}
                        className="text-brand-400 hover:underline"
                      >
                        {entry.name}
                      </Link>
                    </Td>
                    <Td className="text-right text-gray-400">{formatDate(entry.created_at)}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState
              icon={Flag}
              title="No solves yet"
              description="Capture your first flag to see it here."
            />
          )}
        </Card>
      </section>

      <Card className="flex flex-col gap-6">
        <SectionLabel>Progress by category</SectionLabel>
        <div className="grid gap-6 md:grid-cols-2">
          {Object.entries(data.skills).map(([skill, stat]) => (
            <div key={skill} className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="font-medium text-gray-50">{skill}</span>
                <span className="text-gray-400">
                  {stat.solved}/{stat.total} · {stat.earned}/{stat.available} pts
                </span>
              </div>
              <ProgressBar value={percent(stat.earned, stat.available)} label={`${skill} progress`} />
            </div>
          ))}
        </div>
      </Card>

      {data.achievements.length > 0 && (
        <Card className="flex flex-col gap-4">
          <SectionLabel>Recent achievements</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {data.achievements.map((achievement) => (
              <span key={achievement.slug} title={achievement.description}>
                <Badge tone="brand">★ {achievement.name}</Badge>
              </span>
            ))}
          </div>
        </Card>
      )}
    </PageContainer>
  );
}
