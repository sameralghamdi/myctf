import { Trophy } from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { Table, Td, Th, Tr } from "../components/ui/Table";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";
import type { LeaderboardRow } from "../types/api";

export function LeaderboardPage() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useApi<LeaderboardRow[]>("/api/leaderboard");

  return (
    <PageContainer>
      <PageHeader title="Scoreboard" description="The top 100 players by score." />
      {loading && !data ? (
        <PageLoader />
      ) : !data ? (
        <ErrorState message={error ?? "Could not load the scoreboard."} onRetry={reload} />
      ) : data.length === 0 ? (
        <Card>
          <EmptyState
            icon={Trophy}
            title="No solves recorded yet"
            description="Be the first to capture a flag."
          />
        </Card>
      ) : (
        <Card className="overflow-hidden p-0">
          <Table>
            <thead>
              <tr>
                <Th className="w-16">#</Th>
                <Th>Player</Th>
                <Th className="text-right">Solves</Th>
                <Th className="text-right">Score</Th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => {
                const isMe = row.username === user?.username;
                return (
                  <Tr key={row.username} highlight={isMe}>
                    <Td className="font-mono text-gray-400">{row.rank}</Td>
                    <Td className="font-medium text-gray-50">
                      {row.display_name}
                      {isMe && <span className="pl-2 text-xs text-gray-400">(you)</span>}
                    </Td>
                    <Td className="text-right">{row.solves}</Td>
                    <Td className="text-right font-mono text-brand-400">{row.score}</Td>
                  </Tr>
                );
              })}
            </tbody>
          </Table>
        </Card>
      )}
    </PageContainer>
  );
}
