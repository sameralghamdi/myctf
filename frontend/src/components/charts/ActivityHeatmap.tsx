import { useMemo, useState } from "react";

interface Day {
  date: string; // YYYY-MM-DD (UTC)
  solves: number;
}

/** Sequential, one hue (validated against the card surface): more solves = brighter. */
const RAMP = ["#1f2937", "#b91c1c", "#dc2626", "#f87171", "#fecaca"];
const step = (n: number) => (n <= 0 ? 0 : Math.min(4, n));
const CELL = 14;
const GAP = 3;
const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

const monthFmt = new Intl.DateTimeFormat("en", { month: "short", timeZone: "UTC" });
const dayFmt = new Intl.DateTimeFormat("en", { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" });

/** GitHub-style calendar of solves per day, newest week on the right. */
export function ActivityHeatmap({ days }: { days: Day[] }) {
  const [hover, setHover] = useState<{ day: Day; x: number; y: number } | null>(null);

  const { weeks, months, total, best } = useMemo(() => {
    const first = new Date(`${days[0]?.date ?? "1970-01-01"}T00:00:00Z`);
    const lead = first.getUTCDay(); // empty slots before the first day (Sunday-first rows)
    const cells: (Day | null)[] = [...Array<null>(lead).fill(null), ...days];
    const cols: (Day | null)[][] = [];
    for (let i = 0; i < cells.length; i += 7) cols.push(cells.slice(i, i + 7));
    const labels: { col: number; label: string }[] = [];
    let lastMonth = -1;
    cols.forEach((col, index) => {
      const firstDay = col.find(Boolean);
      if (!firstDay) return;
      const month = new Date(`${firstDay.date}T00:00:00Z`).getUTCMonth();
      if (month !== lastMonth) {
        labels.push({ col: index, label: monthFmt.format(new Date(`${firstDay.date}T00:00:00Z`)) });
        lastMonth = month;
      }
    });
    return {
      weeks: cols,
      months: labels,
      total: days.reduce((sum, d) => sum + d.solves, 0),
      best: days.reduce((max, d) => Math.max(max, d.solves), 0),
    };
  }, [days]);

  const width = weeks.length * (CELL + GAP);
  const activeDays = days.filter((d) => d.solves > 0).length;

  return (
    <figure className="flex flex-col gap-4">
      <div className="relative overflow-x-auto pb-2">
        <div className="relative" style={{ width: width + 32 }}>
          <div className="flex pl-8 text-xs text-gray-400" style={{ height: 18 }} aria-hidden="true">
            {months.map((m) => (
              <span key={`${m.col}-${m.label}`} className="absolute" style={{ left: 32 + m.col * (CELL + GAP) }}>
                {m.label}
              </span>
            ))}
          </div>
          <div className="flex">
            <div className="flex w-8 flex-col text-xs text-gray-400" aria-hidden="true" style={{ gap: GAP }}>
              {DAY_LABELS.map((label, i) => (
                <span key={i} style={{ height: CELL, lineHeight: `${CELL}px` }}>
                  {label}
                </span>
              ))}
            </div>
            <div
              role="img"
              aria-label={`${total} solves on ${activeDays} active days in the last ${days.length} days`}
              className="flex"
              style={{ gap: GAP }}
              onMouseLeave={() => setHover(null)}
            >
              {weeks.map((week, w) => (
                <div key={w} className="flex flex-col" style={{ gap: GAP }}>
                  {week.map((day, d) =>
                    day ? (
                      <span
                        key={day.date}
                        onMouseEnter={() => setHover({ day, x: w * (CELL + GAP), y: d * (CELL + GAP) })}
                        className="block rounded-[3px] transition-transform duration-150 hover:scale-125"
                        style={{ width: CELL, height: CELL, backgroundColor: RAMP[step(day.solves)] }}
                      />
                    ) : (
                      <span key={`empty-${d}`} style={{ width: CELL, height: CELL }} />
                    ),
                  )}
                </div>
              ))}
            </div>
          </div>
          {hover && (
            <div
              role="tooltip"
              className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-lg border border-gray-700 bg-gray-950 px-2 py-1 text-xs text-gray-50 shadow-md"
              style={{ left: 32 + hover.x + CELL / 2, top: 18 + hover.y - 6 }}
            >
              <span className="font-semibold">
                {hover.day.solves} {hover.day.solves === 1 ? "solve" : "solves"}
              </span>{" "}
              <span className="text-gray-400">· {dayFmt.format(new Date(`${hover.day.date}T00:00:00Z`))}</span>
            </div>
          )}
        </div>
      </div>
      <figcaption className="flex flex-wrap items-center justify-between gap-4 text-xs text-gray-400">
        <span>
          <span className="font-semibold text-gray-50">{total}</span> solves ·{" "}
          <span className="font-semibold text-gray-50">{activeDays}</span> active days
          {best > 1 && (
            <>
              {" "}
              · best day <span className="font-semibold text-gray-50">{best}</span>
            </>
          )}
        </span>
        <span className="flex items-center gap-2" aria-hidden="true">
          Less
          {RAMP.map((color) => (
            <span key={color} className="block rounded-[3px]" style={{ width: CELL, height: CELL, backgroundColor: color }} />
          ))}
          More
        </span>
      </figcaption>
    </figure>
  );
}
