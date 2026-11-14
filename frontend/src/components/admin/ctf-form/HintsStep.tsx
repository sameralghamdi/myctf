import { Plus, Trash2 } from "lucide-react";
import { Button } from "../../ui/Button";
import { Input, Textarea } from "../../ui/Field";
import { MAX_HINTS } from "./constants";
import { StepHeading } from "./StepHeading";
import type { HintDraft, StepProps } from "./types";

let hintCounter = 0;

function newHint(): HintDraft {
  hintCounter += 1;
  return { id: `h${hintCounter}`, body: "", cost: "0" };
}

export function HintsStep({ values, errors, onChange }: StepProps) {
  const { hints } = values;

  function updateHint(id: string, patch: Partial<HintDraft>) {
    onChange({ hints: hints.map((hint) => (hint.id === id ? { ...hint, ...patch } : hint)) });
  }

  return (
    <div className="flex flex-col gap-8">
      <StepHeading
        title="Hints"
        description="Optional. Players unlock hints in order; a cost is taken off their score when they do."
      />

      {hints.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-gray-800 p-8 text-center">
          <p className="text-sm text-gray-400">
            No hints yet. Start with a gentle nudge, then get more specific.
          </p>
          <Button variant="secondary" onClick={() => onChange({ hints: [newHint()] })}>
            <Plus aria-hidden="true" className="h-4 w-4" />
            Add the first hint
          </Button>
        </div>
      ) : (
        <ol className="flex flex-col gap-4">
          {hints.map((hint, index) => (
            <li
              key={hint.id}
              className="flex flex-col gap-4 rounded-lg border border-gray-800 bg-gray-950 p-6"
            >
              <div className="flex items-center justify-between gap-4">
                <span className="font-mono text-xs uppercase tracking-wide text-gray-400">
                  Hint {index + 1}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={`Remove hint ${index + 1}`}
                  onClick={() => onChange({ hints: hints.filter((item) => item.id !== hint.id) })}
                >
                  <Trash2 aria-hidden="true" className="h-4 w-4" />
                  Remove
                </Button>
              </div>
              <div className="grid gap-6 md:grid-cols-4">
                <div className="md:col-span-3">
                  <Textarea
                    id={`hint-${hint.id}-body`}
                    label="Hint text"
                    rows={2}
                    placeholder="e.g. What happens if the username contains a quote?"
                    value={hint.body}
                    error={errors[`hint-${hint.id}-body`]}
                    onChange={(event) => updateHint(hint.id, { body: event.target.value })}
                  />
                </div>
                <Input
                  id={`hint-${hint.id}-cost`}
                  label="Cost (points)"
                  inputMode="numeric"
                  className="font-mono"
                  value={hint.cost}
                  error={errors[`hint-${hint.id}-cost`]}
                  onChange={(event) => updateHint(hint.id, { cost: event.target.value.trim() })}
                />
              </div>
            </li>
          ))}
        </ol>
      )}

      {hints.length > 0 && (
        <div className="flex flex-wrap items-center gap-4">
          <Button
            variant="secondary"
            disabled={hints.length >= MAX_HINTS}
            onClick={() => onChange({ hints: [...hints, newHint()] })}
          >
            <Plus aria-hidden="true" className="h-4 w-4" />
            Add another hint
          </Button>
          <span className="text-sm text-gray-400">
            {hints.length} of {MAX_HINTS}
          </span>
        </div>
      )}
    </div>
  );
}
