import { Compass, Search } from "lucide-react";
import { PageContainer } from "../components/layout/PageContainer";
import { Button } from "../components/ui/Button";

export function NotFoundPage() {
  return (
    <PageContainer>
      <div className="relative flex flex-col items-center gap-6 overflow-hidden rounded-2xl border border-gray-800 bg-gray-900 px-6 py-16 text-center">
        <div aria-hidden="true" className="bg-grid absolute inset-0 [mask-image:radial-gradient(circle,black,transparent_70%)]" />
        <span className="relative grid h-16 w-16 animate-float place-items-center rounded-2xl bg-brand-500/10 text-brand-400">
          <Compass aria-hidden="true" className="h-8 w-8" />
        </span>
        <p className="relative font-mono text-6xl font-bold tracking-tight text-gradient">404</p>
        <div className="relative flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-gray-50">Nothing to exploit here</h1>
          <p className="max-w-md text-sm text-gray-400">
            This page doesn't exist or was moved. Try the search (press <span className="font-mono text-gray-200">/</span>) or head back.
          </p>
        </div>
        <div className="relative flex flex-wrap justify-center gap-2">
          <Button href="/dashboard">Back to dashboard</Button>
          <Button href="/challenges" variant="secondary">
            <Search aria-hidden="true" className="h-4 w-4" />
            Browse challenges
          </Button>
        </div>
      </div>
    </PageContainer>
  );
}
