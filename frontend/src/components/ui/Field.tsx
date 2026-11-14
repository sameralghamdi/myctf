import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";
import { cn } from "../../lib/cn";

export const controlClasses = cn(
  "w-full rounded-lg border border-gray-800 bg-gray-950 px-4 text-sm text-gray-50",
  "placeholder:text-gray-500 transition-colors duration-200 hover:border-gray-700",
  "focus-visible:border-brand-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/30",
  "disabled:opacity-50",
);

export const controlErrorClasses = "border-red-500/50 hover:border-red-500/50";

interface FieldProps {
  id: string;
  label: string;
  hint?: string;
  /** Validation message. Replaces the hint and is announced to screen readers. */
  error?: string;
  children: ReactNode;
}

/** Label + control + optional hint or error, with consistent 8px rhythm. */
export function Field({ id, label, hint, error, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium text-gray-300">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-xs text-red-300">
          {error}
        </p>
      ) : (
        hint && <p className="text-xs text-gray-400">{hint}</p>
      )}
    </div>
  );
}

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  id: string;
  label: string;
  hint?: string;
  error?: string;
};

export function Input({ id, label, hint, error, className, ...rest }: InputProps) {
  return (
    <Field id={id} label={label} hint={hint} error={error}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        {...rest}
        className={cn(controlClasses, "h-10", error && controlErrorClasses, className)}
      />
    </Field>
  );
}

/** Compact control for toolbars (no label wrapper). */
export function SearchInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...rest} className={cn(controlClasses, "h-10", className)} />;
}

export function Select({ className, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...rest} className={cn(controlClasses, "h-10", className)} />;
}

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  id: string;
  label: string;
  hint?: string;
  error?: string;
};

export function Textarea({ id, label, hint, error, className, ...rest }: TextareaProps) {
  return (
    <Field id={id} label={label} hint={hint} error={error}>
      <textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        {...rest}
        className={cn(controlClasses, "py-2", error && controlErrorClasses, className)}
      />
    </Field>
  );
}
