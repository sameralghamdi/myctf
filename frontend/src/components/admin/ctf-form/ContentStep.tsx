import { useState } from "react";
import { Markdown } from "../../ui/Markdown";
import { Textarea } from "../../ui/Field";
import { Tabs } from "../../ui/Tabs";
import { StepHeading } from "./StepHeading";
import type { StepProps } from "./types";

type Mode = "write" | "preview";

const MODES: { id: Mode; label: string }[] = [
  { id: "write", label: "Write" },
  { id: "preview", label: "Preview" },
];

export function ContentStep({ values, errors, onChange }: StepProps) {
  const [mode, setMode] = useState<Mode>("write");

  return (
    <div className="flex flex-col gap-8">
      <StepHeading
        title="Description"
        description="Tell the player the story and the goal. Don't include the solution: hints come later."
      />

      <div className="flex flex-col gap-4">
        <Tabs tabs={MODES} active={mode} onChange={setMode} />
        {mode === "write" ? (
          <Textarea
            id="ctf-description"
            label="Challenge description"
            rows={12}
            placeholder={"## The goal\nLog in as **admin** without knowing the password.\n\n- Start at the login page\n- The flag is on the admin dashboard"}
            className="font-mono"
            value={values.description}
            error={errors.description}
            hint="Markdown supported: # heading, **bold**, *italic*, `code`, - lists, [link](https://…) and ``` code blocks."
            onChange={(event) => onChange({ description: event.target.value })}
          />
        ) : (
          <div className="min-h-64 rounded-lg border border-gray-800 bg-gray-950 p-6">
            {values.description.trim() ? (
              <Markdown source={values.description} />
            ) : (
              <p className="text-sm text-gray-400">Nothing to preview yet.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
