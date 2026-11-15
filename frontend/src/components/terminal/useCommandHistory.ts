import { useCallback, useRef, useState } from "react";

const MAX_ENTRIES = 200;

/**
 * Shell-style command history.
 *
 * `previous`/`next` walk through earlier commands (Up/Down arrows). The text
 * being typed before the first Up is kept as a draft and restored when the
 * user comes back down past the newest entry, exactly like bash.
 */
export function useCommandHistory() {
  const [entries, setEntries] = useState<string[]>([]);
  // Position while browsing; entries.length means "not browsing" (the draft).
  const position = useRef(0);
  const draft = useRef("");

  const push = useCallback((command: string) => {
    setEntries((current) => {
      // Like bash's ignoredups: don't store the same command twice in a row.
      const next =
        current[current.length - 1] === command ? current : [...current, command];
      const trimmed = next.slice(-MAX_ENTRIES);
      position.current = trimmed.length;
      return trimmed;
    });
    draft.current = "";
  }, []);

  /** Older command, or null when already at the oldest. */
  const previous = useCallback(
    (currentInput: string): string | null => {
      if (position.current === 0 || entries.length === 0) return null;
      if (position.current >= entries.length) draft.current = currentInput;
      position.current = Math.min(position.current, entries.length) - 1;
      return entries[position.current];
    },
    [entries],
  );

  /** Newer command, the saved draft after the newest, or null if not browsing. */
  const next = useCallback((): string | null => {
    if (position.current >= entries.length) return null;
    position.current += 1;
    return position.current === entries.length ? draft.current : entries[position.current];
  }, [entries]);

  /** Stop browsing (called when the user edits or cancels the line). */
  const reset = useCallback(() => {
    position.current = entries.length;
  }, [entries.length]);

  return { entries, push, previous, next, reset };
}
