import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { cn } from "../../lib/cn";
import { TerminalInput } from "./TerminalInput";
import { TerminalLine } from "./TerminalLine";
import { displayPath, TerminalPrompt } from "./TerminalPrompt";
import type {
  ExecuteCommand,
  TerminalIdentity,
  TerminalLineData,
  TerminalLineKind,
} from "./types";
import { useCommandHistory } from "./useCommandHistory";

const MAX_SCROLLBACK = 500;

interface TerminalEmulatorProps {
  identity: TerminalIdentity;
  /** Directory the session starts in. */
  initialCwd: string;
  /** Runs a command and resolves with its output. */
  execute: ExecuteCommand;
  /** Shown once at the top, like a login message. */
  banner?: string;
  /** Focus the command line on mount. */
  autoFocus?: boolean;
  className?: string;
}

/**
 * A terminal window: coloured prompt, block cursor, Up/Down history, scrollback
 * that follows new output, and separate colours for output and errors.
 *
 * Keys: Enter runs, Up/Down recall history, Ctrl+L clears, Ctrl+C cancels the line.
 * It is display + input only. Commands are executed by the `execute` prop.
 */
export function TerminalEmulator({
  identity,
  initialCwd,
  execute,
  banner,
  autoFocus = true,
  className,
}: TerminalEmulatorProps) {
  const [lines, setLines] = useState<TerminalLineData[]>(() =>
    banner ? [{ id: 0, kind: "system", text: banner }] : [],
  );
  const [cwd, setCwd] = useState(initialCwd);
  const [input, setInput] = useState("");
  const [caret, setCaret] = useState(0);
  const [busy, setBusy] = useState(false);
  const [focused, setFocused] = useState(false);

  const history = useCommandHistory();
  const nextId = useRef(1);
  const mounted = useRef(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    mounted.current = true;
    if (autoFocus) inputRef.current?.focus({ preventScroll: true });
    return () => {
      mounted.current = false;
    };
  }, [autoFocus]);

  // Follow the output: jump to the newest line after every change.
  useEffect(() => {
    const element = scrollRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [lines, busy, input]);

  const print = useCallback((kind: TerminalLineKind, text: string, lineCwd?: string) => {
    const id = nextId.current;
    nextId.current += 1;
    setLines((current) =>
      [...current, { id, kind, text, cwd: lineCwd }].slice(-MAX_SCROLLBACK),
    );
  }, []);

  const setLine = useCallback((value: string, position = value.length) => {
    setInput(value);
    setCaret(position);
  }, []);

  async function run(raw: string) {
    const command = raw.trim();
    print("input", raw, cwd);
    setLine("");
    if (!command) return;
    history.push(command);

    // Purely local commands: they only affect this window.
    if (command === "clear") {
      setLines([]);
      return;
    }
    if (command === "history") {
      const { entries } = history;
      const all = entries[entries.length - 1] === command ? entries : [...entries, command];
      print("stdout", all.map((entry, index) => `${String(index + 1).padStart(4)}  ${entry}`).join("\n"));
      return;
    }
    if (command === "exit" || command === "logout") {
      print("system", "This terminal belongs to the lab. Use Stop above to end the session.");
      return;
    }

    setBusy(true);
    try {
      const result = await execute(command);
      if (!mounted.current) return;
      if (result.stdout) print("stdout", result.stdout);
      if (result.stderr) print("stderr", result.stderr);
      if (result.cwd) setCwd(result.cwd);
    } catch (caught) {
      if (!mounted.current) return;
      const reason = caught instanceof Error ? caught.message : "request failed";
      print("stderr", `terminal: could not run command: ${reason}`);
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.ctrlKey && event.key.toLowerCase() === "l") {
      event.preventDefault();
      setLines([]);
      return;
    }
    if (busy) return;

    if (event.ctrlKey && event.key.toLowerCase() === "c") {
      // Keep the browser's copy shortcut when text is selected.
      if (window.getSelection()?.toString()) return;
      event.preventDefault();
      print("input", `${input}^C`, cwd);
      setLine("");
      history.reset();
      return;
    }

    switch (event.key) {
      case "Enter":
        event.preventDefault();
        void run(input);
        break;
      case "ArrowUp": {
        event.preventDefault();
        const older = history.previous(input);
        if (older !== null) setLine(older);
        break;
      }
      case "ArrowDown": {
        event.preventDefault();
        const newer = history.next();
        if (newer !== null) setLine(newer);
        break;
      }
      default:
        break;
    }
  }

  /** Clicking the window focuses the prompt, unless the user is selecting text to copy. */
  function focusInput() {
    if (!window.getSelection()?.toString()) inputRef.current?.focus({ preventScroll: true });
  }

  return (
    <div
      className={cn(
        "flex min-h-96 max-h-[85vh] flex-col overflow-hidden rounded-xl border border-gray-800 bg-black shadow-md",
        "transition-colors duration-200",
        focused && "border-gray-700",
        className,
      )}
    >
      <div className="flex h-8 shrink-0 items-center gap-4 border-b border-gray-800 bg-gray-900 px-4">
        <span aria-hidden="true" className="flex gap-2">
          <span className="h-2 w-2 rounded-full bg-gray-700" />
          <span className="h-2 w-2 rounded-full bg-gray-700" />
          <span className="h-2 w-2 rounded-full bg-gray-700" />
        </span>
        <span className="min-w-0 flex-1 truncate text-center font-mono text-xs text-gray-400">
          {identity.user}@{identity.host}: {displayPath(cwd, identity.home)}
        </span>
        <span className="font-mono text-xs text-gray-500">bash</span>
      </div>

      <div
        ref={scrollRef}
        onMouseUp={focusInput}
        className="min-h-0 flex-1 cursor-text overflow-y-auto p-4 font-mono text-sm leading-6"
      >
        <div role="log" aria-live="polite" aria-label="Terminal output">
          {lines.map((line) => (
            <TerminalLine key={line.id} line={line} identity={identity} />
          ))}
        </div>
        <div className="flex">
          {/* While a command runs there is no prompt, only the cursor, as in a real shell. */}
          {!busy && <TerminalPrompt identity={identity} cwd={cwd} />}
          <TerminalInput
            inputRef={inputRef}
            value={busy ? "" : input}
            caret={caret}
            focused={focused}
            disabled={busy}
            onChange={(value, position) => {
              setLine(value, position);
              history.reset();
            }}
            onCaretMove={setCaret}
            onKeyDown={handleKeyDown}
            onFocusChange={setFocused}
          />
        </div>
      </div>
    </div>
  );
}
