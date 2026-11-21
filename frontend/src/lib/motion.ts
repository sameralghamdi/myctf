import type { CSSProperties } from "react";

/** Staggered entrance: spread on an element to fade it up after `index` steps. */
export function reveal(index: number, step = 60): { className: string; style: CSSProperties } {
  return { className: "animate-fade-up", style: { animationDelay: `${Math.min(index, 12) * step}ms` } };
}
