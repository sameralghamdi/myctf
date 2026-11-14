import type { ReactNode } from "react";
import type { IconComponent } from "../../types/navigation";

interface EmptyStateProps {
  icon: IconComponent;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-8 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-gray-800 text-gray-400">
        <Icon aria-hidden="true" className="h-6 w-6" />
      </span>
      <h3 className="text-base font-semibold text-gray-50">{title}</h3>
      {description && <p className="max-w-sm text-sm text-gray-400">{description}</p>}
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
