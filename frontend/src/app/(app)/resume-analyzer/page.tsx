"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { AiBadge, Badge, Card, EmptyState, ErrorNote, PageHeader, PageSkeleton, Ring, Spinner, btnGhost, btnPrimary } from "@/components/ui";
import { ApiError, api, type Job, type ResumeResult } from "@/lib/api";
import { waitForJob } from "@/lib/jobs";
import { MAX_RESUME_BYTES, categoriesOf, evidenceLabel, groupSkills, validateResumeFile } from "@/lib/resume";

type Phase = "idle" | "uploading" | "processing";

export default function ResumeAnalyzerPage() {
  const [result, setResult] = useState<ResumeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => setResult(await api<ResumeResult | null>("/api/v1/resume/latest")), []);

  useEffect(() => {
    load().catch((e: Error) => setError(e.message)).finally(() => setLoading(false));
  }, [load]);

  async function upload(file: File | undefined) {
    if (!file) return;
    setError("");
    setMessage("");
    const problem = validateResumeFile(file);
    if (problem) {
      setError(problem);
      return;
    }
    setPhase("uploading");
    try {
      const form = new FormData();
      form.append("file", file);
      const started = await api<{ resume_id: string; job: Job }>("/api/v1/resume/analyze", { method: "POST", body: form });
      setPhase("processing");
      const done = await waitForJob(started.job.id);
      if (done.status === "failed") throw new Error(done.error || "The resume could not be analyzed");
      await load();
    } catch (e) {
      setError(e instanceof ApiError || e instanceof Error ? e.message : "Upload failed");
      await load().catch(() => undefined);
    } finally {
      setPhase("idle");
      if (input.current) input.current.value = "";
    }
  }

  async function applyToProfile() {
    if (!result) return;
    setError("");
    try {
      await api(`/api/v1/resume/${result.id}/apply-to-profile`, { method: "POST" });
      setMessage("Skills from your resume were added to your profile with conservative starting levels. Review them on your profile page.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update the profile");
    }
  }

  async function remove() {
    if (!result) return;
    try {
      await api(`/api/v1/resume/${result.id}`, { method: "DELETE" });
      setResult(null);
      setMessage("Analysis deleted.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete the analysis");
    }
  }

  if (loading) return <PageSkeleton />;
  const busy = phase !== "idle";
  const done = result?.status === "completed" && result.analysis;
  const analysis = result?.analysis;
  const groups = analysis ? groupSkills(analysis.skills) : null;
  const comparison = result?.comparison;

  return (
    <>
      <PageHeader title="Resume Analyzer" subtitle="Upload a PDF or DOCX. Skills are only counted as demonstrated when your resume shows them being used." />
      <div className="space-y-4">
        <div
          className={`rounded-xl border-2 border-dashed px-6 py-10 text-center transition ${drag ? "border-accent bg-accent/5" : "border-line bg-surface"}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); void upload(e.dataTransfer.files[0]); }}
        >
          {busy ? (
            <p className="flex items-center justify-center gap-2 text-sm" role="status"><Spinner />{phase === "uploading" ? "Uploading and reading your resume…" : "Analyzing in the background worker…"}</p>
          ) : (
            <>
              <p className="text-sm">Drag and drop your resume here, or</p>
              <button className={`${btnPrimary} mt-3`} onClick={() => input.current?.click()} type="button">Choose a file</button>
              <p className="mt-3 text-xs text-muted">PDF or DOCX, up to {MAX_RESUME_BYTES / 1024 / 1024} MB. The file is read in memory and never stored.</p>
            </>
          )}
          <input accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" aria-label="Resume file" className="hidden" onChange={(e) => void upload(e.target.files?.[0])} ref={input} type="file" />
        </div>
        <ErrorNote message={error} />
        {message ? <p className="rounded-lg border border-good/30 bg-good/10 px-3 py-2 text-sm text-good" role="status">{message}</p> : null}

        {result?.status === "failed" ? <ErrorNote message={result.error || "The last analysis failed."} /> : null}
        {!result && !busy ? <EmptyState title="No resume analyzed yet" text="Upload a resume to see skills with evidence, how they map to your target career, and what to build next." /> : null}

        {done && analysis && groups ? (
          <>
            <Card>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <AiBadge live={result.provider === "openai"} label={result.provider === "openai" ? "Analyzed by OpenAI" : "Keyword analysis (demo, no LLM)"} />
                <Badge>{result.filename}</Badge>
              </div>
              {result.notice ? <p className="mb-2 text-xs text-warn">{result.notice}</p> : null}
              <p className="text-sm leading-relaxed">{analysis.overview}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button className={btnPrimary} onClick={applyToProfile} type="button">Add these skills to my profile</button>
                <Link className={btnGhost} href="/onboarding">Edit profile</Link>
                <button className={btnGhost} onClick={remove} type="button">Delete analysis</button>
              </div>
            </Card>

            {comparison ? (
              <Card>
                <h2 className="text-sm font-medium">Fit for {comparison.target_role}</h2>
                <div className="mt-4 flex flex-wrap items-start gap-6">
                  <div className="text-center">
                    <Ring value={comparison.evidence_coverage_percent} label="evidence" />
                    <p className="mt-2 max-w-[10rem] text-xs text-muted">Evidence coverage, not a hiring score.</p>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">{comparison.summary}</p>
                    <ul className="mt-3 divide-y divide-line">
                      {comparison.competencies.map((c) => (
                        <li key={c.name} className="py-2 text-sm">
                          <div className="flex items-center justify-between gap-2">
                            <span>{c.name}</span>
                            <Badge tone={c.status === "demonstrated" ? "good" : c.status === "listed" ? "warn" : "bad"}>{evidenceLabel(c.status)}</Badge>
                          </div>
                          {c.evidence[0] ? <p className="mt-1 text-xs italic text-muted">“{c.evidence[0]}”</p> : null}
                        </li>
                      ))}
                    </ul>
                    <p className="mt-3 text-xs text-muted">Formula: {comparison.formula}</p>
                  </div>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div><p className="text-xs uppercase tracking-wide text-muted">Learning priorities</p><p className="mt-1 text-sm">{comparison.priorities.join(", ") || "None, every competency has evidence."}</p></div>
                  <div><p className="text-xs uppercase tracking-wide text-muted">Recommended projects</p><ul className="mt-1 list-disc space-y-1 pl-4 text-sm">{comparison.recommended_projects.map((p) => <li key={p}>{p}</li>)}</ul></div>
                </div>
              </Card>
            ) : (
              <Card><p className="text-sm text-muted">Set a target career in <Link className="text-accent" href="/onboarding">your profile</Link> and upload again to compare this resume with the role.</p></Card>
            )}

            <div className="grid gap-4 lg:grid-cols-3">
              {(["demonstrated", "listed", "inferred"] as const).map((level) => (
                <Card key={level}>
                  <h2 className="mb-3 flex items-center justify-between text-sm font-medium">{evidenceLabel(level)}<Badge tone={level === "demonstrated" ? "good" : level === "listed" ? "warn" : "neutral"}>{groups[level].length}</Badge></h2>
                  <ul className="space-y-3">
                    {groups[level].length === 0 ? <li className="text-xs text-muted">None.</li> : null}
                    {groups[level].map((s) => (
                      <li key={s.name} className="text-sm">
                        <p>{s.name} <span className="text-xs text-muted">· {s.category}</span></p>
                        {s.evidence.map((e) => <p key={e} className="mt-1 text-xs italic text-muted">“{e}”</p>)}
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
            <p className="text-xs text-muted">Categories: {categoriesOf(analysis.skills).join(", ") || "none"}.</p>

            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <h2 className="mb-2 text-sm font-medium">Strengths</h2>
                <ul className="list-disc space-y-1 pl-4 text-sm">{analysis.strengths.length ? analysis.strengths.map((s) => <li key={s}>{s}</li>) : <li className="text-muted">None detected.</li>}</ul>
                <h2 className="mb-2 mt-4 text-sm font-medium">Areas to improve</h2>
                <ul className="list-disc space-y-1 pl-4 text-sm">{analysis.improvements.length ? analysis.improvements.map((s) => <li key={s}>{s}</li>) : <li className="text-muted">None detected.</li>}</ul>
              </Card>
              <Card>
                <h2 className="mb-2 text-sm font-medium">Projects</h2>
                <ul className="space-y-2 text-sm">{analysis.projects.length ? analysis.projects.map((p) => <li key={p.name}><p>{p.name}</p><p className="text-xs text-muted">{p.summary}</p></li>) : <li className="text-muted">No projects detected.</li>}</ul>
                <h2 className="mb-2 mt-4 text-sm font-medium">Education and experience</h2>
                <ul className="list-disc space-y-1 pl-4 text-sm">{[...analysis.education, ...analysis.experience].map((s) => <li key={s}>{s}</li>)}</ul>
              </Card>
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}
