import { CheckCircle2, Info, TriangleAlert, X, XCircle } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { cn, focusRing } from "../../lib/cn";

type ToastTone = "success" | "info" | "warning" | "danger";

interface ToastInput {
  tone?: ToastTone;
  title: string;
  description?: string;
  /** Milliseconds before it hides itself. */
  duration?: number;
}

interface ToastItem extends Required<Omit<ToastInput, "description">> {
  id: number;
  description?: string;
}

const ToastContext = createContext<((toast: ToastInput) => void) | null>(null);

const tones: Record<ToastTone, { icon: typeof Info; classes: string }> = {
  success: { icon: CheckCircle2, classes: "text-green-400" },
  info: { icon: Info, classes: "text-gray-300" },
  warning: { icon: TriangleAlert, classes: "text-yellow-400" },
  danger: { icon: XCircle, classes: "text-red-400" },
};

/** Small, stacked notifications in the bottom-right corner. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const push = useCallback(
    ({ tone = "info", title, description, duration = 4000 }: ToastInput) => {
      const id = nextId.current++;
      setItems((current) => [...current.slice(-3), { id, tone, title, description, duration }]);
      window.setTimeout(() => dismiss(id), duration);
    },
    [dismiss],
  );

  const value = useMemo(() => push, [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2"
      >
        {items.map((item) => {
          const { icon: Icon, classes } = tones[item.tone];
          return (
            <div
              key={item.id}
              role={item.tone === "danger" ? "alert" : "status"}
              className="pointer-events-auto flex animate-toast-in items-start gap-4 rounded-xl border border-gray-800 bg-gray-900/95 p-4 shadow-lg shadow-black/40 backdrop-blur"
            >
              <Icon aria-hidden="true" className={cn("mt-1 h-4 w-4 shrink-0", classes)} />
              <div className="flex min-w-0 flex-1 flex-col">
                <p className="text-sm font-medium text-gray-50">{item.title}</p>
                {item.description && <p className="text-xs text-gray-400">{item.description}</p>}
              </div>
              <button
                type="button"
                aria-label="Dismiss"
                onClick={() => dismiss(item.id)}
                className={cn("rounded text-gray-400 transition-colors hover:text-gray-50", focusRing)}
              >
                <X aria-hidden="true" className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside <ToastProvider>");
  return context;
}
