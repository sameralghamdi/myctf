import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
import { APP_TIME_ZONE, parseApiDate } from "../../lib/format";

export interface RaceSeries {
  display_name: string;
  username: string;
  rank: number;
  is_me: boolean;
  points: { at: string; score: number }[];
}

/** Categorical slots in fixed order (validated on the dark card surface). */
const SLOTS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"];
const HEIGHT = 260;
const PAD = { top: 16, right: 16, bottom: 28, left: 44 };

/** A clean tick step (1, 2, 2.5 or 5 × 10^n) giving about four intervals. */
function niceStep(max: number): number {
  const raw = Math.max(max, 1) / 4;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normalized = raw / magnitude;
  return ([1, 2, 2.5, 5, 10].find((s) => normalized <= s) ?? 10) * magnitude;
}

/** Score at time t for a step series (score holds until the next event). */
function scoreAt(points: { t: number; score: number }[], t: number): number {
  let score = 0;
  for (const p of points) {
    if (p.t <= t) score = p.score;
    else break;
  }
  return score;
}

/**
 * Cumulative score over time for the top players (step lines: a score jumps on
 * each solve). Hover anywhere for a crosshair and everyone's score at that moment.
 */
export function ScoreRace({ series }: { series: RaceSeries[] }) {
  const wrap = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  const [hoverT, setHoverT] = useState<number | null>(null);

  useEffect(() => {
    const element = wrap.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(280, entry.contentRect.width)));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const model = useMemo(() => {
    const parsed = series.map((s, index) => ({
      ...s,
      color: SLOTS[index % SLOTS.length],
      pts: s.points.map((p) => ({ t: parseApiDate(p.at).getTime(), score: p.score })),
    }));
    const times = parsed.flatMap((s) => s.pts.map((p) => p.t));
    const now = Date.now();
    const start = times.length ? Math.min(...times) : now - 86400000;
    const span = Math.max(now - start, 3600000);
    const t0 = start - span * 0.04;
    const t1 = now;
    const top = Math.max(0, ...parsed.flatMap((s) => s.pts.map((p) => p.score)));
    const tickStep = niceStep(top || 100);
    const maxScore = Math.max(tickStep, Math.ceil(top / tickStep) * tickStep);
    return { parsed, t0, t1, maxScore, tickStep };
  }, [series]);

  const innerW = width - PAD.left - PAD.right;
  const innerH = HEIGHT - PAD.top - PAD.bottom;
  const x = (t: number) => PAD.left + ((t - model.t0) / (model.t1 - model.t0)) * innerW;
  const y = (score: number) => PAD.top + innerH - (score / model.maxScore) * innerH;

  const spanMs = model.t1 - model.t0;
  const tickFmt = new Intl.DateTimeFormat("en", spanMs < 2 * 86400000
    ? { hour: "2-digit", minute: "2-digit", timeZone: APP_TIME_ZONE }
    : { month: "short", day: "numeric", timeZone: APP_TIME_ZONE });
  const tipFmt = new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", timeZone: APP_TIME_ZONE });
  const tickCount = width < 480 ? 3 : 5;
  const xTicks = Array.from({ length: tickCount }, (_, i) => model.t0 + (spanMs * (i + 0.5)) / tickCount);
  const yTicks = Array.from({ length: Math.round(model.maxScore / model.tickStep) + 1 }, (_, i) => i * model.tickStep);

  const path = (pts: { t: number; score: number }[]) => {
    let d = `M ${x(model.t0)} ${y(0)}`;
    for (const p of pts) d += ` H ${x(p.t)} V ${y(p.score)}`;
    return `${d} H ${x(model.t1)}`;
  };

  function onMove(event: PointerEvent<SVGRectElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - box.left) / box.width;
    setHoverT(model.t0 + Math.max(0, Math.min(1, ratio)) * spanMs);
  }

  const hoverRows = hoverT === null ? [] : model.parsed
    .map((s) => ({ name: s.display_name, color: s.color, me: s.is_me, score: scoreAt(s.pts, hoverT) }))
    .sort((a, b) => b.score - a.score);
  const tipLeft = hoverT === null ? 0 : x(hoverT);
  const flip = tipLeft > width - 200;

  return (
    <figure className="flex flex-col gap-4">
      <ul className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-gray-300" aria-label="Legend">
        {model.parsed.map((s) => (
          <li key={s.username} className="flex items-center gap-2">
            <span aria-hidden="true" className="block h-[3px] w-4 rounded-full" style={{ backgroundColor: s.color }} />
            <span className={s.is_me ? "font-semibold text-gray-50" : undefined}>
              #{s.rank} {s.display_name}
              {s.is_me && " (you)"}
            </span>
          </li>
        ))}
      </ul>
      <div ref={wrap} className="relative w-full">
        <svg width={width} height={HEIGHT} role="img" aria-label="Score over time for the top players" className="block">
          {yTicks.map((tick) => (
            <g key={tick}>
              <line x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} stroke="#1f2937" strokeWidth={1} />
              <text x={PAD.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" fontSize={11} fill="#9ca3af">
                {tick.toLocaleString("en")}
              </text>
            </g>
          ))}
          {xTicks.map((tick) => (
            <text key={tick} x={x(tick)} y={HEIGHT - 8} textAnchor="middle" fontSize={11} fill="#9ca3af">
              {tickFmt.format(new Date(tick))}
            </text>
          ))}
          {model.parsed.map((s) => (
            <path
              key={s.username}
              d={path(s.pts)}
              fill="none"
              stroke={s.color}
              strokeWidth={s.is_me ? 3 : 2}
              strokeLinejoin="round"
              strokeLinecap="round"
              className="race-line"
              opacity={hoverT === null ? 1 : 0.9}
            />
          ))}
          {model.parsed.map((s) => {
            const last = s.pts[s.pts.length - 1];
            if (!last) return null;
            return (
              <circle key={s.username} cx={x(model.t1)} cy={y(last.score)} r={4} fill={s.color} stroke="#111827" strokeWidth={2} />
            );
          })}
          {hoverT !== null && (
            <g pointerEvents="none">
              <line x1={x(hoverT)} x2={x(hoverT)} y1={PAD.top} y2={PAD.top + innerH} stroke="#4b5563" strokeWidth={1} />
              {model.parsed.map((s) => (
                <circle key={s.username} cx={x(hoverT)} cy={y(scoreAt(s.pts, hoverT))} r={4} fill={s.color} stroke="#111827" strokeWidth={2} />
              ))}
            </g>
          )}
          <rect
            x={PAD.left}
            y={PAD.top}
            width={innerW}
            height={innerH}
            fill="transparent"
            onPointerMove={onMove}
            onPointerLeave={() => setHoverT(null)}
          />
        </svg>
        {hoverT !== null && (
          <div
            role="tooltip"
            className="pointer-events-none absolute top-2 z-10 min-w-44 rounded-lg border border-gray-700 bg-gray-950/95 p-2 text-xs shadow-lg"
            style={flip ? { right: width - tipLeft + 12 } : { left: tipLeft + 12 }}
          >
            <p className="pb-1 text-gray-400">{tipFmt.format(new Date(hoverT))}</p>
            <ul className="flex flex-col gap-1">
              {hoverRows.map((row) => (
                <li key={row.name} className="flex items-center justify-between gap-4">
                  <span className="flex items-center gap-2 text-gray-300">
                    <span aria-hidden="true" className="block h-2 w-2 rounded-full" style={{ backgroundColor: row.color }} />
                    <span className={row.me ? "font-semibold text-gray-50" : undefined}>{row.name}</span>
                  </span>
                  <span className="font-mono text-gray-50">{row.score.toLocaleString("en")}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <details className="text-xs text-gray-400">
        <summary className="cursor-pointer select-none hover:text-gray-200">Show as table</summary>
        <table className="mt-2 w-full text-left">
          <thead>
            <tr className="text-gray-400">
              <th className="py-1 font-medium">Player</th>
              <th className="py-1 text-right font-medium">Score now</th>
              <th className="py-1 text-right font-medium">Point events</th>
            </tr>
          </thead>
          <tbody>
            {model.parsed.map((s) => (
              <tr key={s.username} className="border-t border-gray-800 text-gray-300">
                <td className="py-1">{s.display_name}</td>
                <td className="py-1 text-right font-mono">{(s.pts[s.pts.length - 1]?.score ?? 0).toLocaleString("en")}</td>
                <td className="py-1 text-right font-mono">{s.pts.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
