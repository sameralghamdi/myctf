import { AnimatedNumber } from "./AnimatedNumber";

interface ScoreChipProps {
  score: number;
  rank: number | null;
}

export function ScoreChip({ score, rank }: ScoreChipProps) {
  return (
    <div className="hidden h-8 items-center gap-4 rounded-full border border-gray-800 bg-gray-900 px-4 text-sm text-gray-400 sm:flex">
      <span>
        <AnimatedNumber value={score} className="font-mono font-semibold text-brand-400" /> pts
      </span>
      <span aria-hidden="true" className="h-4 w-px bg-gray-800" />
      <span>
        rank <span className="font-mono font-semibold text-brand-400">#{rank ?? "—"}</span>
      </span>
    </div>
  );
}
