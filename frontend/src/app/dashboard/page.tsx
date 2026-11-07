"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken, type Dashboard, type Job } from "@/lib/api";
import { statusLabel } from "@/lib/progress";

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<Dashboard | null>(null);
  const [jobNote, setJobNote] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const board = await api<Dashboard>("/api/v1/dashboard");
    setData(board);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let timer: number | undefined;
    const jobId = sessionStorage.getItem("careerpilot_job");
    const watch = async () => {
      try {
        if (jobId) {
          const job = await api<Job>(`/api/v1/jobs/${jobId}`);
          if (job.status === "queued" || job.status === "running") {
            setJobNote(job.status === "queued" ? "Assessment is queued for the worker." : "The worker is building your assessment and roadmap.");
            timer = window.setTimeout(watch, 2000);
            return;
          }
          sessionStorage.removeItem("careerpilot_job");
          if (job.status === "failed") {
            setError(job.error || "The assessment job failed.");
          }
        }
        setJobNote("");
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load the dashboard");
      }
    };
    void watch();
    return () => window.clearTimeout(timer);
  }, [load, router]);

  if (error && !data) {
    return <main className="mx-auto max-w-3xl px-5 py-16 text-clay">{error}</main>;
  }
  if (!data) {
    return <main className="mx-auto max-w-3xl px-5 py-16 text-muted">{jobNote || "Loading your dashboard…"}</main>;
  }

  const demoSearch = data.resources.some((item) => item.provider === "demo");
  const maxScore = Math.max(1, ...data.top_gaps.map((gap) => gap.priority_score));

  return (
    <main className="mx-auto max-w-6xl px-5 py-10">
      {jobNote ? <p className="mb-4 rounded-xl bg-[#f3ead2] px-4 py-3 text-sm">{jobNote}</p> : null}
      {error ? <p className="mb-4 text-sm text-clay">{error}</p> : null}
      {!data.profile ? (
        <section className="rounded-3xl border border-line bg-card p-8">
          <h1 className="font-serif text-4xl">Start with your profile</h1>
          <p className="mt-2 text-muted">The dashboard stays empty until a career goal and skills are saved.</p>
          <Link className="mt-6 inline-block rounded-full bg-moss px-5 py-2.5 text-white" href="/onboarding">
            Complete profile
          </Link>
        </section>
      ) : (
        <>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.14em] text-moss">Career goal</p>
              <h1 className="font-serif text-4xl">{data.profile.target_career}</h1>
              <p className="mt-1 text-muted">
                {data.profile.weekly_hours} hours / week · {data.profile.timeline_weeks} weeks
              </p>
            </div>
            <div className="rounded-2xl border border-line bg-card px-5 py-4 text-right">
              <p className="text-sm text-muted">Roadmap completion</p>
              <p className="font-serif text-4xl">{data.completion_percent}%</p>
            </div>
          </div>

          {data.assessment ? (
            <section className="mt-8 grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
              <article className="rounded-3xl border border-line bg-card p-6">
                <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-wide text-muted">
                  <span>Normalized role: {data.assessment.normalized_role}</span>
                  <span>Narrative: {data.assessment.provider}</span>
                  <span>Rubric: {data.assessment.rubric_version}</span>
                </div>
                <p className="mt-4 leading-relaxed">{data.assessment.summary}</p>
                <p className="mt-3 text-sm text-muted">{data.assessment.learn_first_reason}</p>
                <p className="mt-4 text-sm text-clay">{data.assessment.disclaimer}</p>
              </article>
              <article className="rounded-3xl border border-line bg-card p-6">
                <h2 className="font-serif text-2xl">Next task</h2>
                {data.next_task ? (
                  <>
                    <p className="mt-3 font-medium">{data.next_task.title}</p>
                    <p className="mt-1 text-sm text-muted">Week {data.next_task.week_number} · {data.next_task.estimated_hours}h</p>
                    <Link className="mt-4 inline-block text-sm text-moss" href="/roadmap">
                      Open roadmap
                    </Link>
                  </>
                ) : (
                  <p className="mt-3 text-sm text-muted">
                    {data.roadmap ? "Every saved task is complete." : "Generate a roadmap from your profile."}
                  </p>
                )}
              </article>
            </section>
          ) : (
            <section className="mt-8 rounded-3xl border border-dashed border-line bg-card p-6">
              <h2 className="font-serif text-2xl">No assessment yet</h2>
              <p className="mt-2 text-sm text-muted">Saving your profile queues the worker that writes the assessment and roadmap.</p>
              <Link className="mt-4 inline-block text-moss" href="/onboarding">Generate a roadmap</Link>
            </section>
          )}

          <section className="mt-8 grid gap-4 lg:grid-cols-2">
            <article className="rounded-3xl border border-line bg-card p-6">
              <h2 className="font-serif text-2xl">Highest-priority gaps</h2>
              <ul className="mt-4 space-y-4">
                {data.top_gaps.length === 0 ? <li className="text-sm text-muted">No open gaps on the latest assessment.</li> : null}
                {data.top_gaps.map((gap) => (
                  <li key={gap.name}>
                    <div className="flex items-center justify-between text-sm">
                      <span>{gap.name}</span>
                      <span className="text-muted">{statusLabel(gap.status)} · score {gap.priority_score}</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-[#efe8dc]">
                      <div className="h-2 rounded-full bg-moss" style={{ width: `${(gap.priority_score / maxScore) * 100}%` }} />
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      Self-reported {gap.self_reported_level} / target {gap.target_level}. {gap.why_it_matters}
                    </p>
                  </li>
                ))}
              </ul>
            </article>
            <article className="rounded-3xl border border-line bg-card p-6">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-serif text-2xl">Learning resources</h2>
                {demoSearch ? <span className="rounded-full bg-[#f6e4dc] px-2 py-1 text-xs text-clay">Demo catalog, not live search</span> : <span className="rounded-full bg-[#e5f3ee] px-2 py-1 text-xs text-moss">Live search</span>}
              </div>
              <ul className="mt-4 space-y-3">
                {data.resources.length === 0 ? <li className="text-sm text-muted">Resources appear after the assessment job finishes.</li> : null}
                {data.resources.map((resource) => (
                  <li key={resource.id}>
                    <a className="font-medium text-moss" href={resource.url} rel="noreferrer" target="_blank">{resource.title}</a>
                    <p className="text-xs text-muted">{resource.domain} · {resource.skill} · {resource.provider}</p>
                  </li>
                ))}
              </ul>
            </article>
          </section>

          <section className="mt-8 rounded-3xl border border-line bg-card p-6">
            <h2 className="font-serif text-2xl">Recently completed</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {data.recently_completed.length === 0 ? <li className="text-muted">Completed tasks will show up here.</li> : null}
              {data.recently_completed.map((task) => (
                <li key={task.id}>{task.title}{task.notes ? ` — ${task.notes}` : ""}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </main>
  );
}
