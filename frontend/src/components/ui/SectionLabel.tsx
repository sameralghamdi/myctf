import type { ReactNode } from "react";

/** Small overline heading used on cards. */
export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="text-xs font-medium uppercase tracking-wider text-gray-400">{children}</h2>
  );
}
