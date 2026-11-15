import type { ReactNode } from "react";
import { cn, focusRing } from "../../../lib/cn";
import { DifficultyBadge } from "../../ui/ChallengeBadges";
import { Field } from "../../ui/Field";
import { Markdown } from "../../ui/Markdown";
import { SegmentedControl, type SegmentOption } from "../../ui/SegmentedControl";
import { StepHeading } from "./StepHeading";
import type { CategoryOption, StepId, StepProps } from "./types";

type Visibility = "published" | "draft";

const VISIBILITY: SegmentOption<Visibility>[] = [
  { value: "published", label: "Publish now" },
  { value: "draft", label: "Save as draft" },
];

interface ReviewStepProps extends StepProps {
  categories: CategoryOption[];
  onEdit: (step: StepId) => void;
}

interface RowProps {
  label: string;
  step: StepId;
  onEdit: (step: StepId) => void;
  children: ReactNode;
}

function Row({ label, step, onEdit, children }: RowProps) {
  return (
    <div className="grid gap-2 border-b border-gray-800 py-4 last:border-b-0 md:grid-cols-4 md:gap-6">
      <dt className="text-sm font-medium text-gray-400">{label}</dt>
      <dd className="min-w-0 text-sm text-gray-300 md:col-span-2">{children}</dd>
      <div className="md:text-right">
        <button
          type="button"
          onClick={() => onEdit(step)}
          className={cn(
            "rounded text-sm font-medium text-brand-400 transition-colors duration-200 hover:text-brand-300 hover:underline",
            focusRing,
          )}
        >
          Edit
        </button>
      </div>
    </div>
  );
}

export function ReviewStep({ values, onChange, categories, onEdit }: ReviewStepProps) {
  const categoryName =
    categories.find((category) => category.slug === values.category)?.name ?? values.category;

  return (
    <div className="flex flex-col gap-8">
      <StepHeading
        title="Review"
        description="Check everything once more. Nothing is saved until you press the button below."
      />

      <dl className="rounded-lg border border-gray-800 bg-gray-950 px-6">
        <Row label="Title" step="basics" onEdit={onEdit}>
          <span className="font-medium text-gray-50">{values.title}</span>
          <span className="block font-mono text-xs text-gray-400">/challenges/{values.slug}</span>
        </Row>
        <Row label="Category" step="basics" onEdit={onEdit}>
          {categoryName}
        </Row>
        <Row label="Difficulty & points" step="basics" onEdit={onEdit}>
          <span className="flex flex-wrap items-center gap-2">
            <DifficultyBadge difficulty={values.difficulty} />
            <span className="font-mono text-brand-400">{values.points} pts</span>
          </span>
        </Row>
        <Row label="Description" step="content" onEdit={onEdit}>
          <Markdown source={values.description} />
        </Row>
        {values.kind === "static" ? (
          <>
            <Row label="Target URL" step="target" onEdit={onEdit}>
              {values.targetUrl.trim() ? (
                <span className="break-all font-mono text-xs">{values.targetUrl.trim()}</span>
              ) : (
                <span className="text-gray-400">None</span>
              )}
            </Row>
            <Row label="Flag" step="target" onEdit={onEdit}>
              <span className="font-mono text-xs">
                MYCTF{"{"}••••••••{"}"}
              </span>
              <span className="block text-xs text-gray-400">
                Hidden. {values.flag.trim().length} characters, stored as a hash.
              </span>
            </Row>
          </>
        ) : (
          <Row label="Built-in lab" step="target" onEdit={onEdit}>
            <span className="font-mono text-xs">{values.labKind}</span>
            <span className="block text-xs text-gray-400">A new flag per player and session.</span>
          </Row>
        )}
        <Row label="Hints" step="hints" onEdit={onEdit}>
          {values.hints.length === 0 ? (
            <span className="text-gray-400">None</span>
          ) : (
            <ol className="flex list-decimal flex-col gap-2 pl-6">
              {values.hints.map((hint) => (
                <li key={hint.id}>
                  {hint.body}
                  <span className="font-mono text-xs text-gray-400">
                    {" "}
                    · {hint.cost === "0" ? "free" : `−${hint.cost} pts`}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </Row>
      </dl>

      <Field
        id="ctf-visibility"
        label="Visibility"
        hint={
          values.published
            ? "Players will see the challenge in the catalog right away."
            : "Only admins can see and test a draft. Publish it later from Manage challenges."
        }
      >
        <SegmentedControl
          label="Visibility"
          options={VISIBILITY}
          value={values.published ? "published" : "draft"}
          onChange={(visibility) => onChange({ published: visibility === "published" })}
        />
      </Field>
    </div>
  );
}
