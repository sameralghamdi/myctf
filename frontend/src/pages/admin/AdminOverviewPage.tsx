import { useState } from "react";
import { PageContainer } from "../../components/layout/PageContainer";
import { PageHeader } from "../../components/layout/PageHeader";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Select } from "../../components/ui/Field";
import { ErrorState, PageLoader } from "../../components/ui/PageLoader";
import { SectionLabel } from "../../components/ui/SectionLabel";
import { StatCard } from "../../components/ui/StatCard";
import { Table, Td, Th, Tr } from "../../components/ui/Table";
import { Tabs } from "../../components/ui/Tabs";
import { useApi } from "../../hooks/useApi";
import { api, toMessage } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import type {
  AdminOverview,
  Analytics,
  AuditEntry,
  RunningLab,
} from "../../types/api";
import type { UserRole } from "../../types/navigation";

type TabId = "challenges" | "users" | "labs" | "audit" | "analytics";

const tabs: { id: TabId; label: string }[] = [
  { id: "challenges", label: "Challenges" },
  { id: "users", label: "Users" },
  { id: "labs", label: "Labs monitor" },
  { id: "audit", label: "Audit log" },
  { id: "analytics", label: "Analytics" },
];

const ROLES: UserRole[] = ["student", "instructor", "administrator"];

export function AdminOverviewPage() {
  const overview = useApi<AdminOverview>("/admin/api/overview");
  const [tab, setTab] = useState<TabId>("challenges");

  return (
    <PageContainer>
      <PageHeader title="Admin panel" description="Manage challenges, users and running labs." />

      {overview.loading && !overview.data ? (
        <PageLoader />
      ) : !overview.data ? (
        <ErrorState message={overview.error ?? "Could not load the admin panel."} onRetry={overview.reload} />
      ) : (
        <>
          <section aria-label="Platform stats" className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Users" value={overview.data.stats.users} />
            <StatCard label="Published" value={overview.data.stats.challenges} tone="brand" />
            <StatCard label="Solves" value={overview.data.stats.solves} tone="success" />
            <StatCard label="Running labs" value={overview.data.stats.running_labs} />
          </section>

          <div className="flex flex-col gap-6">
            <Tabs tabs={tabs} active={tab} onChange={setTab} />
            {tab === "challenges" && (
              <Card className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-col gap-2">
                  <p className="font-medium text-gray-50">Challenge management</p>
                  <p className="text-sm text-gray-400">
                    Create, publish and validate challenges from manifests.
                  </p>
                </div>
                <Button href="/admin/challenges">Open manager</Button>
              </Card>
            )}
            {tab === "users" && <UsersTab users={overview.data.users} />}
            {tab === "labs" && <LabsTab />}
            {tab === "audit" && <AuditTab />}
            {tab === "analytics" && <AnalyticsTab />}
          </div>
        </>
      )}
    </PageContainer>
  );
}

