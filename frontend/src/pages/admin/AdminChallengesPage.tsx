import { Plus } from "lucide-react";
import { useState } from "react";
import { PageContainer } from "../../components/layout/PageContainer";
import { PageHeader } from "../../components/layout/PageHeader";
import { Alert, type AlertTone } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { DifficultyBadge } from "../../components/ui/ChallengeBadges";
import { Textarea } from "../../components/ui/Field";
import { ErrorState, PageLoader } from "../../components/ui/PageLoader";
import { SectionLabel } from "../../components/ui/SectionLabel";
import { Table, Td, Th, Tr } from "../../components/ui/Table";
import { useBreadcrumbs } from "../../context/BreadcrumbContext";
import { useApi } from "../../hooks/useApi";
import { api, toMessage } from "../../lib/api";
import type { AdminChallenge } from "../../types/api";

const SAMPLE_MANIFEST = `{
  "slug": "demo-static",
  "name": "Demo Static Challenge",
  "category": "crypto",
  "difficulty": "very_easy",
  "lab_kind": "static",
  "flag": "MYCTF{replace_with_your_own_flag}",
  "description": "A simple static-flag demo.",
  "hints": [{"level": 1, "cost": 0, "body": "The flag is right there."}]
}`;

export function AdminChallengesPage() {
  useBreadcrumbs([
    { label: "MyCTF", href: "/dashboard" },
    { label: "Admin", href: "/admin" },
    { label: "Manage challenges" },
  ]);
  const { data, error, loading, reload } = useApi<AdminChallenge[]>("/admin/api/challenges");
  const [manifest, setManifest] = useState(SAMPLE_MANIFEST);
  const [result, setResult] = useState<{ tone: AlertTone; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function togglePublished(challenge: AdminChallenge) {
    try {
      await api(`/admin/api/challenges/${challenge.id}/publish`, {
        method: "POST",
        body: { published: !challenge.published },
      });
      reload();
    } catch (caught) {
      setResult({ tone: "danger", text: toMessage(caught) });
    }
  }

  async function submitManifest(publish: boolean) {
    let parsed: unknown;
    try {
      parsed = JSON.parse(manifest);
    } catch (caught) {
      setResult({ tone: "danger", text: `Invalid JSON: ${toMessage(caught)}` });
      return;
    }
    setBusy(true);
    try {
      if (publish) {
        const response = await api<{ challenge_id: number }>("/admin/api/challenges/publish", {
          method: "POST",
          body: parsed,
        });
        setResult({ tone: "success", text: `Published (id ${response.challenge_id}).` });
        reload();
      } else {
        const response = await api<{ normalized: unknown }>("/admin/api/challenges/validate", {
          method: "POST",
          body: parsed,
        });
        setResult({ tone: "success", text: `Valid: ${JSON.stringify(response.normalized)}` });
      }
    } catch (caught) {
      setResult({ tone: "danger", text: `Rejected: ${toMessage(caught)}` });
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Manage challenges"
        description="Publish or unpublish challenges, or add a new one."
        actions={
          <Button href="/admin/challenges/new">
            <Plus aria-hidden="true" className="h-4 w-4" />
            New challenge
          </Button>
        }
      />

      {loading && !data ? (
        <PageLoader />
      ) : !data ? (
        <ErrorState message={error ?? "Could not load challenges."} onRetry={reload} />
      ) : (
        <Card className="overflow-hidden p-0">
          <Table>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Category</Th>
                <Th>Difficulty</Th>
                <Th>Lab</Th>
                <Th className="text-right">Points</Th>
                <Th>Status</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {data.map((challenge) => (
                <Tr key={challenge.id}>
                  <Td>
                    <span className="font-medium text-gray-50">{challenge.name}</span>
                    <span className="block font-mono text-xs text-gray-400">{challenge.slug}</span>
                  </Td>
                  <Td>{challenge.category_name}</Td>
                  <Td>
                    <DifficultyBadge difficulty={challenge.difficulty} />
                  </Td>
                  <Td className="font-mono text-xs">{challenge.lab_kind}</Td>
                  <Td className="text-right font-mono text-brand-400">{challenge.points}</Td>
                  <Td>
                    <Badge tone={challenge.published ? "success" : "neutral"}>
                      {challenge.published ? "published" : "draft"}
                    </Badge>
                  </Td>
                  <Td className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => void togglePublished(challenge)}>
                      {challenge.published ? "Unpublish" : "Publish"}
                    </Button>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      <Card className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <SectionLabel>Advanced: publish from manifest</SectionLabel>
          <p className="text-sm text-gray-400">
            For bulk or scripted changes, paste a challenge manifest (JSON). Unlike the form, this
            can also update an existing challenge with the same slug.
          </p>
        </div>
        <Textarea
          id="manifest"
          label="Manifest"
          rows={12}
          spellCheck={false}
          value={manifest}
          onChange={(event) => setManifest(event.target.value)}
          className="font-mono"
        />
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" disabled={busy} onClick={() => void submitManifest(false)}>
            Validate
          </Button>
          <Button disabled={busy} onClick={() => void submitManifest(true)}>
            Validate &amp; publish
          </Button>
        </div>
        {result && <Alert tone={result.tone}>{result.text}</Alert>}
      </Card>
    </PageContainer>
  );
}
