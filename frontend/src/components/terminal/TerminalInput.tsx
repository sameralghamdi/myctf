import type { KeyboardEvent, RefObject } from "react";
import { cn } from "../../lib/cn";

interface TerminalInputProps {
  inputRef: RefObject<HTMLInputElement>;
  value: string;
  /** Cursor position inside `value` (0 = before the first character). */
  caret: number;
  focused: boolean;
  disabled: boolean;
  onChange: (value: string, caret: number) => void;
  onCaretMove: (caret: number) => void;
  onKeyDown: (event: KeyboardEvent<HTMLInputElement>) => void;
  onFocusChange: (focused: boolean) => void;
}

/**
 * The editable command line.
 *
 * A real <input> sits invisibly on top so typing, selection, mobile keyboards
 * and screen readers all work natively. What you see is drawn underneath: the
 * text plus a block cursor, which a native input can't show.
 */
export function TerminalInput({
  inputRef,
  value,
  caret,
  focused,
  disabled,
  onChange,
  onCaretMove,
  onKeyDown,
  onFocusChange,
}: TerminalInputProps) {
  const position = Math.min(caret, value.length);
  const under = value.charAt(position);

  return (
    <span className="relative min-w-0 flex-1 whitespace-pre-wrap break-all text-gray-50">
      {value.slice(0, position)}
      <span
        // Re-keyed on every edit so the blink restarts and the cursor stays solid while typing.
        key={`${value}:${position}`}
        aria-hidden="true"
        className={cn(
          focused
            ? "animate-blink bg-gray-200 text-black motion-reduce:animate-none"
            : "ring-1 ring-inset ring-gray-500",
        )}
      >
        {under || " "}
      </span>
      {value.slice(position + 1)}
      <input
        ref={inputRef}
        value={value}
        readOnly={disabled}
        aria-label="Terminal command input"
        autoCapitalize="none"
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
        className="absolute inset-0 h-full w-full cursor-text opacity-0"
        onChange={(event) =>
          onChange(event.target.value, event.target.selectionStart ?? event.target.value.length)
        }
        onSelect={(event) =>
          onCaretMove(event.currentTarget.selectionStart ?? event.currentTarget.value.length)
        }
        onKeyDown={onKeyDown}
        onFocus={() => onFocusChange(true)}
        onBlur={() => onFocusChange(false)}
      />
    </span>
  );
}
