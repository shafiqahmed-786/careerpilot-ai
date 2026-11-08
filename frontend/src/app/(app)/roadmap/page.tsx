"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AiBadge, Badge, Card, EmptyState, ErrorNote, PageHeader, PageSkeleton, ProgressBar, Spinner, btnGhost, btnPrimary, inputClass } from "@/components/ui";
import { api, type Assessment, type Roadmap, type Task } from "@/lib/api";
import { waitForJob } from "@/lib/jobs";
import { statusLabel } from "@/lib/progress";
import { currentWeek, groupByWeek, nextTaskId, replaceTask, sourceLabel } from "@/lib/roadmap";

const STATUSES = ["pending", "in_progress", "completed"] as const;
const MODES = [
  { value: "revise", label: "Revise my weekly plan" },
  { value: "intensive", label: "More intensive schedule (+50% hours)" },
  { value: "lighter", label: "Reduce my workload (−40% hours)" },
  { value: "focus", label: "Focus on one weak skill" },
];

export default function RoadmapPage() {
  const [plan, setPlan] = useState<Roadmap | null>(null);
  const [skills, setSkills] = useState<string[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [open, setOpen] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [mode, setMode] = useState("revise");
  const [focus, setFocus] = useState("");
  const [adapting, setAdapting] = useState(false);

  const load = useCallback(async () => {
    const [current, assessment] = await Promise.all([
      api<Roadmap | null>("/api/v1/roadmaps/current"),
      api<Assessment | null>("/api/v1/assessments/latest"),
    ]);
    setPlan(current);
    setSkills((assessment?.competencies ?? []).map((c) => c.name));
    setNotes(Object.fromEntries((current?.tasks ?? []).map((t) => [t.id, t.notes || ""])));
    if (current) setOpen((prev) => prev ?? nextTaskId(current.tasks));
  }, []);

  useEffect(() => {
    load()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [load]);

  async function update(task: Task, status: string) {
    setError("");
    setBusyId(task.id);
    try {
      const updated = await api<Task>(`/api/v1/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status, notes: notes[task.id] || "" }),
      });
      setPlan((current) => {
        if (!current) return current;
        const tasks = replaceTask(current.tasks, updated);
        const done = tasks.filter((t) => t.status === "completed").length;
        return { ...current, tasks, completion_percent: Math.round((done * 100) / tasks.length) };
      });
      setSavedId(task.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the task");
    } finally {
      setBusyId(null);
    }
  }

  async function adapt() {
    setError("");
    if (mode === "focus" && !focus) {
      setError("Choose the skill to focus on.");
      return;
    }
    setAdapting(true);
    try {
      const job = await api<{ id: string }>("/api/v1/roadmaps/current/adapt", {
        method: "POST",
        body: JSON.stringify({ mode, focus_skill: mode === "focus" ? focus : null }),
      });
      const done = await waitForJob(job.id);
      if (done.status === "failed") throw new Error(done.error || "The revised plan could not be created");
      setOpen(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not revise the plan");
    } finally {
      setAdapting(false);
    }
  }

  if (loading) return <PageSkeleton />;
  if (!plan) {
    return (
      <>
        <PageHeader title="Learning Roadmap" />
        <ErrorNote message={error} />
        <EmptyState
          title="No roadmap yet"
          text="Save your career profile to generate an assessment and a weekly roadmap in the background."
          action={<Link className={btnPrimary} href="/onboarding">Go to my profile</Link>}
        />
      </>
    );
  }

  const weeks = groupByWeek(plan.tasks);
  const now = currentWeek(weeks);
  const next = nextTaskId(plan.tasks);
  const milestones = new Map(plan.milestones.map((m) => [m.week, m.title]));

  return (
    <>
      <PageHeader title={plan.title} subtitle={plan.overview} actions={<AiBadge live={plan.source === "ai"} label={sourceLabel(plan.source)} />} />
      <div className="space-y-4">
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{plan.completion_percent}% complete</p>
              <p className="text-xs text-muted">{plan.timeline_weeks} weeks · {plan.weekly_hours}h / week{plan.adapted_count ? ` · revised ${plan.adapted_count}×` : ""}</p>
            </div>
            <div className="w-full md:w-72"><ProgressBar value={plan.completion_percent} tone="good" /></div>
          </div>
          {plan.adaptation_note ? <p className="mt-3 rounded-lg bg-raised px-3 py-2 text-xs text-muted">{plan.adaptation_note}</p> : null}
        </Card>

        <Card>
          <h2 className="text-sm font-medium">Adapt this plan to my progress</h2>
          <p className="mt-1 text-xs text-muted">Completed and in-progress tasks are kept. Only unstarted tasks are replaced, using your latest progress.</p>
          <div className="mt-3 flex flex-wrap items-end gap-3">
            <label className="text-xs text-muted">
              What do you need?
              <select className={`${inputClass} mt-1 w-64`} disabled={adapting} onChange={(e) => setMode(e.target.value)} value={mode}>
                {MODES.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
              </select>
            </label>
            {mode === "focus" ? (
              <label className="text-xs text-muted">
                Skill
                <select className={`${inputClass} mt-1 w-48`} disabled={adapting} onChange={(e) => setFocus(e.target.value)} value={focus}>
                  <option value="">Choose…</option>
                  {skills.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
            ) : null}
            <button className={btnPrimary} disabled={adapting} onClick={adapt} type="button">
              {adapting ? <><Spinner /> Revising…</> : "Revise my plan"}
            </button>
          </div>
        </Card>
        <ErrorNote message={error} />

        {weeks.map((week) => (
          <section key={week.week} className="rounded-xl border border-line bg-surface">
            <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-4">
              <div>
                <p className="text-sm font-medium">
                  Week {week.week} {week.week === now ? <Badge tone="accent">Now</Badge> : null}
                </p>
                <p className="mt-0.5 max-w-2xl text-xs text-muted">{week.objective}</p>
                {milestones.get(week.week) ? <p className="mt-1 text-xs text-accent">Milestone: {milestones.get(week.week)}</p> : null}
              </div>
              <div className="w-32 text-right text-xs text-muted">
                {week.completed}/{week.total} · {week.hours}h
                <div className="mt-1"><ProgressBar value={week.percent} tone={week.percent === 100 ? "good" : "accent"} /></div>
              </div>
            </header>
            <ul className="divide-y divide-line">
              {week.tasks.map((task) => {
                const expanded = open === task.id;
                return (
                  <li key={task.id} className="px-5 py-3">
                    <button className="flex w-full items-center justify-between gap-3 text-left" onClick={() => setOpen(expanded ? null : task.id)} aria-expanded={expanded} type="button">
                      <span className="text-sm">
                        <span className={task.status === "completed" ? "text-muted line-through" : ""}>{task.title}</span>
                        {task.id === next ? <span className="ml-2"><Badge tone="accent">Next</Badge></span> : null}
                      </span>
                      <Badge tone={task.status === "completed" ? "good" : task.status === "in_progress" ? "warn" : "neutral"}>{statusLabel(task.status)}</Badge>
                    </button>
                    {expanded ? (
                      <div className="mt-3 space-y-3 text-sm">
                        <p className="text-muted">{task.details}</p>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-lg bg-raised p-3"><p className="text-xs uppercase tracking-wide text-muted">Why it matters · outcome</p><p className="mt-1">{task.expected_outcome}</p></div>
                          <div className="rounded-lg bg-raised p-3"><p className="text-xs uppercase tracking-wide text-muted">Done when</p><p className="mt-1">{task.completion_criteria}</p></div>
                        </div>
                        <p className="text-xs text-muted">{task.estimated_hours}h · {task.skills.join(", ")}</p>
                        {task.resources.length ? (
                          <ul className="space-y-1">
                            {task.resources.map((r) => (
                              <li key={r.url}><a className="text-accent hover:underline" href={r.url} rel="noreferrer" target="_blank">{r.title}</a> <span className="text-xs text-muted">{r.domain}{r.provider === "demo" ? " · demo catalog" : ""}</span></li>
                            ))}
                          </ul>
                        ) : null}
                        <textarea
                          aria-label={`Notes for ${task.title}`}
                          className={`${inputClass} min-h-16`}
                          maxLength={2000}
                          onChange={(e) => { setSavedId(null); setNotes((c) => ({ ...c, [task.id]: e.target.value })); }}
                          placeholder="Notes: what you built, what was hard…"
                          value={notes[task.id] ?? ""}
                        />
                        <div className="flex flex-wrap items-center gap-2">
                          {STATUSES.map((s) => (
                            <button key={s} className={`${btnGhost} ${task.status === s ? "!border-accent !text-accent" : ""}`} disabled={busyId === task.id} onClick={() => update(task, s)} type="button">
                              Mark {statusLabel(s).toLowerCase()}
                            </button>
                          ))}
                          <button className={btnGhost} disabled={busyId === task.id || (notes[task.id] ?? "") === (task.notes ?? "")} onClick={() => update(task, task.status)} type="button">Save notes</button>
                          {savedId === task.id ? <span className="text-xs text-good" role="status">Saved</span> : null}
                        </div>
                      </div>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>
    </>
  );
}
