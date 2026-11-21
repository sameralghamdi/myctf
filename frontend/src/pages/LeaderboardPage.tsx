import { Crown, Droplet, Flag, Radio, Search, Trophy, UserRound } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ScoreRace } from "../components/charts/ScoreRace";
import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { AnimatedNumber } from "../components/ui/AnimatedNumber";
import { Avatar } from "../components/ui/Avatar";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { SearchInput } from "../components/ui/Field";
import { ErrorState } from "../components/ui/PageLoader";
import { SectionLabel } from "../components/ui/SectionLabel";
import { PageSkeleton } from "../components/ui/Skeleton";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";
import { useInterval } from "../hooks/useInterval";
import { cn, focusRing } from "../lib/cn";
import { timeAgo } from "../lib/format";
import { reveal } from "../lib/motion";
import type { LeaderboardInsights, LeaderboardRow } from "../types/api";

const REFRESH_MS = 30000;

const MEDALS = {
  1: { ring: "ring-yellow-400/70", text: "text-yellow-300", bar: "from-yellow-500/30 to-yellow-500/5 border-yellow-500/40", height: "h-40", label: "1st" },
  2: { ring: "ring-gray-300/60", text: "text-gray-200", bar: "from-gray-300/20 to-gray-300/5 border-gray-400/30", height: "h-28", label: "2nd" },
  3: { ring: "ring-orange-400/60", text: "text-orange-300", bar: "from-orange-500/25 to-orange-500/5 border-orange-500/30", height: "h-20", label: "3rd" },
} as const;

