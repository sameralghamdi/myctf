import type { HTMLAttributes, PointerEvent } from "react";
import { cn } from "../../lib/cn";

/** A card with a soft light that follows the pointer. */
export function SpotlightCard({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  function onMove(event: PointerEvent<HTMLDivElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    event.currentTarget.style.setProperty("--x", `${event.clientX - box.left}px`);
    event.currentTarget.style.setProperty("--y", `${event.clientY - box.top}px`);
  }
  return (
    <div
      {...rest}
      onPointerMove={onMove}
      className={cn(
        "group relative overflow-hidden rounded-xl border border-gray-800 bg-gray-900 p-6 transition-colors duration-300 hover:border-gray-700",
        className,
      )}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: "radial-gradient(320px circle at var(--x) var(--y), rgb(239 68 68 / 0.12), transparent 60%)" }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
