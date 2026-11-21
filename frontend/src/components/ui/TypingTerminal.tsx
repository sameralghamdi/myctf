import { useEffect, useState } from "react";
import { useReducedMotion } from "../../hooks/useReducedMotion";

export interface TerminalScriptLine {
  kind: "cmd" | "out" | "ok";
  text: string;
}

/** A decorative terminal that types out a scripted session, then loops. */
export function TypingTerminal({ script, title = "ctf@lab: ~", compact = false }: { script: TerminalScriptLine[]; title?: string; compact?: boolean }) {
  const reduced = useReducedMotion();
  const [line, setLine] = useState(reduced ? script.length : 0);
  const [chars, setChars] = useState(0);

  useEffect(() => {
    if (reduced) return;
    if (line >= script.length) {
      const restart = window.setTimeout(() => {
        setLine(0);
        setChars(0);
      }, 3500);
      return () => window.clearTimeout(restart);
    }
    const current = script[line];
    if (current.kind === "cmd" && chars < current.text.length) {
      const id = window.setTimeout(() => setChars((c) => c + 1), 35 + Math.random() * 45);
      return () => window.clearTimeout(id);
    }
    const id = window.setTimeout(() => {
      setLine((l) => l + 1);
      setChars(0);
    }, current.kind === "cmd" ? 350 : 220);
    return () => window.clearTimeout(id);
  }, [line, chars, script, reduced]);

  return (
    <div aria-hidden="true" className="overflow-hidden rounded-xl border border-gray-800 bg-black/80 shadow-2xl shadow-black/60 backdrop-blur">
      <div className="flex h-8 items-center gap-2 border-b border-gray-800 bg-gray-900/80 px-4">
        <span className="h-2 w-2 rounded-full bg-red-500/80" />
        <span className="h-2 w-2 rounded-full bg-yellow-500/80" />
        <span className="h-2 w-2 rounded-full bg-green-500/80" />
        <span className="flex-1 text-center font-mono text-xs text-gray-400">{title}</span>
      </div>
      <div className={`flex flex-col gap-1 p-4 font-mono text-xs leading-6 sm:text-sm ${compact ? "min-h-32" : "min-h-64"}`}>
        {script.slice(0, line + 1).map((entry, index) => {
          const typing = index === line && entry.kind === "cmd";
          const text = typing ? entry.text.slice(0, chars) : entry.text;
          if (index === line && entry.kind !== "cmd") return null;
          return (
            <div key={index} className={entry.kind === "ok" ? "text-green-400" : entry.kind === "out" ? "text-gray-400" : "text-gray-50"}>
              {entry.kind === "cmd" && <span className="text-green-400">ctf@lab</span>}
              {entry.kind === "cmd" && <span className="text-gray-400">:~$ </span>}
              {text}
              {typing && <span className="ml-px inline-block h-4 w-2 translate-y-1 animate-blink bg-gray-200" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
