import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, setUnauthorizedHandler } from "../lib/api";
import type { SessionResponse, SessionUser } from "../types/api";

interface AuthContextValue {
  /** "loading" until the first /api/session answer arrives. */
  status: "loading" | "ready";
  user: SessionUser | null;
  score: number;
  rank: number | null;
  signIn: (identifier: string, password: string, otp?: string) => Promise<void>;
  signUp: (username: string, email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Re-read score/rank, e.g. after solving a challenge. */
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [user, setUser] = useState<SessionUser | null>(null);
  const [score, setScore] = useState(0);
  const [rank, setRank] = useState<number | null>(null);

  const apply = useCallback((session: SessionResponse) => {
    setUser(session.user);
    setScore(session.score ?? 0);
    setRank(session.rank ?? null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      apply(await api<SessionResponse>("/api/session"));
    } catch {
      apply({ user: null });
    } finally {
      setStatus("ready");
    }
  }, [apply]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    setUnauthorizedHandler(() => apply({ user: null }));
    return () => setUnauthorizedHandler(null);
  }, [apply]);

  const signIn = useCallback(
    async (identifier: string, password: string, otp?: string) => {
      await api("/api/auth/login", {
        method: "POST",
        body: { username: identifier, password, ...(otp ? { otp } : {}) },
      });
      await refresh();
    },
    [refresh],
  );

  const signUp = useCallback(
    async (username: string, email: string, password: string) => {
      await api("/api/auth/register", { method: "POST", body: { username, email, password } });
      await refresh();
    },
    [refresh],
  );

  const signOut = useCallback(async () => {
    try {
      await api("/api/auth/logout", { method: "POST" });
    } finally {
      apply({ user: null });
    }
  }, [apply]);

  const value = useMemo(
    () => ({ status, user, score, rank, signIn, signUp, signOut, refresh }),
    [status, user, score, rank, signIn, signUp, signOut, refresh],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
