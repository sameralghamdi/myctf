import { AdminCTFForm } from "../../components/admin/AdminCTFForm";
import { PageContainer } from "../../components/layout/PageContainer";
import { PageHeader } from "../../components/layout/PageHeader";
import { Button } from "../../components/ui/Button";
import { useBreadcrumbs } from "../../context/BreadcrumbContext";

export function AdminChallengeNewPage() {
  useBreadcrumbs([
    { label: "MyCTF", href: "/dashboard" },
    { label: "Admin", href: "/admin" },
    { label: "Manage challenges", href: "/admin/challenges" },
    { label: "New challenge" },
  ]);

  return (
    <PageContainer>
      <PageHeader
        title="New challenge"
        description="Create a challenge in five short steps. You can save it as a draft and publish it later."
        actions={
          <Button variant="ghost" href="/admin/challenges">
            Cancel
          </Button>
        }
      />
      <AdminCTFForm />
    </PageContainer>
  );
}
