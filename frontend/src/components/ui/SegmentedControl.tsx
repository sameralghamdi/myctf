import { cn, focusRing } from "../../lib/cn";

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string> {
  /** Accessible name for the group, e.g. "Difficulty". */
  label: string;
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
}

/** A small set of mutually exclusive choices, shown side by side. */
export function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="flex flex-wrap gap-2 rounded-lg border border-gray-800 bg-gray-950 p-2"
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              "h-8 flex-1 whitespace-nowrap rounded-md px-4 text-sm font-medium transition-colors duration-200",
              focusRing,
              selected
                ? "bg-brand-600 text-white shadow-sm"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-50",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
