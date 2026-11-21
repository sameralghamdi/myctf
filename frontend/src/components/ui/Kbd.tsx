import type { ReactNode } from "react";

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="inline-flex h-6 min-w-6 items-center justify-center rounded-md border border-gray-700 bg-gray-800 px-2 font-mono text-xs text-gray-300">
      {children}
    </kbd>
  );
}