function Podium({ rows, me }: { rows: LeaderboardRow[]; me?: string }) {
  // Visual order: 2nd, 1st, 3rd.
  const order = [rows[1], rows[0], rows[2]].filter(Boolean) as LeaderboardRow[];
  return (
    <div className="grid grid-cols-3 items-end gap-4 sm:gap-6">
      {order.map((row, index) => {
        const medal = MEDALS[row.rank as 1 | 2 | 3];
        return (
          <div key={row.username} className="flex flex-col items-center gap-2">
            <div className="relative flex animate-fade-up flex-col items-center gap-2 text-center" style={{ animationDelay: `${300 + index * 120}ms` }}>
              {row.rank === 1 && (
                <Crown aria-hidden="true" className="h-6 w-6 animate-float fill-yellow-400/30 text-yellow-300" />
              )}
              <Avatar
                name={row.display_name}
                size={row.rank === 1 ? "xl" : "lg"}
                className={cn("ring-4 ring-offset-4 ring-offset-gray-900", medal.ring)}
              />
              <span className="max-w-full truncate text-sm font-semibold text-gray-50">
                {row.display_name}
                {row.username === me && <span className="pl-1 text-xs font-normal text-gray-400">(you)</span>}
              </span>
              <span className="font-mono text-lg font-semibold text-gray-50">
                <AnimatedNumber value={row.score} />
                <span className="pl-1 text-xs font-normal text-gray-400">pts</span>
              </span>
            </div>
            <div
              className={cn(
                "flex w-full origin-bottom animate-rise flex-col items-center justify-start rounded-t-xl border border-b-0 bg-gradient-to-b pt-2",
                medal.bar,
                medal.height,
              )}
              style={{ animationDelay: `${index * 120}ms` }}
            >
              <span className={cn("font-mono text-2xl font-bold", medal.text)}>{row.rank}</span>
              <span className="text-xs text-gray-400">{row.solves} solves</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RankCell({ rank }: { rank: number }) {
  if (rank <= 3) {
    const medal = MEDALS[rank as 1 | 2 | 3];
    return (
      <span className={cn("inline-flex h-8 w-8 items-center justify-center rounded-full bg-gray-800 font-mono text-sm font-bold ring-1", medal.ring, medal.text)}>
        {rank}
      </span>
    );
  }
  return <span className="inline-flex h-8 w-8 items-center justify-center font-mono text-sm text-gray-400">{rank}</span>;
}

export function LeaderboardPage() {
  const { user, refresh } = useAuth();
  const board = useApi<LeaderboardRow[]>("/api/leaderboard");
  const insights = useApi<LeaderboardInsights>("/api/leaderboard/insights");
  const [query, setQuery] = useState("");
  const [updatedAt, setUpdatedAt] = useState(Date.now());
  const [now, setNow] = useState(Date.now());
  const [flashed, setFlashed] = useState<Set<string>>(new Set());
  // Rows fade in on the first paint only, not on every live refresh.
  const [entering, setEntering] = useState(true);
  useEffect(() => {
    const id = window.setTimeout(() => setEntering(false), 1500);
    return () => window.clearTimeout(id);
  }, []);
  const previous = useRef<Map<string, number> | null>(null);
  const meRow = useRef<HTMLTableRowElement>(null);

  // Live: refetch every 30s while the tab is visible, and tick relative times.
  useInterval(() => {
    board.reload();
    insights.reload();
    void refresh();
  }, REFRESH_MS);
  useInterval(() => setNow(Date.now()), 10000);

  // Rows whose score changed since the last fetch glow once.
  useEffect(() => {
    if (!board.data) return;
    const current = new Map(board.data.map((row) => [row.username, row.score]));
    if (previous.current) {
      const changed = new Set(
        board.data.filter((row) => previous.current?.get(row.username) !== row.score).map((row) => row.username),
      );
      setFlashed(changed);
    }
    previous.current = current;
    setUpdatedAt(Date.now());
  }, [board.data]);

  const rows = board.data ?? [];
  const mine = rows.find((row) => row.username === user?.username);
  const above = mine ? rows.find((row) => row.rank === mine.rank - 1) : rows[rows.length - 1];
  const leader = rows[0]?.score ?? 0;
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? rows.filter((row) => `${row.display_name} ${row.username}`.toLowerCase().includes(q)) : rows;
  }, [rows, query]);

  const liveLabel = (
    <span className="flex items-center gap-2 text-xs text-gray-400">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-green-400" />
      </span>
      Live · updated {timeAgo(new Date(updatedAt).toISOString(), now)}
    </span>
  );

  if (board.loading && !board.data) {
    return (
      <PageContainer>
        <PageSkeleton tiles={3} />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="Scoreboard"
        description="Every flag counts. Climb the ranks, chase first bloods, and watch the race unfold live."
        actions={liveLabel}
      />

      {!board.data ? (
        <ErrorState message={board.error ?? "Could not load the scoreboard."} onRetry={board.reload} />
      ) : rows.length === 0 ? (
        <Card>
          <EmptyState
            icon={Trophy}
            title="No solves recorded yet"
            description="The podium is empty. Capture the first flag and claim it."
            action={<Button href="/challenges">Find a challenge</Button>}
          />
        </Card>
      ) : (
        <>
          <section className="grid gap-6 lg:grid-cols-5">
            <Card className="relative overflow-hidden lg:col-span-3">
              <div aria-hidden="true" className="bg-glow absolute inset-0" />
              <div className="relative flex flex-col gap-6">
                <div className="flex items-center justify-between">
                  <SectionLabel>Podium</SectionLabel>
                  <span className="text-xs text-gray-400">{insights.data?.players ?? rows.length} ranked players</span>
                </div>
                <Podium rows={rows.slice(0, 3)} me={user?.username} />
              </div>
            </Card>

            <Card {...reveal(2)} className={cn(reveal(2).className, "flex flex-col gap-4 lg:col-span-2")}>
              <SectionLabel>Your position</SectionLabel>
              {mine ? (
                <div className="flex flex-1 flex-col gap-4">
                  <div className="flex items-center gap-4">
                    <Avatar name={mine.display_name} size="lg" />
                    <div className="flex flex-col">
                      <span className="font-mono text-4xl font-bold text-gray-50">#{mine.rank}</span>
                      <span className="text-sm text-gray-400">
                        <AnimatedNumber value={mine.score} className="font-mono text-brand-400" /> pts · {mine.solves} solves
                      </span>
                    </div>
                  </div>
                  <dl className="grid grid-cols-3 gap-2 text-center">
                    {[
                      ["Solves", String(mine.solves)],
                      ["First bloods", String(mine.first_bloods)],
                      ["Last solve", timeAgo(mine.last_solve, now)],
                    ].map(([label, value]) => (
                      <div key={label} className="rounded-lg bg-gray-950/60 px-2 py-2">
                        <dt className="text-xs text-gray-400">{label}</dt>
                        <dd className="font-mono text-sm font-semibold text-gray-50">{value}</dd>
                      </div>
                    ))}
                  </dl>
                  {above && mine.rank > 1 ? (
                    <div className="flex flex-col gap-2 rounded-lg border border-gray-800 bg-gray-950/60 p-4">
                      <p className="text-sm text-gray-300">
                        <span className="font-mono font-semibold text-brand-400">{above.score - mine.score + 1}</span>{" "}
                        {above.score - mine.score + 1 === 1 ? "pt" : "pts"} to pass{" "}
                        <span className="font-medium text-gray-50">{above.display_name}</span> for #{above.rank}
                      </p>
                      <div className="h-2 overflow-hidden rounded-full bg-gray-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-600 to-orange-400 transition-[width] duration-1000"
                          style={{ width: `${Math.min(100, (mine.score / Math.max(1, above.score + 1)) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-200">
                      You're on top. Everyone is chasing you.
                    </p>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-auto self-start"
                    onClick={() => {
                      setQuery("");
                      requestAnimationFrame(() => meRow.current?.scrollIntoView({ behavior: "smooth", block: "center" }));
                    }}
                  >
                    <UserRound aria-hidden="true" className="h-4 w-4" />
                    Jump to my row
                  </Button>
                </div>
              ) : (
                <EmptyState
                  icon={Flag}
                  title="You're not on the board yet"
                  description={above ? `One solve puts you in the race. ${above.display_name} holds the last spot with ${above.score} pts.` : "One solve puts you in the race."}
                  action={<Button href="/challenges" size="sm">Capture a flag</Button>}
                />
              )}
            </Card>
          </section>

          {insights.data && insights.data.race.length > 0 && (
            <Card {...reveal(3)} className={cn(reveal(3).className, "flex flex-col gap-4")}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <SectionLabel>Score race · top players</SectionLabel>
                <span className="text-xs text-gray-400">Hover the chart to compare scores at any moment</span>
              </div>
              <ScoreRace series={insights.data.race} />
            </Card>
          )}

          <section className="grid gap-6 lg:grid-cols-3">
            <Card flush {...reveal(4)} className={cn(reveal(4).className, "flex flex-col gap-4 lg:col-span-2")}>
              <div className="flex flex-wrap items-center justify-between gap-4 px-6 pt-6">
                <SectionLabel>Rankings</SectionLabel>
                <div className="relative w-full sm:w-64">
                  <Search aria-hidden="true" className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <SearchInput
                    aria-label="Search players"
                    placeholder="Search players…"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    className="h-8 pl-10"
                  />
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-xs font-medium uppercase tracking-wider text-gray-400">
                      <th className="h-10 border-b border-gray-800 pl-6 pr-2 font-medium">#</th>
                      <th className="h-10 border-b border-gray-800 px-4 font-medium">Player</th>
                      <th className="hidden h-10 border-b border-gray-800 px-4 text-right font-medium sm:table-cell">Solves</th>
                      <th className="hidden h-10 border-b border-gray-800 px-4 text-right font-medium md:table-cell" title="First bloods">
                        <Droplet aria-label="First bloods" className="ml-auto h-4 w-4" />
                      </th>
                      <th className="hidden h-10 border-b border-gray-800 px-4 text-right font-medium md:table-cell">Last solve</th>
                      <th className="h-10 border-b border-gray-800 pl-4 pr-6 text-right font-medium">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((row, index) => {
                      const isMe = row.username === user?.username;
                      return (
                        <tr
                          key={row.username}
                          ref={isMe ? meRow : undefined}
                          className={cn(
                            "group transition-colors duration-200",
                            entering && "animate-fade-up",
                            isMe ? "bg-brand-500/10" : "hover:bg-gray-800/50",
                            flashed.has(row.username) && "animate-flash",
                          )}
                          style={{ animationDelay: `${Math.min(index, 15) * 30}ms` }}
                        >
                          <td className="h-14 border-b border-gray-800 pl-6 pr-2">
                            <RankCell rank={row.rank} />
                          </td>
                          <td className="h-14 border-b border-gray-800 px-4">
                            <span className="flex items-center gap-4">
                              <Avatar name={row.display_name} size="md" className="transition-transform duration-200 group-hover:scale-110" />
                              <span className="flex flex-col">
                                <span className="font-medium text-gray-50">
                                  {row.display_name}
                                  {isMe && <span className="ml-2 rounded-full bg-brand-500/20 px-2 text-xs text-brand-300">you</span>}
                                </span>
                                <span className="h-1 w-24 overflow-hidden rounded-full bg-gray-800 sm:w-32" aria-hidden="true">
                                  <span
                                    className="block h-full rounded-full bg-gradient-to-r from-brand-600 to-orange-400"
                                    style={{ width: `${leader ? (row.score / leader) * 100 : 0}%` }}
                                  />
                                </span>
                              </span>
                            </span>
                          </td>
                          <td className="hidden h-14 border-b border-gray-800 px-4 text-right font-mono text-gray-300 sm:table-cell">{row.solves}</td>
                          <td className="hidden h-14 border-b border-gray-800 px-4 text-right font-mono md:table-cell">
                            {row.first_bloods > 0 ? <span className="text-red-300">{row.first_bloods}</span> : <span className="text-gray-600">0</span>}
                          </td>
                          <td className="hidden h-14 border-b border-gray-800 px-4 text-right text-xs text-gray-400 md:table-cell">
                            {timeAgo(row.last_solve, now)}
                          </td>
                          <td className="h-14 border-b border-gray-800 pl-4 pr-6 text-right font-mono text-base font-semibold text-brand-400">
                            {row.score.toLocaleString("en")}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {visible.length === 0 && <p className="px-6 py-8 text-center text-sm text-gray-400">No players match “{query}”.</p>}
              </div>
            </Card>

            <Card {...reveal(5)} className={cn(reveal(5).className, "flex flex-col gap-4")}>
              <div className="flex items-center justify-between">
                <SectionLabel>Live feed</SectionLabel>
                <Radio aria-hidden="true" className="h-4 w-4 text-green-400" />
              </div>
              {insights.data && insights.data.feed.length > 0 ? (
                <ol className="flex flex-col gap-2" aria-live="polite">
                  {insights.data.feed.map((item, index) => (
                    <li
                      key={`${item.username}-${item.public_slug}-${item.at}`}
                      className="animate-fade-up"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <Link
                        to={`/challenges/${item.public_slug}`}
                        className={cn("flex items-start gap-4 rounded-lg p-2 transition-colors duration-200 hover:bg-gray-800/50", focusRing)}
                      >
                        <Avatar name={item.display_name} size="sm" className="mt-1" />
                        <span className="flex min-w-0 flex-1 flex-col">
                          <span className="text-sm text-gray-300">
                            <span className="font-medium text-gray-50">{item.display_name}</span> solved{" "}
                            <span className="font-medium text-gray-50">{item.challenge}</span>
                          </span>
                          <span className="flex items-center gap-2 text-xs text-gray-400">
                            <span className="font-mono text-brand-400">+{item.points}</span>
                            {item.first_blood && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 text-red-300 ring-1 ring-inset ring-red-500/30">
                                <Droplet aria-hidden="true" className="h-3 w-3" /> first blood
                              </span>
                            )}
                            · {timeAgo(item.at, now)}
                          </span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-gray-400">Solves will stream in here as they happen.</p>
              )}
            </Card>
          </section>
        </>
      )}
    </PageContainer>
  );
}
