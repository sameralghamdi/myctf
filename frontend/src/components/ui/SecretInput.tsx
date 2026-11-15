import { Eye, EyeOff } from "lucide-react";
import { useState, type InputHTMLAttributes } from "react";
import { cn, focusRing } from "../../lib/cn";
import { controlClasses, controlErrorClasses, Field } from "./Field";

type SecretInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  id: string;
  label: string;
  hint?: string;
  error?: string;
};

/** Masked text input with a show/hide toggle. Used for flags and other secrets. */
export function SecretInput({ id, label, hint, error, className, ...rest }: SecretInputProps) {
  const [visible, setVisible] = useState(false);
  const Icon = visible ? EyeOff : Eye;

  return (
    <Field id={id} label={label} hint={hint} error={error}>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          autoComplete="new-password"
          spellCheck={false}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          {...rest}
          className={cn(
            controlClasses,
            "h-10 pr-12 font-mono",
            error && controlErrorClasses,
            className,
          )}
        />
        <button
          type="button"
          aria-label={visible ? `Hide ${label}` : `Show ${label}`}
          aria-pressed={visible}
          onClick={() => setVisible((current) => !current)}
          className={cn(
            "absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-lg text-gray-400",
            "transition-colors duration-200 hover:text-gray-50",
            focusRing,
          )}
        >
          <Icon aria-hidden="true" className="h-4 w-4" />
        </button>
      </div>
    </Field>
  );
}
