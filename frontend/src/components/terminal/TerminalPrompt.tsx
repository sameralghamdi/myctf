import type { TerminalIdentity } from "./types";

interface TerminalPromptProps {
  identity: TerminalIdentity;
  cwd: string;
}

/** `/home/guest/docs` -> `~/docs` */
export function displayPath(cwd: string, home: string): string {
  if (cwd === home) return "~";
  return cwd.startsWith(`${home}/`) ? `~${cwd.slice(home.length)}` : cwd;
}

/** The classic coloured prefix: green user@host, blue path, then `$`. */
export function TerminalPrompt({ identity, cwd }: TerminalPromptProps) {
  return (
    <span className="shrink-0 whitespace-pre">
      <span className="font-semibold text-green-400">
        {identity.user}@{identity.host}
      </span>
      <span className="text-gray-50">:</span>
      <span className="font-semibold text-blue-400">{displayPath(cwd, identity.home)}</span>
      <span className="text-gray-50">$ </span>
    </span>
  );
}
