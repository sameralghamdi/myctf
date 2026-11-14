import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export type BadgeTone = "neutral" | "brand" | "success" | "warning" | "danger";

interface BadgeProps {
  tone?: BadgeTone;
  children: ReactNode;
}

const tones: Record<BadgeTone, string> = {
  neutral: "bg-gray-800 text-gray-300 ring-gray-700",
  brand: "bg-brand-500/10 text-brand-400 ring-brand-500/30",
  success: "bg-green-500/10 text-green-400 ring-green-500/30",
  warning: "bg-yellow-500/10 text-yellow-400 ring-yellow-500/30",
  danger: "bg-red-500/10 text-red-400 ring-red-500/30",
};

export function Badge({ tone = "neutral", children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 text-xs font-medium leading-6 ring-1 ring-inset",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}
