import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  /** Right-aligned actions, e.g. a primary Button. */
  actions?: ReactNode;
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-50">{title}</h1>
        {description && <p className="max-w-2xl text-sm text-gray-400">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
