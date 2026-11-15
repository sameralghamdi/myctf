import { Alert } from "./Alert";
import { Button } from "./Button";

export function Spinner() {
  return (
    <span
      role="status"
      aria-label="Loading"
      className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-700 border-t-brand-400"
    />
  );
}

export function PageLoader() {
  return (
    <div className="flex min-h-64 items-center justify-center">
      <Spinner />
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-4">
      <Alert tone="danger">{message}</Alert>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
