import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

interface PageContainerProps {
  children: ReactNode;
  /** Use for full-bleed screens such as the challenge play view. */
  wide?: boolean;
}

/** Standard page body: consistent gutters and an 8-point gap between sections. */
export function PageContainer({ children, wide = false }: PageContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto flex w-full flex-col gap-8 px-6 py-8 lg:px-8",
        wide ? "max-w-none" : "max-w-6xl",
      )}
    >
      {children}
    </div>
  );
}
