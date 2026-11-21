import type { CSSProperties, ReactNode } from "react";
import { cn } from "../../lib/cn";
import type { IconComponent } from "../../types/navigation";
import { AnimatedNumber } from "./AnimatedNumber";
import { Card } from "./Card";

interface StatCardProps {
  label: string;
  /** Numbers count up when they appear; strings are shown as-is. */
  value: string | number;
  sub?: ReactNode;
  tone?: "default" | "brand" | "success" | "warning";
  icon?: IconComponent;
  prefix?: string;
  className?: string;
  style?: CSSProperties;
}

const valueTone = {
  default: "text-gray-50",
  brand: "text-brand-400",
  success: "text-green-400",
  warning: "text-yellow-300",
} as const;

const iconTone = {
  default: "bg-gray-800 text-gray-300",
  brand: "bg-brand-500/10 text-brand-400",
  success: "bg-green-500/10 text-green-400",
  warning: "bg-yellow-500/10 text-yellow-300",
} as const;

export function StatCard({ label, value, sub, tone = "default", icon: Icon, prefix, className, style }: StatCardProps) {
  return (
    <Card className={cn("group lift flex flex-col gap-2", className)} style={style}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm text-gray-400">{label}</span>
        {Icon && (
          <span className={cn("grid h-8 w-8 place-items-center rounded-lg transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6", iconTone[tone])}>
            <Icon aria-hidden="true" className="h-4 w-4" />
          </span>
        )}
      </div>
      <span className={cn("font-mono text-3xl font-semibold tracking-tight", valueTone[tone])}>
        {prefix}
        {typeof value === "number" ? <AnimatedNumber value={value} /> : value}
      </span>
      {sub && <span className="text-xs text-gray-400">{sub}</span>}
    </Card>
  );
}
