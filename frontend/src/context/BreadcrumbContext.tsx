import { createContext, useContext, useEffect } from "react";
import type { Breadcrumb } from "../types/navigation";

type SetCrumbs = (crumbs: Breadcrumb[] | null) => void;

export const BreadcrumbContext = createContext<SetCrumbs>(() => undefined);

/** Lets a page replace the default top-bar breadcrumbs (e.g. Challenges / <name>). */
export function useBreadcrumbs(crumbs: Breadcrumb[] | null): void {
  const setCrumbs = useContext(BreadcrumbContext);
  const key = JSON.stringify(crumbs);
  useEffect(() => {
    setCrumbs(JSON.parse(key) as Breadcrumb[] | null);
    return () => setCrumbs(null);
  }, [key, setCrumbs]);
}
