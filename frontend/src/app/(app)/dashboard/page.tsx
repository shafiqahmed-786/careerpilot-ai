"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActivityBars, SkillBars } from "@/components/charts";
import { Badge, Card, EmptyState, ErrorNote, PageHeader, PageSkeleton, ProgressBar, Ring, btnGhost, btnPrimary } from "@/components/ui";
import { api, type Dashboard } from "@/lib/api";
import { statusLabel } from "@/lib/progress";
import { groupByWeek } from "@/lib/roadmap";

const POLL_MS = 2000;
const STALL_MS = 45_000;
const KIND: Record<string, string> = { assessment: "assessment", adapt: "revised roadmap", resume: "resume analysis" };

function Stat({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card className="!p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 truncate text-2xl font-semibold">{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-muted">{hint}</p> : null}
    </Card>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [stalled, setStalled] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    const started = Date.now();
    const tick = async () => {
      try {
        const board = await api<Dashboard>("/api/v1/dashboard");
        if (cancelled) return;
        setData(board);
        setError("");
        const job = board.latest_job;
        if (job && (job.status === "queued" || job.status === "running")) {
          setStalled(job.status === "queued" && Date.now() - started > STALL_MS);
          timer = window.setTimeout(tick, POLL_MS);
        } else {
          setStalled(false);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load the dashboard");
      }
    };
    void tick();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [reloadKey]);

  async function retry() {
    setRetrying(true);
    try {
      await api("/api/v1/assessments", { method: "POST" });
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not queue the assessment");
    } finally {
      setRetrying(false);
    }
  }

  if (!data) {
    if (error) {
      return (
        <div className="space-y-3">
          <ErrorNote message={error} />
          <button className={btnGhost} onClick={() => setReloadKey((k) => k + 1)} type="button">
            Try again
          </button>
        </div>
      );
    }
    return <PageSkeleton />;
  }

  const job = data.latest_job;
  const working = job?.status === "queued" || job?.status === "running";
  const assessmentTime = data.assessment ? new Date(data.assessment.created_at).getTime() : 0;
  const jobFailed =
    job?.status === "failed" && job.kind !== "resume" && (!data.assessment || new Date(job.created_at).getTime() > assessmentTime);
  const weeks = data.roadmap ? groupByWeek(data.roadmap.tasks) : [];
  const name = data.profile?.full_name?.split(" ")[0];

  if (!data.profile) {
    return (
      <>
        <PageHeader title={`Welcome${name ? `, ${name}` : ""}`} subtitle="Three steps to your personalized career plan." />
        <EmptyState
          title="Start with your career profile"
          text="Tell CareerPilot your target role, skills and weekly hours. It scores your skill gaps, finds resources, and builds a roadmap in the background."
          action={
            <Link className={btnPrimary} href="/onboarding">
              Complete my profile
            </Link>
          }
        />
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {["Upload a resume to see which skills have real evidence", "Generate a weekly learning roadmap", "Ask the AI mentor what to do next"].map((text, i) => (
            <Card key={text}>
              <p className="text-xs text-accent">Step {i + 2}</p>
              <p className="mt-1 text-sm text-muted">{text}</p>
            </Card>
          ))}
        </div>
      </>
    );
  }

  const nextAction = data.next_task
    ? { title: data.next_task.title, text: `Week ${data.next_task.week_number} · ${data.next_task.estimated_hours}h · ${data.next_task.completion_criteria}`, href: "/roadmap", cta: "Open roadmap" }
    : !data.assessment
      ? { title: "Generate your assessment", text: "Your profile is saved. Run the assessment to calculate gaps and a roadmap.", href: "/onboarding", cta: "Generate roadmap" }
      : !data.resume
        ? { title: "Upload your resume", text: "See which of your skills are backed by project or experience evidence.", href: "/resume-analyzer", cta: "Analyze resume" }
        : { title: "Every task is complete", text: "Ask the mentor for a revised plan or a new focus.", href: "/mentor", cta: "Ask the mentor" };

  return (
    <>
      <PageHeader
        title={`${name ? `${name}, your` : "Your"} career workspace`}
        subtitle="Everything below is computed from your saved profile, assessment, roadmap and completed tasks."
        actions={
          <Link className={btnPrimary} href="/mentor">
            Ask AI Mentor
          </Link>
        }
      />
      <div className="space-y-4">
        {working ? (
          <div className="rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm" role="status">
            {job?.status === "queued" ? `Your ${KIND[job.kind] ?? "job"} is queued for the background worker.` : `The worker is building your ${KIND[job?.kind ?? ""] ?? "plan"}.`}
            {stalled ? <span className="ml-1 text-warn">Still queued. Make sure the RQ worker is running (python -m app.worker in backend/).</span> : null}
          </div>
        ) : null}
        {jobFailed ? (
          <div className="rounded-xl border border-bad/30 bg-bad/10 px-4 py-3 text-sm" role="alert">
            <p className="font-medium text-bad">The last job failed.</p>
            <p className="mt-1 text-muted">{job?.error || "No error detail was recorded."}</p>
            <button className={`${btnPrimary} mt-3`} disabled={retrying} onClick={retry} type="button">
              {retrying ? "Queueing…" : "Try again"}
            </button>
          </div>
        ) : null}
        <ErrorNote message={error} />

        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          <Stat label="Target career" value={data.profile.target_career} />
          <Stat label="Progress" value={`${data.completion_percent}%`} hint="of roadmap tasks" />
          <Stat label="Skills identified" value={data.skills_identified} hint="profile + resume" />
          <Stat label="Critical gaps" value={data.critical_gaps} hint="importance ≥ 4" />
          <Stat label="Milestones" value={`${data.milestones_completed}/${data.milestones_total}`} hint="weeks completed" />
          <Stat label="Streak" value={`${data.streak_days} d`} hint="days with a completed task" />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <h2 className="text-sm font-medium">Next recommended action</h2>
            <p className="mt-3 text-lg font-medium">{nextAction.title}</p>
            <p className="mt-1 text-sm text-muted">{nextAction.text}</p>
            <Link className={`${btnGhost} mt-4`} href={nextAction.href}>
              {nextAction.cta}
            </Link>
          </Card>
          <Card className="flex items-center gap-4">
            <Ring value={data.readiness_percent} label="coverage" />
            <div className="text-xs text-muted">
              <p className="font-medium text-ink">Career readiness</p>
              <p className="mt-1">Rubric coverage of your self-reported skills for {data.assessment?.normalized_role ?? "your role"}. Not a verified score.</p>
              {data.resume?.match_percent != null ? <p className="mt-1">Resume evidence coverage: {data.resume.match_percent}%</p> : null}
            </div>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="mb-4 text-sm font-medium">Skill progression</h2>
            {data.competencies.length ? <SkillBars items={data.competencies} /> : <p className="text-sm text-muted">Appears after the assessment finishes.</p>}
            <p className="mt-3 text-xs text-muted">Bar = self-reported level. Marker = roadmap target.</p>
          </Card>
          <Card>
            <h2 className="mb-4 text-sm font-medium">Learning activity · last 14 days</h2>
            <ActivityBars days={data.activity} />
            <p className="mt-3 text-xs text-muted">Counts tasks you marked completed (UTC days).</p>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="mb-3 text-sm font-medium">Priority skill gaps</h2>
            <ul className="space-y-3">
              {data.top_gaps.length === 0 ? <li className="text-sm text-muted">No open gaps yet.</li> : null}
              {data.top_gaps.map((gap) => (
                <li key={gap.name} className="flex items-start justify-between gap-3 text-sm">
                  <div>
                    <p>{gap.name}</p>
                    <p className="text-xs text-muted">{gap.why_it_matters}</p>
                  </div>
                  <Badge tone={gap.status === "missing" ? "bad" : "warn"}>{statusLabel(gap.status)} · {gap.priority_score}</Badge>
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium">Roadmap overview</h2>
              {data.roadmap ? <Badge tone={data.roadmap.source === "ai" ? "accent" : "warn"}>{data.roadmap.source === "ai" ? "AI-generated" : "Template"}</Badge> : null}
            </div>
            {weeks.length === 0 ? <p className="text-sm text-muted">No roadmap yet.</p> : null}
            <ul className="space-y-3">
              {weeks.map((week) => (
                <li key={week.week}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span>Week {week.week}</span>
                    <span className="text-muted">{week.completed}/{week.total} tasks</span>
                  </div>
                  <ProgressBar value={week.percent} tone={week.percent === 100 ? "good" : "accent"} />
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium">Recommended resources</h2>
              {data.resources.length ? <Badge tone={data.resources.some((r) => r.provider === "demo") ? "warn" : "good"}>{data.resources.some((r) => r.provider === "demo") ? "Demo catalog" : "Live search"}</Badge> : null}
            </div>
            <ul className="space-y-3">
              {data.resources.length === 0 ? <li className="text-sm text-muted">Resources appear after the assessment.</li> : null}
              {data.resources.map((r) => (
                <li key={r.id} className="text-sm">
                  <a className="text-accent hover:underline" href={r.url} rel="noreferrer" target="_blank">{r.title}</a>
                  <p className="text-xs text-muted">{r.domain} · {r.skill}</p>
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <h2 className="mb-3 text-sm font-medium">Recently completed</h2>
            <ul className="space-y-2 text-sm">
              {data.recently_completed.length === 0 ? <li className="text-muted">Completed tasks will show up here.</li> : null}
              {data.recently_completed.map((t) => (
                <li key={t.id}>{t.title}{t.notes ? <span className="text-muted"> — {t.notes}</span> : null}</li>
              ))}
            </ul>
            <div className="mt-5 border-t border-line pt-4">
              <p className="text-xs text-muted">Quick questions for the mentor</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {["What should I focus on this week?", "Analyze my biggest skill gaps."].map((q) => (
                  <Link key={q} className={btnGhost} href={`/mentor?q=${encodeURIComponent(q)}`}>{q}</Link>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
