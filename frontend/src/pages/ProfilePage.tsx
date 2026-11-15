import { Flag } from "lucide-react";
import { Link } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Avatar } from "../components/ui/Avatar";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionLabel } from "../components/ui/SectionLabel";
import { Table, Td, Tr } from "../components/ui/Table";
import { useApi } from "../hooks/useApi";
import { percent } from "../lib/format";
import type { ProfileData } from "../types/api";

function Stat({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className={`font-mono text-2xl font-semibold ${accent ? "text-brand-400" : "text-gray-50"}`}>
        {value}
      </span>
      <span className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</span>
    </div>
  );
}

export function ProfilePage() {
  const { data, error, loading, reload } = useApi<ProfileData>("/api/profile");

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
        <ErrorState message={error ?? "Could not load your profile."} onRetry={reload} />
      </PageContainer>
    );
  }

  const { user } = data;
  return (
    <PageContainer>
      <PageHeader title="Profile" />

      <Card className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <Avatar name={user.display_name} size="lg" />
          <div className="flex flex-col gap-2">
            <p className="text-xl font-semibold text-gray-50">{user.display_name}</p>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{user.role}</Badge>
              <Badge tone={user.email_verified ? "success" : "neutral"}>
                {user.email_verified ? "Verified" : "Unverified"}
              </Badge>
              {user.two_factor && <Badge tone="brand">2FA on</Badge>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-8">
          <Stat label="Points" value={data.score} accent />
          <Stat label="Rank" value={data.rank ? `#${data.rank}` : "—"} />
          <Stat label="Solves" value={data.solves.length} />
        </div>
      </Card>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <SectionLabel>Solved challenges</SectionLabel>
          {data.solves.length > 0 ? (
            <Table>
              <tbody>
                {data.solves.map((solve) => (
                  <Tr key={solve.slug}>
                    <Td>
                      <Link to={`/challenges/${solve.public_slug}`} className="text-brand-400 hover:underline">
                        {solve.name}
                      </Link>
                    </Td>
                    <Td>
                      <DifficultyBadge difficulty={solve.difficulty} />
                    </Td>
                    <Td className="text-right font-mono text-brand-400">+{solve.points_awarded}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState
              icon={Flag}
              title="No solves yet"
              description="Your captured flags will appear here."
            />
          )}
        </Card>

        <Card className="flex flex-col gap-6">
          <div className="flex flex-col gap-4">
            <SectionLabel>Category breakdown</SectionLabel>
            {Object.entries(data.skills).map(([skill, stat]) => (
              <div key={skill} className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-50">{skill}</span>
                  <span className="text-gray-400">
                    {stat.solved}/{stat.total}
                  </span>
                </div>
                <ProgressBar value={percent(stat.solved, stat.total)} label={`${skill} solved`} />
              </div>
            ))}
          </div>
          <div className="flex flex-col gap-4">
            <SectionLabel>Badges</SectionLabel>
            {data.achievements.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {data.achievements.map((achievement) => (
                  <span key={achievement.slug} title={achievement.description}>
                    <Badge tone="brand">★ {achievement.name}</Badge>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">None yet.</p>
            )}
          </div>
        </Card>
      </section>
    </PageContainer>
  );
}
