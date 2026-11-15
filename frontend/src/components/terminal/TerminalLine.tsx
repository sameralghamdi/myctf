import { cn } from "../../lib/cn";
import { TerminalPrompt } from "./TerminalPrompt";
import type { TerminalIdentity, TerminalLineData, TerminalLineKind } from "./types";

const OUTPUT_COLORS: Record<Exclude<TerminalLineKind, "input">, string> = {
  stdout: "text-gray-300",
  stderr: "text-red-400",
  system: "text-gray-500",
};

interface TerminalLineProps {
  line: TerminalLineData;
  identity: TerminalIdentity;
}

/** One scrollback entry: an echoed command, or a block of output. */
export function TerminalLine({ line, identity }: TerminalLineProps) {
  if (line.kind === "input") {
    return (
      <div className="flex">
        <TerminalPrompt identity={identity} cwd={line.cwd ?? identity.home} />
        <span className="min-w-0 whitespace-pre-wrap break-all text-gray-50">{line.text}</span>
      </div>
    );
  }
  return (
    <div className={cn("whitespace-pre-wrap break-words", OUTPUT_COLORS[line.kind])}>
      {line.kind === "stderr" && <span className="sr-only">Error: </span>}
      {line.text}
    </div>
  );
}
