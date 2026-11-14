import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import { useApi } from "../../hooks/useApi";
import { api, ApiError, toMessage } from "../../lib/api";
import type { PublicInfo } from "../../types/api";
import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { BasicsStep } from "./ctf-form/BasicsStep";
import { INITIAL_VALUES, PRESET_CATEGORIES, STEPS } from "./ctf-form/constants";
import { ContentStep } from "./ctf-form/ContentStep";
import { HintsStep } from "./ctf-form/HintsStep";
import { ReviewStep } from "./ctf-form/ReviewStep";
import { Stepper } from "./ctf-form/Stepper";
import { TargetStep } from "./ctf-form/TargetStep";
import type {
  CategoryOption,
  CtfFormErrors,
  CtfFormValues,
  StepId,
} from "./ctf-form/types";
import { firstInvalidStep, toManifest, validateStep } from "./ctf-form/validation";

interface CreatedChallenge {
  slug: string;
  title: string;
  published: boolean;
}

interface AdminCTFFormProps {
  /** Called after the challenge is saved, e.g. to refresh a list. */
  onCreated?: (challenge: CreatedChallenge) => void;
}

/**
 * Step-by-step form for creating a challenge. It only collects and checks
 * input; the server (POST /admin/api/challenges/publish) validates everything
 * again and is the one that enforces the administrator role.
 */
export function AdminCTFForm({ onCreated }: AdminCTFFormProps) {
  const [values, setValues] = useState<CtfFormValues>(INITIAL_VALUES);
  const [errors, setErrors] = useState<CtfFormErrors>({});
  const [step, setStep] = useState<StepId>("basics");
  const [reachedIndex, setReachedIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [created, setCreated] = useState<CreatedChallenge | null>(null);

  const { data: serverCategories } = useApi<CategoryOption[]>("/admin/api/categories");
  const { data: publicInfo } = useApi<PublicInfo>("/api/public");

  // Presets first, then anything on the server that isn't a preset. Server names win.
  const categories = useMemo(() => {
    const bySlug = new Map(PRESET_CATEGORIES.map((category) => [category.slug, category]));
    (serverCategories ?? []).forEach((category) => bySlug.set(category.slug, category));
    return Array.from(bySlug.values());
  }, [serverCategories]);

  const stepIndex = STEPS.findIndex((item) => item.id === step);
  const isLastStep = stepIndex === STEPS.length - 1;

  function handleChange(patch: Partial<CtfFormValues>) {
    setValues((current) => ({ ...current, ...patch }));
    setSubmitError(null);
  }

  function goTo(target: StepId) {
    setErrors({});
    setStep(target);
  }

  function goNext() {
    const problems = validateStep(step, values);
    setErrors(problems);
    if (Object.keys(problems).length > 0) return;
    const nextIndex = stepIndex + 1;
    setReachedIndex((current) => Math.max(current, nextIndex));
    setStep(STEPS[nextIndex].id);
  }

  async function submit() {
    const invalid = firstInvalidStep(values);
    if (invalid) {
      setStep(invalid.step);
      setErrors(invalid.errors);
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api("/admin/api/challenges/publish", {
        method: "POST",
        body: toManifest(values, categories),
      });
      const result = { slug: values.slug, title: values.title.trim(), published: values.published };
      // Drop the flag from memory as soon as it has been sent.
      setValues(INITIAL_VALUES);
      setCreated(result);
      onCreated?.(result);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) {
        setStep("basics");
        setErrors({ slug: "This URL name is already used by another challenge." });
      } else {
        setSubmitError(toMessage(caught));
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLastStep) void submit();
    else goNext();
  }

  function startOver() {
    setCreated(null);
    setErrors({});
    setStep("basics");
    setReachedIndex(0);
  }

  if (created) {
    return (
      <Card className="flex flex-col items-center gap-6 p-12 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full border border-green-500/30 bg-green-500/10 text-green-300">
          <Check aria-hidden="true" className="h-6 w-6" />
        </span>
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-semibold text-gray-50">
            {created.published ? "Challenge published" : "Draft saved"}
          </h2>
          <p className="max-w-md text-sm text-gray-400">
            <span className="text-gray-300">{created.title}</span>{" "}
            {created.published
              ? "is now live in the catalog."
              : "is saved as a draft. Only admins can open it until you publish it."}
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          <Button href={`/challenges/${created.slug}`}>Open challenge</Button>
          <Button variant="secondary" onClick={startOver}>
            Create another
          </Button>
          <Button variant="ghost" href="/admin/challenges">
            Manage challenges
          </Button>
        </div>
      </Card>
    );
  }

  const stepProps = { values, errors, onChange: handleChange };

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-6">
      <Stepper current={step} reachedIndex={reachedIndex} onSelect={goTo} />

      <Card className="flex flex-col gap-8 md:p-8">
        {step === "basics" && <BasicsStep {...stepProps} categories={categories} />}
        {step === "content" && <ContentStep {...stepProps} />}
        {step === "target" && (
          <TargetStep {...stepProps} labKinds={publicInfo?.live_kinds ?? []} />
        )}
        {step === "hints" && <HintsStep {...stepProps} />}
        {step === "review" && (
          <ReviewStep {...stepProps} categories={categories} onEdit={goTo} />
        )}

        {submitError && <Alert tone="danger">Could not save: {submitError}</Alert>}

        <div className="flex items-center justify-between gap-4 border-t border-gray-800 pt-6">
          <Button
            variant="ghost"
            disabled={stepIndex === 0 || submitting}
            onClick={() => goTo(STEPS[stepIndex - 1].id)}
          >
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            Back
          </Button>
          <Button type="submit" disabled={submitting}>
            {isLastStep ? (
              submitting ? "Saving…" : values.published ? "Publish challenge" : "Save draft"
            ) : (
              <>
                Continue
                <ArrowRight aria-hidden="true" className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </Card>
    </form>
  );
}
