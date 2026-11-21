import { useEffect, useRef, type ClipboardEvent, type KeyboardEvent } from "react";
import { cn, focusRing } from "../../lib/cn";

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  /** Called once all digits are filled (typed or pasted). */
  onComplete?: (value: string) => void;
  length?: number;
  disabled?: boolean;
  invalid?: boolean;
  label?: string;
}

/** One box per digit: auto-advance, backspace goes back, and pasting a full code fills every box. */
export function OtpInput({ value, onChange, onComplete, length = 6, disabled, invalid, label = "Verification code" }: OtpInputProps) {
  const boxes = useRef<(HTMLInputElement | null)[]>([]);
  const digits = Array.from({ length }, (_, i) => value[i] ?? "");

  useEffect(() => {
    boxes.current[0]?.focus();
  }, []);

  function setAt(index: number, digit: string) {
    const next = (value.slice(0, index) + digit + value.slice(index + 1)).replace(/\D/g, "").slice(0, length);
    onChange(next);
    if (next.length === length) onComplete?.(next);
  }

  function onKey(index: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace") {
      event.preventDefault();
      if (digits[index]) setAt(index, "");
      else if (index > 0) {
        onChange(value.slice(0, index - 1) + value.slice(index));
        boxes.current[index - 1]?.focus();
      }
    } else if (event.key === "ArrowLeft" && index > 0) {
      boxes.current[index - 1]?.focus();
    } else if (event.key === "ArrowRight" && index < length - 1) {
      boxes.current[index + 1]?.focus();
    }
  }

  function onPaste(event: ClipboardEvent<HTMLInputElement>) {
    const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    if (!pasted) return;
    event.preventDefault();
    onChange(pasted);
    boxes.current[Math.min(pasted.length, length - 1)]?.focus();
    if (pasted.length === length) onComplete?.(pasted);
  }

  return (
    <div role="group" aria-label={label} className="flex justify-between gap-2">
      {digits.map((digit, index) => (
        <input
          key={index}
          ref={(el) => {
            boxes.current[index] = el;
          }}
          value={digit}
          disabled={disabled}
          inputMode="numeric"
          autoComplete={index === 0 ? "one-time-code" : "off"}
          aria-label={`Digit ${index + 1}`}
          aria-invalid={invalid || undefined}
          maxLength={length}
          onPaste={onPaste}
          onKeyDown={(event) => onKey(index, event)}
          onFocus={(event) => event.currentTarget.select()}
          onChange={(event) => {
            const typed = event.target.value.replace(/\D/g, "");
            if (typed.length > 1) {
              // iOS/Android "fill from SMS/email" types the whole code into one box.
              onChange(typed.slice(0, length));
              if (typed.length >= length) onComplete?.(typed.slice(0, length));
              return;
            }
            if (!typed) return;
            setAt(index, typed);
            if (index < length - 1) boxes.current[index + 1]?.focus();
          }}
          className={cn(
            "h-14 w-full min-w-0 rounded-lg border bg-gray-950 text-center font-mono text-2xl font-semibold text-gray-50 transition-all duration-150",
            "focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30",
            digit ? "border-gray-600" : "border-gray-800",
            invalid && "border-red-500/60",
            disabled && "opacity-50",
            focusRing,
          )}
        />
      ))}
    </div>
  );
}
