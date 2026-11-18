import { ExternalLink, Play, RotateCcw, Square } from "lucide-react";
import {
  useCallback,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { Navigate, useParams } from "react-router-dom";
import { Alert, type AlertTone } from "../components/ui/Alert";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DifficultyBadge } from "../components/ui/ChallengeBadges";
import { SearchInput } from "../components/ui/Field";
import { LabTerminal } from "../components/terminal/LabTerminal";
import { Markdown } from "../components/ui/Markdown";
import { ErrorState, PageLoader } from "../components/ui/PageLoader";
import { SectionLabel } from "../components/ui/SectionLabel";
import { useAuth } from "../context/AuthContext";
import { useBreadcrumbs } from "../context/BreadcrumbContext";
import { useApi } from "../hooks/useApi";
import { api, ApiError, toMessage } from "../lib/api";
import { cn } from "../lib/cn";
import { formatDateTime, isSafeUrl } from "../lib/format";
import type { ChallengeDetail, Hint, SubmitResult } from "../types/api";

type View = "brief" | "split" | "lab";

const MIN_BRIEF = 320;
const MAX_BRIEF = 720;

/** Route entry: remounts the screen when the slug changes so no state leaks across challenges. */
export function ChallengePlayPage() {
  const { slug = "" } = useParams();
  return <PlayScreen key={slug} slug={slug} />;
}

