import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export type AlertTone = "info" | "success" | "warning" | "danger";

const tones: Record<AlertTone, string> = {
  info: "border-gray-700 bg-gray-800/50 text-gray-300",
  success: "border-green-500/30 bg-green-500/10 text-green-300",
  warning: "border-yellow-500/30 bg-yellow-500/10 text-yellow-300",
  danger: "border-red-500/30 bg-red-500/10 text-red-300",
};

export function Alert({ tone = "info", children }: { tone?: AlertTone; children: ReactNode }) {
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      className={cn("rounded-lg border px-4 py-2 text-sm", tones[tone])}
    >
      {children}
    </div>
  );
}
