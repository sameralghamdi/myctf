import {
  ArrowRight,
  CalendarDays,
  Check,
  Crosshair,
  Droplet,
  Flag,
  Flame,
  Medal,
  Sparkles,
  Star,
  Target,
  Trophy,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import { ActivityHeatmap } from "../components/charts/ActivityHeatmap";
import { PageContainer } from "../components/layout/PageContainer";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/PageLoader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { ProgressRing } from "../components/ui/ProgressRing";
import { SectionLabel } from "../components/ui/SectionLabel";
import { PageSkeleton } from "../components/ui/Skeleton";
import { StatCard } from "../components/ui/StatCard";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";
import { cn, focusRing } from "../lib/cn";
import { greeting, percent, timeAgo } from "../lib/format";
import { reveal } from "../lib/motion";
import type { DashboardData } from "../types/api";

function headline(data: DashboardData): string {
  if (data.completed === 0) return "Capture your first flag to get on the scoreboard.";
  if (data.completed === data.total) return "Every challenge solved. Legendary.";
  if (data.rank === 1) return "You're #1. Defend the top spot.";
  if (data.next_target) {
    const gap = data.next_target.gap;
    return `${gap.toLocaleString("en")} ${gap === 1 ? "pt" : "pts"} to pass ${data.next_target.display_name} for #${data.next_target.rank}.`;
  }
  return "Keep going: every flag moves you up.";
}

export function DashboardPage() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useApi<DashboardData>("/api/dashboard");

  if (loading && !data) {
    return (
      <PageContainer>
        <PageSkeleton />
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
  // Older API servers don't send these yet; degrade gracefully instead of crashing.
  const activity = data.activity ?? [];
  const firstBloods = data.first_bloods ?? 0;
  const name = user?.display_name ?? "hacker";
  const skills = Object.entries(data.skills).sort(
    ([, a], [, b]) => percent(b.solved, b.total) - percent(a.solved, a.total),
  );

  return (
    <PageContainer>
      {/* Hero */}
      <section
        {...reveal(0)}
        className={cn(
          reveal(0).className,
          "relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-900 p-6 sm:p-8",
        )}
      >
        <div aria-hidden="true" className="bg-grid absolute inset-0 [mask-image:linear-gradient(to_bottom,black,transparent)]" />
        <div aria-hidden="true" className="bg-glow absolute inset-0" />
        <div className="relative flex flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-4">
            <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-brand-400">
              <Sparkles aria-hidden="true" className="h-4 w-4" />
              {greeting()}
            </p>
            <h1 className="text-3xl font-semibold tracking-tight text-gray-50 sm:text-4xl">
              Welcome back, <span className="text-gradient">{name}</span>
            </h1>
            <p className="max-w-xl text-base text-gray-300">{headline(data)}</p>
            {data.next_target && data.rank !== 1 && data.completed > 0 && (
              <div className="flex max-w-md flex-col gap-2">
                <div className="flex justify-between text-xs text-gray-400">
                  <span>You · {data.score.toLocaleString("en")} pts</span>
                  <span>
                    #{data.next_target.rank} {data.next_target.display_name}
                  </span>
                </div>
                <ProgressBar
                  value={percent(data.score, data.score + data.next_target.gap)}
                  label="Progress toward the next rank"
                />
              </div>
            )}
            <div className="flex flex-wrap gap-2 pt-2">
              {next ? (
                <Button href={`/challenges/${next.public_slug}`}>
                  <Crosshair aria-hidden="true" className="h-4 w-4" />
                  {data.in_progress ? `Resume ${next.name}` : `Start ${next.name}`}
                </Button>
              ) : (
                <Button href="/challenges">Browse challenges</Button>
              )}
              <Button href="/leaderboard" variant="secondary">
                <Trophy aria-hidden="true" className="h-4 w-4" />
                Scoreboard
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-6 self-start md:self-center">
            <ProgressRing value={data.completion_pct} size={144} label="Challenges completed">
              <span className="flex flex-col items-center">
                <span className="font-mono text-3xl font-semibold text-gray-50">{Math.round(data.completion_pct)}%</span>
                <span className="text-xs text-gray-400">
                  {data.completed}/{data.total} solved
                </span>
              </span>
            </ProgressRing>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section aria-label="Your stats" className="grid grid-cols-2 gap-4 sm:gap-6 lg:grid-cols-4">
        <StatCard {...reveal(1)} label="Total score" value={data.score} tone="brand" icon={Star} sub="points earned" />
        <StatCard
          {...reveal(2)}
          label="Global rank"
          value={data.rank ? `#${data.rank}` : "—"}
          icon={Medal}
          sub={data.rank ? (data.players ? `of ${data.players} ranked players` : "on the scoreboard") : "solve a challenge to rank"}
        />
        <StatCard
          {...reveal(3)}
          label="First bloods"
          value={firstBloods}
          tone="success"
          icon={Droplet}
          sub="first to solve a challenge"
        />
        <StatCard
          {...reveal(4)}
          label="Day streak"
          value={data.streak}
          tone="warning"
          icon={Flame}
          sub={data.streak ? "keep the fire going" : "solve one today to start"}
        />
      </section>

      {/* Activity + next up */}
      <section className="grid gap-6 lg:grid-cols-3">
        <Card {...reveal(5)} className={cn(reveal(5).className, "flex flex-col gap-4 lg:col-span-2")}>
          <div className="flex items-center justify-between gap-4">
            <SectionLabel>Activity · last 16 weeks</SectionLabel>
            <CalendarDays aria-hidden="true" className="h-4 w-4 text-gray-400" />
          </div>
          {activity.length > 0 ? (
            <ActivityHeatmap days={activity} />
          ) : (
            <p className="text-sm text-gray-400">Your solve activity will appear here.</p>
          )}
        </Card>

        <Card {...reveal(6)} className={cn(reveal(6).className, "relative flex flex-col gap-4 overflow-hidden")}>
          <div aria-hidden="true" className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-brand-500/10 blur-2xl" />
          <SectionLabel>{data.in_progress ? "Pick up where you left off" : "Up next"}</SectionLabel>
          {next ? (
            <Link
              to={`/challenges/${next.public_slug}`}
              className={cn("group relative flex flex-1 flex-col gap-4 rounded-xl", focusRing)}
            >
              <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand-500/10 text-brand-400 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-6">
                <Target aria-hidden="true" className="h-6 w-6" />
              </span>
              <span className="text-xl font-semibold text-gray-50">{next.name}</span>
              <span className="flex flex-wrap items-center gap-2">
                <DifficultyBadge difficulty={next.difficulty} />
                {next.category_name && <Badge>{next.category_name}</Badge>}
                <span className="font-mono text-sm text-brand-400">{next.points} pts</span>
              </span>
              <span className="mt-auto flex items-center gap-2 text-sm font-medium text-brand-400">
                {data.in_progress ? "Resume" : "Start challenge"}
                <ArrowRight aria-hidden="true" className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </span>
            </Link>
          ) : (
            <EmptyState icon={Trophy} title="All caught up" description="You have solved every published challenge." />
          )}
        </Card>
      </section>

      {/* Skills + recent */}
      <section className="grid gap-6 lg:grid-cols-2">
        <Card {...reveal(7)} className={cn(reveal(7).className, "flex flex-col gap-6")}>
          <div className="flex items-center justify-between">
            <SectionLabel>Skills</SectionLabel>
            <Link to="/challenges" className={cn("rounded text-xs text-gray-400 transition-colors hover:text-brand-400", focusRing)}>
              Browse →
            </Link>
          </div>
          <ul className="flex flex-col gap-4">
            {skills.map(([skill, stat]) => (
              <li key={skill} className="group flex flex-col gap-2">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="font-medium text-gray-50 transition-colors group-hover:text-brand-300">{skill}</span>
                  <span className="font-mono text-xs text-gray-400">
                    {stat.solved}/{stat.total} · {stat.earned}/{stat.available} pts
                  </span>
                </div>
                <ProgressBar
                  value={percent(stat.solved, stat.total)}
                  tone={stat.solved === stat.total && stat.total > 0 ? "success" : "brand"}
                  label={`${skill} progress`}
                />
              </li>
            ))}
          </ul>
        </Card>

        <Card {...reveal(8)} className={cn(reveal(8).className, "flex flex-col gap-4")}>
          <SectionLabel>Recent activity</SectionLabel>
          {data.recent.length > 0 ? (
            <ol className="relative flex flex-col gap-1 before:absolute before:bottom-4 before:left-4 before:top-4 before:w-px before:bg-gray-800">
              {data.recent.map((entry) => {
                const ok = Boolean(entry.correct);
                return (
                  <li key={`${entry.public_slug}-${entry.created_at}`}>
                    <Link
                      to={`/challenges/${entry.public_slug}`}
                      className={cn(
                        "relative flex items-center gap-4 rounded-lg py-2 pr-2 transition-colors duration-200 hover:bg-gray-800/50",
                        focusRing,
                      )}
                    >
                      <span
                        className={cn(
                          "relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full ring-4 ring-gray-900",
                          ok ? "bg-green-500/15 text-green-400" : "bg-gray-800 text-gray-400",
                        )}
                      >
                        {ok ? <Check aria-hidden="true" className="h-4 w-4" /> : <X aria-hidden="true" className="h-4 w-4" />}
                      </span>
                      <span className="flex min-w-0 flex-1 flex-col">
                        <span className="truncate text-sm font-medium text-gray-50">{entry.name}</span>
                        <span className="text-xs text-gray-400">{ok ? "Flag captured" : "Wrong flag"}</span>
                      </span>
                      <span className="shrink-0 text-xs text-gray-400">{timeAgo(entry.created_at)}</span>
                    </Link>
                  </li>
                );
              })}
            </ol>
          ) : (
            <EmptyState icon={Flag} title="No activity yet" description="Submit your first flag to see it here." />
          )}
        </Card>
      </section>

      {data.achievements.length > 0 && (
        <Card {...reveal(9)} className={cn(reveal(9).className, "flex flex-col gap-4")}>
          <SectionLabel>Recent achievements</SectionLabel>
          <div className="flex flex-wrap gap-4">
            {data.achievements.map((achievement, index) => (
              <div
                key={achievement.slug}
                title={achievement.description}
                className="group flex animate-scale-in items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 py-1 pl-1 pr-4 transition-transform duration-200 hover:-translate-y-1"
                style={{ animationDelay: `${index * 80}ms` }}
              >
                <span className="grid h-6 w-6 place-items-center rounded-full bg-brand-500/20 text-brand-300 transition-transform duration-300 group-hover:rotate-12">
                  <Star aria-hidden="true" className="h-4 w-4 fill-current" />
                </span>
                <span className="text-sm font-medium text-brand-200">{achievement.name}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </PageContainer>
  );
}