function PlayScreen({ slug }: { slug: string }) {
  const { refresh } = useAuth();
  const path = `/api/challenges/${encodeURIComponent(slug)}`;
  const { data: challenge, error, loading, reload } = useApi<ChallengeDetail>(path);

  useBreadcrumbs(
    challenge
      ? [
          { label: "MyCTF", href: "/dashboard" },
          { label: "Challenges", href: "/challenges" },
          { label: challenge.name },
        ]
      : null,
  );

  const [view, setView] = useState<View>("split");
  const [labView, setLabView] = useState<"target" | "terminal" | null>(null);
  const [briefWidth, setBriefWidth] = useState(480);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const [flag, setFlag] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ tone: AlertTone; text: string } | null>(null);
  const [labBusy, setLabBusy] = useState(false);
  const [labError, setLabError] = useState<string | null>(null);

  const runLabAction = useCallback(
    async (action: string) => {
      setLabBusy(true);
      setLabError(null);
      try {
        await api(action, { method: "POST" });
        reload();
      } catch (caught) {
        setLabError(toMessage(caught));
      } finally {
        setLabBusy(false);
      }
    },
    [reload],
  );

  if (loading && !challenge) return <PageLoader />;
  if (!challenge) {
    return (
      <div className="p-6">
        <ErrorState message={error ?? "Challenge not found."} onRetry={reload} />
      </div>
    );
  }

  if (slug !== challenge.public_slug) return <Navigate to={`/challenges/${challenge.public_slug}`} replace />;

  const lab = challenge.lab ?? null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!flag.trim()) return;
    setSubmitting(true);
    setResult(null);
    try {
      const response = await api<SubmitResult>(`${path}/submit`, {
        method: "POST",
        body: { flag: flag.trim() },
      });
      setResult({ tone: "success", text: response.message });
      setFlag("");
      if (!response.already_solved) await refresh(); // score + rank in the top bar
      reload();
    } catch (caught) {
      const tone: AlertTone = caught instanceof ApiError && caught.status === 429 ? "warning" : "danger";
      setResult({ tone, text: toMessage(caught) });
    } finally {
      setSubmitting(false);
    }
  }

  async function unlockHint(hint: Hint) {
    try {
      await api(`${path}/hints/${hint.level}`, { method: "POST" });
      await refresh(); // hints can cost points
      reload();
    } catch (caught) {
      setResult({ tone: "danger", text: toMessage(caught) });
    }
  }

  function onDividerDown(event: ReactPointerEvent<HTMLDivElement>) {
    dragging.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function onDividerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const container = containerRef.current;
    if (!dragging.current || !container) return;
    const rect = container.getBoundingClientRect();
    const max = Math.min(MAX_BRIEF, rect.width - MIN_BRIEF);
    setBriefWidth(Math.max(MIN_BRIEF, Math.min(max, event.clientX - rect.left)));
  }
  function onDividerUp(event: ReactPointerEvent<HTMLDivElement>) {
    dragging.current = false;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }

  const showBrief = view !== "lab";
  const showLab = view !== "brief";

  return (
    <div className="flex flex-1 flex-col lg:h-app">
      {/* Title + view toggle */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-800 px-6 py-2">
        <h1 className="text-lg font-semibold text-gray-50">{challenge.name}</h1>
        <div role="group" aria-label="Layout" className="flex rounded-lg border border-gray-800 p-0">
          {(["brief", "split", "lab"] as const).map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={view === option}
              onClick={() => setView(option)}
              className={cn(
                "h-8 px-4 text-sm font-medium capitalize transition-colors duration-200 first:rounded-l-lg last:rounded-r-lg",
                view === option ? "bg-gray-800 text-gray-50" : "text-gray-400 hover:text-gray-50",
              )}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div
        ref={containerRef}
        style={{ "--play-left": `${briefWidth}px` } as CSSProperties}
        className="flex min-h-0 flex-1 flex-col lg:flex-row"
      >
        {showBrief && (
          <section
            aria-label="Challenge brief"
            className={cn(
              "flex flex-col overflow-y-auto",
              view === "split" ? "lg:w-play lg:shrink-0" : "flex-1",
            )}
          >
            <div className="flex flex-col gap-6 p-6">
              <div className="flex flex-wrap items-center gap-2">
                <DifficultyBadge difficulty={challenge.difficulty} />
                {challenge.category_name && <Badge>{challenge.category_name}</Badge>}
                <span className="font-mono text-sm text-brand-400">{challenge.points} pts</span>
                {challenge.solved && <Badge tone="success">✓ Solved</Badge>}
              </div>

              <Markdown source={challenge.description} />

              {challenge.target_url && isSafeUrl(challenge.target_url) && (
                <div>
                  <Button
                    href={challenge.target_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="secondary"
                  >
                    <ExternalLink aria-hidden="true" className="h-4 w-4" />
                    Open target
                  </Button>
                </div>
              )}

              {challenge.hints.length > 0 && (
                <div className="flex flex-col gap-4">
                  <SectionLabel>Hints</SectionLabel>
                  {challenge.hints.map((hint) => (
                    <Card key={hint.id} className="flex flex-col gap-2 p-4">
                      <div className="flex items-center justify-between gap-4">
                        <span className="flex items-center gap-2 text-sm font-medium text-gray-50">
                          Hint {hint.level}
                          {hint.cost > 0 ? (
                            <Badge tone="warning">−{hint.cost} pts</Badge>
                          ) : (
                            <span className="text-xs font-normal text-gray-400">free</span>
                          )}
                        </span>
                        {!hint.unlocked && (
                          <Button variant="secondary" size="sm" onClick={() => void unlockHint(hint)}>
                            Reveal
                          </Button>
                        )}
                      </div>
                      {hint.unlocked && <p className="text-sm text-gray-300">{hint.body}</p>}
                    </Card>
                  ))}
                </div>
              )}

              {challenge.solved && (challenge.walkthrough || challenge.remediation) && (
                <Card className="flex flex-col gap-2 border-green-500/30 p-4">
                  <h2 className="text-sm font-semibold text-green-400">✓ Debrief</h2>
                  {challenge.walkthrough && (
                    <p className="text-sm text-gray-300">
                      <span className="font-medium text-gray-50">How it works: </span>
                      {challenge.walkthrough}
                    </p>
                  )}
                  {challenge.remediation && (
                    <p className="text-sm text-gray-300">
                      <span className="font-medium text-gray-50">Remediation: </span>
                      {challenge.remediation}
                    </p>
                  )}
                </Card>
              )}
            </div>

            {/* Sticky flag submission */}
            <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-gray-800 bg-gray-900 p-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <SearchInput
                  aria-label="Flag"
                  placeholder="MYCTF{...}"
                  autoComplete="off"
                  spellCheck={false}
                  disabled={challenge.solved}
                  value={flag}
                  onChange={(event) => setFlag(event.target.value)}
                  className="font-mono"
                />
                <Button type="submit" disabled={challenge.solved || submitting}>
                  {challenge.solved ? "Solved ✓" : submitting ? "Checking…" : "Submit"}
                </Button>
              </form>
              {result && <Alert tone={result.tone}>{result.text}</Alert>}
              <p className="text-xs text-gray-400">Attempts: {challenge.attempts}</p>
            </div>
          </section>
        )}

        {view === "split" && (
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize panels"
            onPointerDown={onDividerDown}
            onPointerMove={onDividerMove}
            onPointerUp={onDividerUp}
            className="hidden w-2 shrink-0 cursor-col-resize touch-none bg-gray-800 transition-colors duration-200 hover:bg-brand-500/50 lg:block"
          />
        )}

        {showLab && (
          <section
            aria-label="Lab"
            className="flex min-h-96 min-w-0 flex-1 flex-col border-t border-gray-800 lg:border-t-0"
          >
            {lab ? (
              <>
                <div className="flex flex-wrap items-center gap-4 border-b border-gray-800 bg-gray-900 px-4 py-2 text-sm">
                  <span className="flex items-center gap-2 text-green-400">
                    <span aria-hidden="true" className="h-2 w-2 rounded-full bg-green-400" />
                    Running
                  </span>
                  <span className="font-mono text-gray-300">{lab.instance_id.slice(0, 8)}</span>
                  <span className="text-gray-400">Expires {formatDateTime(lab.expires_at)} (SA time)</span>
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="text-gray-400">URL</span>
                    <code className="select-all truncate rounded bg-gray-950 px-2 py-0.5 font-mono text-xs text-gray-200">
                      {window.location.origin}{lab.url}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void navigator.clipboard?.writeText(`${window.location.origin}${lab.url}`)}
                    >
                      Copy
                    </Button>
                  </span>
                  <span className="ml-auto flex items-center gap-2">
                    <Button href={challenge.has_web_ui && (labView ?? challenge.default_lab_view) === "terminal" ? `${lab.url}terminal` : lab.url} external target="_blank" rel="noopener noreferrer" variant="ghost" size="sm">
                      Open in tab ↗
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={labBusy}
                      onClick={() => void runLabAction(`/api/labs/${lab.instance_id}/reset`)}
                    >
                      <RotateCcw aria-hidden="true" className="h-4 w-4" />
                      Restart
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      disabled={labBusy}
                      onClick={() => void runLabAction(`/api/labs/${lab.instance_id}/stop`)}
                    >
                      <Square aria-hidden="true" className="h-4 w-4" />
                      Stop
                    </Button>
                  </span>
                </div>
                {labError && (
                  <div className="p-4">
                    <Alert tone="danger">{labError}</Alert>
                  </div>
                )}
                {challenge.has_web_ui && (
                  <div className="flex gap-2 border-b border-gray-800 bg-gray-950 px-4 py-2" role="group" aria-label="Lab interface">
                    <Button size="sm" variant={(labView ?? challenge.default_lab_view) === "target" ? "primary" : "ghost"} aria-pressed={(labView ?? challenge.default_lab_view) === "target"} onClick={() => setLabView("target")}>
                      Target page
                    </Button>
                    <Button size="sm" variant={(labView ?? challenge.default_lab_view) === "terminal" ? "primary" : "ghost"} aria-pressed={(labView ?? challenge.default_lab_view) === "terminal"} onClick={() => setLabView("terminal")}>
                      Terminal
                    </Button>
                  </div>
                )}
                {challenge.is_shell && (!challenge.has_web_ui || (labView ?? challenge.default_lab_view) === "terminal") ? (
                  <div className="flex min-h-0 flex-1 flex-col p-4">
                    <LabTerminal key={lab.instance_id} labUrl={lab.url} />
                  </div>
                ) : (
                  <iframe
                    key={lab.instance_id}
                    src={lab.url}
                    title="Lab target"
                    className="min-h-96 w-full flex-1 border-0 bg-white"
                  />
                )}
              </>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
                {challenge.has_lab ? (
                  <>
                    <p className="font-mono text-sm text-gray-400">
                      {challenge.has_web_ui
                        ? "Start the lab to open your target page and terminal"
                        : challenge.is_shell
                        ? "Start the lab to open your private terminal"
                        : "Start the lab to launch your isolated target"}
                    </p>
                    {labError && <Alert tone="danger">{labError}</Alert>}
                    <Button disabled={labBusy} onClick={() => void runLabAction(`${path}/lab/start`)}>
                      <Play aria-hidden="true" className="h-4 w-4" />
                      {labBusy ? "Starting…" : "Start lab"}
                    </Button>
                  </>
                ) : (
                  <p className="text-sm text-gray-400">This challenge is solved without a live lab.</p>
                )}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
