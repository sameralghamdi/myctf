import { Check } from "lucide-react";
import { cn, focusRing } from "../../../lib/cn";
import { STEPS } from "./constants";
import type { StepId } from "./types";

interface StepperProps {
  current: StepId;
  /** Furthest step the admin has reached; earlier steps can be revisited. */
  reachedIndex: number;
  onSelect: (step: StepId) => void;
}

export function Stepper({ current, reachedIndex, onSelect }: StepperProps) {
  const currentIndex = STEPS.findIndex((step) => step.id === current);

  return (
    <nav aria-label="Progress">
      <p className="text-sm text-gray-400 md:hidden">
        Step {currentIndex + 1} of {STEPS.length}
        <span className="text-gray-50"> · {STEPS[currentIndex].label}</span>
      </p>
      <ol className="hidden items-center gap-2 md:flex">
        {STEPS.map((step, index) => {
          const active = index === currentIndex;
          const done = index < currentIndex;
          const reachable = index <= reachedIndex;
          return (
            <li key={step.id} className="flex flex-1 items-center gap-2 last:flex-none">
              <button
                type="button"
                disabled={!reachable}
                aria-current={active ? "step" : undefined}
                onClick={() => onSelect(step.id)}
                className={cn(
                  "flex items-center gap-2 rounded-lg p-2 text-sm font-medium transition-colors duration-200",
                  "disabled:pointer-events-none",
                  focusRing,
                  active ? "text-gray-50" : "text-gray-400",
                  reachable && !active && "hover:bg-gray-800 hover:text-gray-50",
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border font-mono text-xs",
                    "transition-colors duration-200",
                    active && "border-brand-500 bg-brand-500/10 text-brand-400",
                    done && "border-brand-600 bg-brand-600 text-white",
                    !active && !done && "border-gray-800 bg-gray-900 text-gray-400",
                  )}
                >
                  {done ? <Check aria-hidden="true" className="h-4 w-4" /> : index + 1}
                </span>
                <span className="whitespace-nowrap">{step.label}</span>
              </button>
              {index < STEPS.length - 1 && (
                <span
                  aria-hidden="true"
                  className={cn(
                    "h-px flex-1 transition-colors duration-200",
                    done ? "bg-brand-600" : "bg-gray-800",
                  )}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
