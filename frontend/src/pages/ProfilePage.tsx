import { Droplet, Flag, Medal, ShieldCheck, Star, Trophy } from "lucide-react";
import { Link } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { AnimatedNumber } from "../components/ui/AnimatedNumber";
import { AvatarUploader } from "../components/ui/AvatarUploader";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/PageLoader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionLabel } from "../components/ui/SectionLabel";
import { PageSkeleton } from "../components/ui/Skeleton";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";
import { cn, focusRing } from "../lib/cn";
import { percent, timeAgo } from "../lib/format";
import { reveal } from "../lib/motion";
import type { ProfileData } from "../types/api";

function Stat({ label, value, icon: Icon, accent = false }: { label: string; value: number | string; icon: typeof Star; accent?: boolean }) {
  return (
    <div className="group flex flex-col items-center gap-1 rounded-xl px-4 py-2 transition-colors duration-200 hover:bg-gray-800/50">
      <Icon aria-hidden="true" className={cn("h-4 w-4 transition-transform duration-300 group-hover:scale-125", accent ? "text-brand-400" : "text-gray-400")} />
      <span className={cn("font-mono text-2xl font-semibold", accent ? "text-brand-400" : "text-gray-50")}>
        {typeof value === "number" ? <AnimatedNumber value={value} /> : value}
      </span>
      <span className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</span>
    </div>
  );
}

export function ProfilePage() {
  const { data, error, loading, reload } = useApi<ProfileData>("/api/profile");
  const { refresh } = useAuth();

  if (loading && !data) {
    return (
      <PageContainer>
        <PageSkeleton tiles={3} />
      </PageContainer>
    );
  }
  if (!data) {
    return (
      <PageContainer>
        <ErrorState message={error ?? "Could not load your profile."} onRetry={reload} />
      </PageContainer>
    );
  }

  const { user } = data;
  const skills = Object.entries(data.skills);
  const points = data.solves.reduce((sum, s) => sum + s.points_awarded, 0);

  return (
    <PageContainer>
      <section {...reveal(0)} className={cn(reveal(0).className, "relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-900")}>
        <div aria-hidden="true" className="h-28 bg-gradient-to-r from-brand-700/40 via-orange-600/20 to-gray-900" />
        <div aria-hidden="true" className="bg-grid absolute inset-x-0 top-0 h-28 opacity-60" />
        <div className="relative flex flex-col gap-6 px-6 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="-mt-10 flex items-start gap-4">
            <AvatarUploader
              name={user.display_name}
              src={user.avatar_url}
              onChange={async () => {
                await refresh(); // top-bar avatar
                reload();
              }}
            />
            <div className="flex flex-col gap-2 pt-12">
              <h1 className="text-2xl font-semibold tracking-tight text-gray-50">{user.display_name}</h1>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{user.role}</Badge>
                <Badge tone={user.email_verified ? "success" : "neutral"}>{user.email_verified ? "Verified" : "Unverified"}</Badge>
                {user.two_factor && (
                  <Badge tone="brand">
                    <ShieldCheck aria-hidden="true" className="mr-1 h-3 w-3" />
                    2FA on
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Stat label="Points" value={data.score} icon={Star} accent />
            <Stat label="Rank" value={data.rank ? `#${data.rank}` : "—"} icon={Medal} />
            <Stat label="Solves" value={data.solves.length} icon={Flag} />
            <Stat label="Badges" value={data.achievements.length} icon={Trophy} />
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-5">
        <Card {...reveal(1)} className={cn(reveal(1).className, "flex flex-col gap-4 lg:col-span-3")}>
          <div className="flex items-center justify-between">
            <SectionLabel>Captured flags</SectionLabel>
            {points > 0 && <span className="font-mono text-xs text-gray-400">{points} pts from solves</span>}
          </div>
          {data.solves.length > 0 ? (
            <ul className="flex flex-col">
              {data.solves.map((solve, index) => (
                <li key={solve.slug} className="animate-fade-up" style={{ animationDelay: `${Math.min(index, 10) * 40}ms` }}>
                  <Link
                    to={`/challenges/${solve.public_slug}`}
                    className={cn("group flex items-center gap-4 rounded-lg px-2 py-2 transition-colors duration-200 hover:bg-gray-800/50", focusRing)}
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-green-500/10 text-green-400 transition-transform duration-200 group-hover:scale-110">
                      <Flag aria-hidden="true" className="h-4 w-4" />
                    </span>
                    <span className="flex min-w-0 flex-1 flex-col">
                      <span className="truncate text-sm font-medium text-gray-50 group-hover:text-brand-300">{solve.name}</span>
                      <span className="text-xs text-gray-400">
                        {solve.skill ?? "General"} · {timeAgo(solve.created_at)}
                      </span>
                    </span>
                    <DifficultyBadge difficulty={solve.difficulty} />
                    <span className="w-16 text-right font-mono text-sm font-semibold text-brand-400">+{solve.points_awarded}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState icon={Flag} title="No flags yet" description="Every flag you capture is recorded here." />
          )}
        </Card>

        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card {...reveal(2)} className={cn(reveal(2).className, "flex flex-col gap-4")}>
            <SectionLabel>Category breakdown</SectionLabel>
            {skills.map(([skill, stat]) => (
              <div key={skill} className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-50">{skill}</span>
                  <span className="font-mono text-xs text-gray-400">
                    {stat.solved}/{stat.total}
                  </span>
                </div>
                <ProgressBar
                  value={percent(stat.solved, stat.total)}
                  tone={stat.total > 0 && stat.solved === stat.total ? "success" : "brand"}
                  label={`${skill} solved`}
                />
              </div>
            ))}
          </Card>

          <Card {...reveal(3)} className={cn(reveal(3).className, "flex flex-col gap-4")}>
            <SectionLabel>Badges</SectionLabel>
            {data.achievements.length > 0 ? (
              <div className="grid grid-cols-2 gap-2">
                {data.achievements.map((achievement) => (
                  <div
                    key={achievement.slug}
                    title={achievement.description}
                    className="group flex items-center gap-2 rounded-lg border border-brand-500/20 bg-brand-500/5 p-2 transition-all duration-200 hover:-translate-y-1 hover:border-brand-500/40"
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-500/15 text-brand-300 transition-transform duration-300 group-hover:rotate-12">
                      {achievement.slug === "first_blood" ? <Droplet aria-hidden="true" className="h-4 w-4" /> : <Star aria-hidden="true" className="h-4 w-4 fill-current" />}
                    </span>
                    <span className="truncate text-xs font-medium text-gray-200">{achievement.name}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">None yet. Your first solve earns one.</p>
            )}
          </Card>
        </div>
      </section>
    </PageContainer>
  );
}
