import { useCallback, useEffect, useState } from "react";
import { api, toMessage } from "../lib/api";

interface State<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

/** GET `path` and track loading/error. Pass null to skip. `reload` refetches. */
export function useApi<T>(path: string | null) {
  const [state, setState] = useState<State<T>>({ data: null, error: null, loading: path !== null });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (path === null) return;
    const controller = new AbortController();
    setState((previous) => ({ ...previous, loading: true, error: null }));
    api<T>(path, { signal: controller.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({ data: null, error: toMessage(error), loading: false });
      });
    return () => controller.abort();
  }, [path, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { ...state, reload };
}
