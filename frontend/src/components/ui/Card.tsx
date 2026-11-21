import type { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds a hover treatment for cards that act as links. */
  interactive?: boolean;
  /** No inner padding (for edge-to-edge tables). */
  flush?: boolean;
}

export function Card({ interactive = false, flush = false, className, ...rest }: CardProps) {
  return (
    <div
      {...rest}
      className={cn(
        "rounded-xl border border-gray-800 bg-gray-900 shadow-sm",
        !flush && "p-6",
        interactive && "lift hover:bg-gray-800/40",
        className,
      )}
    />
  );
}
