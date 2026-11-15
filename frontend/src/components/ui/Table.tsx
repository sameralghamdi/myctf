import type { HTMLAttributes, ReactNode, TdHTMLAttributes, ThHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">{children}</table>
    </div>
  );
}

export function Th({ className, ...rest }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      {...rest}
      className={cn(
        "h-10 border-b border-gray-800 px-4 text-xs font-medium uppercase tracking-wider text-gray-400",
        className,
      )}
    />
  );
}

export function Td({ className, ...rest }: TdHTMLAttributes<HTMLTableCellElement>) {
  return <td {...rest} className={cn("h-12 border-b border-gray-800 px-4 text-gray-300", className)} />;
}

interface TrProps extends HTMLAttributes<HTMLTableRowElement> {
  highlight?: boolean;
}

export function Tr({ highlight = false, className, ...rest }: TrProps) {
  return (
    <tr
      {...rest}
      className={cn(
        "transition-colors duration-200",
        highlight ? "bg-brand-500/10" : "hover:bg-gray-800/50",
        className,
      )}
    />
  );
}
