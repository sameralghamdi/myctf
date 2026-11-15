import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { PageContainer } from "./PageContainer";
import { PageHeader } from "./PageHeader";
import { Button } from "../ui/Button";

/** Sends signed-out visitors to /login and brings them back afterwards. */
export function RequireAuth() {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return <Outlet />;
}

export function RequireAdmin() {
  const { user } = useAuth();
  if (user?.role !== "administrator") {
    return (
      <PageContainer>
        <PageHeader
          title="Administrators only"
          description="Your account doesn't have access to this area."
          actions={<Button href="/dashboard">Back to dashboard</Button>}
        />
      </PageContainer>
    );
  }
  return <Outlet />;
}
