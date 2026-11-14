import { PageContainer } from "../components/layout/PageContainer";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";

export function NotFoundPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Page not found"
        description="The page you're looking for doesn't exist or was moved."
        actions={<Button href="/dashboard">Back to dashboard</Button>}
      />
    </PageContainer>
  );
}
