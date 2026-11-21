import { useEffect, useState } from "react";
import { cn } from "../../lib/cn";

interface ProgressBarProps {
  /** 0–100 */
  value: number;
  label?: string;
  tone?: "brand" | "success";
  size?: "sm" | "md";
}

/** Thin meter that fills in from zero when it first appears. */
export function ProgressBar({ value, label, tone = "brand", size = "md" }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setShown(clamped));
    return () => cancelAnimationFrame(id);
  }, [clamped]);

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className={cn("w-full overflow-hidden rounded-full bg-gray-800", size === "sm" ? "h-1" : "h-2")}
    >
      <div
        className={cn(
          "h-full rounded-full bg-gradient-to-r transition-[width] duration-1000 ease-out",
          tone === "success" ? "from-green-600 to-green-400" : "from-brand-600 to-orange-400",
        )}
        style={{ width: `${shown}%` }}
      />
    </div>
  );
}
