import { useCallback } from "react";
import { useApi } from "../../hooks/useApi";
import { api } from "../../lib/api";
import type { ShellResult, ShellSession } from "../../types/api";
import { ErrorState, Spinner } from "../ui/PageLoader";
import { TerminalEmulator } from "./TerminalEmulator";

interface LabTerminalProps {
  /** The running lab's base URL, e.g. `/labs/<instance-id>/`. */
  labUrl: string;
}

/**
 * Connects <TerminalEmulator> to a running shell lab. Every command is sent to
 * the server and interpreted there against the player's private, simulated
 * machine, so the flag never exists in the browser until the player earns it.
 */
export function LabTerminal({ labUrl }: LabTerminalProps) {
  const endpoint = `${labUrl.replace(/\/+$/, "")}/shell`;
  const { data: session, error, loading, reload } = useApi<ShellSession>(endpoint);

  const execute = useCallback(
    (command: string) => api<ShellResult>(endpoint, { method: "POST", body: { command } }),
    [endpoint],
  );

  if (loading && !session) {
    return (
      <div className="flex min-h-96 flex-1 items-center justify-center rounded-xl border border-gray-800 bg-black">
        <Spinner />
      </div>
    );
  }
  if (!session) {
    return <ErrorState message={error ?? "Could not connect to the terminal."} onRetry={reload} />;
  }

  return (
    <TerminalEmulator
      identity={{ user: session.user, host: session.host, home: session.home }}
      initialCwd={session.cwd}
      banner={session.motd}
      execute={execute}
      className="flex-1"
    />
  );
}
