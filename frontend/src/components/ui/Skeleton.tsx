import { cn } from "../../lib/cn";

/** Shimmering placeholder block. Size it with className (h-*, w-*). */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("skeleton", className)} />;
}

/** A page-shaped placeholder: header, a row of tiles, two panels. */
export function PageSkeleton({ tiles = 4 }: { tiles?: number }) {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-80 max-w-full" />
      </div>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: tiles }, (_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}
