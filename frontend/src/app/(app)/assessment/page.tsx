"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AiBadge, Badge, Card, EmptyState, ErrorNote, PageHeader, PageSkeleton, ProgressBar, Spinner, btnPrimary } from "@/components/ui";
import { api, type Assessment } from "@/lib/api";
import { waitForJob } from "@/lib/jobs";
import { statusLabel } from "@/lib/progress";

export default function AssessmentPage() {
  const [data, setData] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => setData(await api<Assessment | null>("/api/v1/assessments/latest")), []);

  useEffect(() => {
    load().catch((e: Error) => setError(e.message)).finally(() => setLoading(false));
  }, [load]);

  async function rerun() {
    setRunning(true);
    setError("");
    try {
      const job = await api<{ id: string }>("/api/v1/assessments", { method: "POST" });
      const done = await waitForJob(job.id);
      if (done.status === "failed") throw new Error(done.error || "The assessment failed");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run the assessment");
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <PageSkeleton />;
  const action = (
    <button className={btnPrimary} disabled={running} onClick={rerun} type="button">
      {running ? <><Spinner /> Running…</> : "Re-run assessment"}
    </button>
  );
  if (!data) {
    return (
      <>
        <PageHeader title="Skill Assessment" />
        <ErrorNote message={error} />
        <EmptyState title="No assessment yet" text="Complete your profile first to evaluate your skills and generate a personalized readiness assessment." action={<Link className={btnPrimary} href="/onboarding">Go to my profile</Link>} />
      </>
    );
  }
  const skills = new Set(data.resources.map((r) => r.skill));
  return (
    <>
      <PageHeader title={`${data.normalized_role} assessment`} subtitle="Scores come from a fixed rubric: priority = importance × gap. No language model touches the numbers." actions={action} />
      <div className="space-y-4">
        <ErrorNote message={error} />
        <Card>
          <div className="mb-2 flex items-center gap-2"><AiBadge live={data.provider === "groq"} label={data.provider === "groq" ? "AI Narrative Analysis" : "Narrative Summary (Demo)"} /><Badge>Rubric {data.rubric_version}</Badge></div>
          <p className="text-sm leading-relaxed">{data.summary}</p>
          <p className="mt-2 text-sm text-muted">{data.learn_first_reason}</p>
          <p className="mt-3 text-xs text-warn">{data.disclaimer}</p>
        </Card>
        <Card>
          <h2 className="mb-4 text-sm font-medium">Competencies</h2>
          <ul className="space-y-4">
            {data.competencies.map((c) => (
              <li key={c.name}>
                <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="font-medium">{c.name}</span>
                  <span className="flex items-center gap-2 text-xs text-muted">importance {c.importance} · self {c.self_reported_level} / target {c.target_level} · priority {c.priority_score}
                    <Badge tone={c.status === "sufficient" ? "good" : c.status === "missing" ? "bad" : "warn"}>{statusLabel(c.status)}</Badge></span>
                </div>
                <div className="mt-2"><ProgressBar value={(c.self_reported_level / c.target_level) * 100} tone={c.status === "sufficient" ? "good" : "accent"} /></div>
                <p className="mt-1 text-xs text-muted">{c.why_it_matters} {c.recommendation}</p>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-medium">Learning resources</h2><Badge tone={data.resources.some((r) => r.provider === "demo") ? "warn" : "good"}>{data.resources.some((r) => r.provider === "demo") ? "Demo catalog, not live search" : "Live search (Tavily)"}</Badge></div>
          {Array.from(skills).map((skill) => (
            <div key={skill} className="mb-4">
              <p className="text-xs uppercase tracking-wide text-muted">{skill}</p>
              <ul className="mt-1 space-y-2">
                {data.resources.filter((r) => r.skill === skill).map((r) => (
                  <li key={r.id} className="text-sm"><a className="text-accent hover:underline" href={r.url} rel="noreferrer" target="_blank">{r.title}</a><p className="text-xs text-muted">{r.domain} · {r.relevance}</p></li>
                ))}
              </ul>
            </div>
          ))}
        </Card>
      </div>
    </>
  );
}
