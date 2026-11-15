import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { useApi } from "../hooks/useApi";
import { cn, focusRing } from "../lib/cn";
import type { PublicInfo } from "../types/api";

const sections = [
  { id: "start", label: "Getting started" },
  { id: "how", label: "How a challenge works" },
  { id: "flags", label: "Per-session flags" },
  { id: "labs", label: "Lab types" },
  { id: "safety", label: "Safety" },
] as const;

const heading = "scroll-mt-24 text-lg font-semibold text-gray-50";
const body = "text-sm text-gray-300";

export function DocsPage() {
  const { data } = useApi<PublicInfo>("/api/public");

  return (
    <PageContainer>
      <PageHeader title="Documentation" description="Everything you need to start capturing flags." />
      <div className="grid gap-8 lg:grid-cols-4">
        <nav aria-label="On this page" className="lg:sticky lg:top-24 lg:self-start">
          <p className="pb-2 text-xs font-medium uppercase tracking-wider text-gray-400">
            On this page
          </p>
          <ul className="flex flex-col">
            {sections.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  className={cn(
                    "flex h-8 items-center rounded-lg px-2 text-sm text-gray-400 transition-colors duration-200 hover:bg-gray-800 hover:text-gray-50",
                    focusRing,
                  )}
                >
                  {section.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <article className="flex max-w-3xl flex-col gap-8 lg:col-span-3">
          <section className="flex flex-col gap-4">
            <h2 id="start" className={heading}>
              Getting started
            </h2>
            <p className={body}>
              MyCTF teaches penetration testing through hands-on, isolated labs. The loop is{" "}
              <strong className="font-medium text-gray-50">
                Learn → Start Lab → Investigate → Exploit → Capture Flag → Understand → Improve.
              </strong>
            </p>
          </section>

          <section className="flex flex-col gap-4">
            <h2 id="how" className={heading}>
              How a challenge works
            </h2>
            <ol className={cn(body, "flex list-decimal flex-col gap-2 pl-6")}>
              <li>Open a challenge and read the objectives.</li>
              <li>Click Start lab to spin up your own isolated instance with a unique flag.</li>
              <li>Interact with the target in the right-hand pane, or open it in a new tab.</li>
              <li>
                Find and exploit the vulnerability to reveal the flag (format{" "}
                <code className="font-mono text-brand-400">MYCTF{"{...}"}</code>).
              </li>
              <li>Submit it on the left. Points are awarded once, and a debrief unlocks.</li>
            </ol>
          </section>

          <section className="flex flex-col gap-4">
            <h2 id="flags" className={heading}>
              Per-session flags
            </h2>
            <p className={body}>
              Each lab instance has its own flag tied to your account, so sharing a flag never
              completes someone else&apos;s challenge. Validation happens on the platform backend —
              exploiting a lab cannot shortcut scoring.
            </p>
          </section>

          <section className="flex flex-col gap-4">
            <h2 id="labs" className={heading}>
              Lab types available
            </h2>
            <div className="flex flex-wrap gap-2">
              {data?.live_kinds.map((kind) => <Badge key={kind}>{kind}</Badge>)}
            </div>
          </section>

          <section className="flex flex-col gap-4">
            <h2 id="safety" className={heading}>
              Safety
            </h2>
            <p className={body}>
              All vulnerable behaviour is confined to intentionally isolated training targets. Never
              point these techniques at systems you don&apos;t own or have explicit permission to
              test.
            </p>
          </section>
        </article>
      </div>
    </PageContainer>
  );
}
