import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface AnimatedNumberProps {
  value: number;
  /** Milliseconds for the count. */
  duration?: number;
  format?: (value: number) => string;
  className?: string;
}

const defaultFormat = (value: number) => Math.round(value).toLocaleString("en");

/** Counts from the previous value to the new one (ease-out). Static under reduced motion. */
export function AnimatedNumber({ value, duration = 900, format = defaultFormat, className }: AnimatedNumberProps) {
  const reduced = useReducedMotion();
  const [shown, setShown] = useState(reduced ? value : 0);
  const from = useRef(reduced ? value : 0);

  useEffect(() => {
    if (reduced) {
      setShown(value);
      from.current = value;
      return;
    }
    const start = performance.now();
    const origin = from.current;
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(origin + (value - origin) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
      else from.current = value;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration, reduced]);

  return (
    <span className={className} aria-label={format(value)}>
      <span aria-hidden="true">{format(shown)}</span>
    </span>
  );
}
