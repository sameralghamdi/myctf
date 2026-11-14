import { Field, Input, Select, controlErrorClasses } from "../../ui/Field";
import { SegmentedControl, type SegmentOption } from "../../ui/SegmentedControl";
import { DIFFICULTY_LABELS } from "../../../lib/format";
import type { Difficulty } from "../../../types/api";
import { DEFAULT_POINTS } from "./constants";
import { StepHeading } from "./StepHeading";
import type { CategoryOption, StepProps } from "./types";
import { slugify } from "./validation";

const DIFFICULTIES = (Object.keys(DIFFICULTY_LABELS) as Difficulty[]).map(
  (value): SegmentOption<Difficulty> => ({ value, label: DIFFICULTY_LABELS[value] }),
);

interface BasicsStepProps extends StepProps {
  categories: CategoryOption[];
}

export function BasicsStep({ values, errors, onChange, categories }: BasicsStepProps) {
  return (
    <div className="flex flex-col gap-8">
      <StepHeading
        title="Basics"
        description="How the challenge appears in the catalog: its name, where it is filed and what it is worth."
      />

      <div className="grid gap-6 md:grid-cols-2">
        <Input
          id="ctf-title"
          label="Challenge title"
          placeholder="e.g. Login Bypass"
          maxLength={120}
          value={values.title}
          error={errors.title}
          onChange={(event) => {
            const title = event.target.value;
            onChange(values.slugEdited ? { title } : { title, slug: slugify(title) });
          }}
        />
        <Input
          id="ctf-slug"
          label="URL name"
          placeholder="login-bypass"
          className="font-mono"
          spellCheck={false}
          maxLength={49}
          value={values.slug}
          error={errors.slug}
          hint={`Players open it at /challenges/${values.slug || "…"}. It can't be changed later.`}
          onChange={(event) =>
            onChange({ slug: event.target.value.toLowerCase(), slugEdited: true })
          }
        />
      </div>

      <Field id="ctf-category" label="Category" error={errors.category}>
        <Select
          id="ctf-category"
          value={values.category}
          className={errors.category ? controlErrorClasses : undefined}
          onChange={(event) => onChange({ category: event.target.value })}
        >
          {categories.map((category) => (
            <option key={category.slug} value={category.slug}>
              {category.name}
            </option>
          ))}
        </Select>
      </Field>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2">
          <Field id="ctf-difficulty" label="Difficulty">
            <SegmentedControl
              label="Difficulty"
              options={DIFFICULTIES}
              value={values.difficulty}
              onChange={(difficulty) =>
                onChange(
                  values.pointsEdited
                    ? { difficulty }
                    : { difficulty, points: String(DEFAULT_POINTS[difficulty]) },
                )
              }
            />
          </Field>
        </div>
        <Input
          id="ctf-points"
          label="Points"
          inputMode="numeric"
          className="font-mono"
          value={values.points}
          error={errors.points}
          hint={`Default for ${DIFFICULTY_LABELS[values.difficulty]}: ${DEFAULT_POINTS[values.difficulty]}`}
          onChange={(event) => onChange({ points: event.target.value.trim(), pointsEdited: true })}
        />
      </div>
    </div>
  );
}
