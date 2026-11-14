import { cn, focusRing } from "../../lib/cn";

interface TabsProps<T extends string> {
  tabs: { id: T; label: string }[];
  active: T;
  onChange: (id: T) => void;
}

export function Tabs<T extends string>({ tabs, active, onChange }: TabsProps<T>) {
  return (
    <div role="tablist" className="flex flex-wrap gap-2 border-b border-gray-800">
      {tabs.map((tab) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(tab.id)}
            className={cn(
              "-mb-px h-10 border-b-2 px-4 text-sm font-medium transition-colors duration-200",
              focusRing,
              selected
                ? "border-brand-500 text-gray-50"
                : "border-transparent text-gray-400 hover:text-gray-50",
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
