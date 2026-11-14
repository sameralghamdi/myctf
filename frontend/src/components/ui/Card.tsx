import type { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Adds a hover treatment for cards that act as links. */
  interactive?: boolean;
}

export function Card({ interactive = false, className, ...rest }: CardProps) {
  return (
    <div
      {...rest}
      className={cn(
        "rounded-xl border border-gray-800 bg-gray-900 p-6 shadow-sm",
        interactive && "transition-colors duration-200 hover:border-gray-700 hover:bg-gray-800/50",
        className,
      )}
    />
  );
}