function UsersTab({ users }: { users: AdminOverview["users"] }) {
  const [roles, setRoles] = useState<Record<number, UserRole>>(
    () => Object.fromEntries(users.map((user) => [user.id, user.role])),
  );
  const [notice, setNotice] = useState<{ tone: "success" | "danger"; text: string } | null>(null);

  async function changeRole(id: number, role: UserRole) {
    try {
      await api(`/admin/api/users/${id}/role`, { method: "POST", body: { role } });
      setRoles((previous) => ({ ...previous, [id]: role }));
      setNotice({ tone: "success", text: "Role updated." });
    } catch (caught) {
      setNotice({ tone: "danger", text: toMessage(caught) });
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
      <Card className="overflow-hidden p-0">
        <Table>
          <thead>
            <tr>
              <Th>User</Th>
              <Th>Last login</Th>
              <Th>Role</Th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <Tr key={user.id}>
                <Td>
                  <span className="font-medium text-gray-50">{user.username}</span>
                  <span className="block text-xs text-gray-400">{user.email}</span>
                </Td>
                <Td className="text-gray-400">{formatDateTime(user.last_login_at)}</Td>
                <Td>
                  <Select
                    aria-label={`Role for ${user.username}`}
                    value={roles[user.id]}
                    onChange={(event) => void changeRole(user.id, event.target.value as UserRole)}
                    className="w-40"
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </Select>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}

function LabsTab() {
  const { data, error, loading, reload } = useApi<RunningLab[]>("/admin/api/labs/running");
  const [notice, setNotice] = useState<string | null>(null);

  async function run(path: string, message: (response: { cleaned?: number }) => string) {
    try {
      const response = await api<{ cleaned?: number }>(path, { method: "POST" });
      setNotice(message(response));
      reload();
    } catch (caught) {
      setNotice(toMessage(caught));
    }
  }

  if (loading && !data) return <PageLoader />;
  if (!data) return <ErrorState message={error ?? "Could not load labs."} onRetry={reload} />;

  return (
    <div className="flex flex-col gap-4">
      {notice && <Alert>{notice}</Alert>}
      <Card className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-4">
          <SectionLabel>Running labs</SectionLabel>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void run("/admin/api/labs/sweep", (r) => `Cleaned ${r.cleaned ?? 0} labs.`)}
          >
            Sweep expired
          </Button>
        </div>
        {data.length === 0 ? (
          <p className="text-sm text-gray-400">No running labs.</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>User</Th>
                <Th>Challenge</Th>
                <Th>Expires</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {data.map((lab) => (
                <Tr key={lab.instance_id}>
                  <Td>{lab.user}</Td>
                  <Td>{lab.challenge}</Td>
                  <Td className="text-gray-400">{formatDateTime(lab.expires_at)}</Td>
                  <Td className="text-right">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() =>
                        void run(`/admin/api/labs/${lab.instance_id}/restart`, () => "Lab restarted.")
                      }
                    >
                      Restart
                    </Button>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}

function AuditTab() {
  const { data, error, loading, reload } = useApi<AuditEntry[]>("/admin/api/audit");
  if (loading && !data) return <PageLoader />;
  if (!data) return <ErrorState message={error ?? "Could not load the audit log."} onRetry={reload} />;

  return (
    <Card className="overflow-hidden p-0">
      <Table>
        <thead>
          <tr>
            <Th>When</Th>
            <Th>User</Th>
            <Th>Action</Th>
            <Th>Detail</Th>
          </tr>
        </thead>
        <tbody>
          {data.map((entry, index) => (
            <Tr key={`${entry.at}-${index}`}>
              <Td className="whitespace-nowrap text-gray-400">{formatDateTime(entry.at)}</Td>
              <Td>{entry.user ?? "—"}</Td>
              <Td>
                <Badge>{entry.action}</Badge>
              </Td>
              <Td className="text-gray-400">{entry.detail}</Td>
            </Tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function AnalyticsTab() {
  const { data, error, loading, reload } = useApi<Analytics>("/admin/api/analytics");
  if (loading && !data) return <PageLoader />;
  if (!data) return <ErrorState message={error ?? "Could not load analytics."} onRetry={reload} />;

  const rows = (items: { label: string; value: number }[]) =>
    items.length === 0 ? (
      <p className="text-sm text-gray-400">No data.</p>
    ) : (
      <ul className="flex flex-col">
        {items.map((item) => (
          <li
            key={item.label}
            className="flex h-10 items-center justify-between gap-4 border-b border-gray-800 text-sm"
          >
            <span className="text-gray-300">{item.label}</span>
            <span className="font-mono text-gray-50">{item.value}</span>
          </li>
        ))}
      </ul>
    );

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="flex flex-col gap-4">
        <SectionLabel>Solves by category</SectionLabel>
        {rows(data.solves_by_category.map((r) => ({ label: r.category, value: r.solves })))}
      </Card>
      <Card className="flex flex-col gap-4">
        <SectionLabel>Least-solved challenges</SectionLabel>
        {rows(data.least_solved.map((r) => ({ label: r.name, value: r.solves })))}
      </Card>
    </div>
  );
}
