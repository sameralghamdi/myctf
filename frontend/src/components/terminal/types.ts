/** Who and where the prompt says you are: `user@host:~/path$`. */
export interface TerminalIdentity {
  user: string;
  host: string;
  /** Home directory; shown as `~` in the prompt. */
  home: string;
}

/** What running one command produced. Either stream may be empty. */
export interface CommandResult {
  stdout: string;
  stderr: string;
  /** Working directory after the command (changes after `cd`). */
  cwd: string;
}

/**
 * Runs a command somewhere (the lab API in production, a stub in tests) and
 * resolves with its output. The terminal itself never interprets commands, apart
 * from the purely local `clear`, `history` and `exit`.
 */
export type ExecuteCommand = (command: string) => Promise<CommandResult>;

export type TerminalLineKind = "input" | "stdout" | "stderr" | "system";

export interface TerminalLineData {
  id: number;
  kind: TerminalLineKind;
  text: string;
  /** For "input" lines: the directory the command was typed in. */
  cwd?: string;
}
