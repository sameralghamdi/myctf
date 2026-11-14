import { cn } from "../../lib/cn";
import { Card } from "./Card";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  tone?: "default" | "brand" | "success";
}

const valueTone = {
  default: "text-gray-50",
  brand: "text-brand-400",
  success: "text-green-400",
} as const;

export function StatCard({ label, value, sub, tone = "default" }: StatCardProps) {
  return (
    <Card className="flex flex-col gap-2">
      <span className="text-sm text-gray-400">{label}</span>
      <span className={cn("font-mono text-2xl font-semibold", valueTone[tone])}>{value}</span>
      {sub && <span className="text-xs text-gray-400">{sub}</span>}
    </Card>
  );
}
