import { useEffect, useState } from "react";

/** True when the visitor asked the OS for less motion. */
export function useReducedMotion(): boolean {
  const query = "(prefers-reduced-motion: reduce)";
  const [reduced, setReduced] = useState(() =>
    typeof window !== "undefined" && window.matchMedia ? window.matchMedia(query).matches : false,
  );
  useEffect(() => {
    if (!window.matchMedia) return;
    const media = window.matchMedia(query);
    const onChange = () => setReduced(media.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);
  return reduced;
}
