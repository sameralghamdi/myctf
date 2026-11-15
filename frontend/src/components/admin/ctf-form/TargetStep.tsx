import { Sparkles } from "lucide-react";
import { Alert } from "../../ui/Alert";
import { Button } from "../../ui/Button";
import { Field, Input, Select, controlErrorClasses } from "../../ui/Field";
import { SecretInput } from "../../ui/SecretInput";
import { SegmentedControl, type SegmentOption } from "../../ui/SegmentedControl";
import { StepHeading } from "./StepHeading";
import type { ChallengeKind, StepProps } from "./types";
import { generateFlag } from "./validation";

const KINDS: SegmentOption<ChallengeKind>[] = [
  { value: "static", label: "Your own target" },
  { value: "lab", label: "Built-in lab" },
];

interface TargetStepProps extends StepProps {
  /** Lab handlers registered on the server (from /api/public). */
  labKinds: string[];
}

export function TargetStep({ values, errors, onChange, labKinds }: TargetStepProps) {
  return (
    <div className="flex flex-col gap-8">
      <StepHeading
        title="Target & flag"
        description="Where the player attacks, and the secret that proves they solved it."
      />

      <Field id="ctf-kind" label="Challenge type">
        <SegmentedControl
          label="Challenge type"
          options={KINDS}
          value={values.kind}
          onChange={(kind) => onChange({ kind })}
        />
      </Field>

      {values.kind === "static" ? (
        <>
          <Input
            id="ctf-target-url"
            label="Target URL (optional)"
            type="url"
            inputMode="url"
            placeholder="https://target.example.com"
            className="font-mono"
            spellCheck={false}
            value={values.targetUrl}
            error={errors.targetUrl}
            hint="The web instance players should attack. Leave empty for challenges with no website (crypto, forensics…)."
            onChange={(event) => onChange({ targetUrl: event.target.value })}
          />

          <div className="flex flex-col gap-4">
            <SecretInput
              id="ctf-flag"
              label="Flag"
              placeholder="MYCTF{...}"
              value={values.flag}
              error={errors.flag}
              hint="Stored as a one-way hash. Nobody, including admins, can read it back later, so keep your own copy."
              onChange={(event) => onChange({ flag: event.target.value })}
            />
            <div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onChange({ flag: generateFlag(values.slug) })}
              >
                <Sparkles aria-hidden="true" className="h-4 w-4" />
                Generate a random flag
              </Button>
            </div>
          </div>
        </>
      ) : (
        <>
          <Field
            id="ctf-lab-kind"
            label="Lab"
            error={errors.labKind}
            hint="A simulated vulnerable app that runs inside MyCTF, one private copy per player."
          >
            <Select
              id="ctf-lab-kind"
              value={values.labKind}
              className={errors.labKind ? controlErrorClasses : "font-mono"}
              onChange={(event) => onChange({ labKind: event.target.value })}
            >
              <option value="">Choose a lab…</option>
              {labKinds.map((kind) => (
                <option key={kind} value={kind}>
                  {kind}
                </option>
              ))}
            </Select>
          </Field>
          <Alert>
            Built-in labs create a fresh flag for every player each time they start the lab, so
            there is no flag to enter here and flags can't be shared between players.
          </Alert>
        </>
      )}
    </div>
  );
}
