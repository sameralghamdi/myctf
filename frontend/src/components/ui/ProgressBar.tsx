interface ProgressBarProps {
  /** 0–100 */
  value: number;
  label?: string;
}

export function ProgressBar({ value, label }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className="h-2 w-full overflow-hidden rounded-full bg-gray-800"
    >
      <div
        className="h-full rounded-full bg-brand-500 transition-all duration-200"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
