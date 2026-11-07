"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken, type Roadmap, type Task } from "@/lib/api";
import { statusLabel } from "@/lib/progress";

export default function RoadmapPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<Roadmap | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    const current = await api<Roadmap | null>("/api/v1/roadmaps/current");
    setPlan(current);
    setNotes(Object.fromEntries((current?.tasks || []).map((task) => [task.id, task.notes || ""])));
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    load()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [load, router]);

  async function update(task: Task, status: string) {
    setError("");
    setBusyId(task.id);
    try {
      await api(`/api/v1/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status, notes: notes[task.id] || "" }),
      });
      await load();
      setSavedId(task.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the task");
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <main className="mx-auto max-w-4xl px-5 py-16 text-muted">Loading roadmap…</main>;
  if (!plan && error) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16">
        <p className="text-clay" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!plan) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16">
        <h1 className="font-serif text-4xl">No roadmap yet</h1>
        <p className="mt-2 text-muted">Generate one from your career profile. The worker stores it before this page can show tasks.</p>
        <Link className="mt-4 inline-block text-moss" href="/onboarding">Go to profile</Link>
      </main>
    );
  }

  const weeks = [...new Set(plan.tasks.map((task) => task.week_number))];

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <p className="text-sm uppercase tracking-[0.14em] text-moss">{plan.completion_percent}% complete · {plan.provider} narrative</p>
      <h1 className="mt-2 font-serif text-4xl">{plan.title}</h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-muted">{plan.overview}</p>
      <p className="mt-2 text-sm text-muted">{plan.weekly_hours} planned hours each week.</p>
      {error ? (
        <p className="mt-4 text-sm text-clay" role="alert">
          {error}
        </p>
      ) : null}
      <div className="mt-8 space-y-8">
        {weeks.map((week) => {
          const tasks = plan.tasks.filter((task) => task.week_number === week);
          return (
            <section key={week}>
              <h2 className="font-serif text-2xl">Week {week}</h2>
              <p className="text-sm text-muted">{tasks[0]?.objective}</p>
              <div className="mt-3 space-y-3">
                {tasks.map((task) => (
                  <article className="rounded-2xl border border-line bg-card p-5" key={task.id}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium">{task.title}</h3>
                        <p className="mt-1 text-sm text-muted">{task.details}</p>
                      </div>
                      <span className="text-xs uppercase tracking-wide text-moss">{statusLabel(task.status)}</span>
                    </div>
                    <dl className="mt-3 grid gap-2 text-sm text-muted md:grid-cols-2">
                      <div>Skills: {task.skills.join(", ") || "—"}</div>
                      <div>Estimated time: {task.estimated_hours}h</div>
                      <div>Outcome: {task.expected_outcome}</div>
                      <div>Done when: {task.completion_criteria}</div>
                    </dl>
                    <ul className="mt-3 space-y-1 text-sm">
                      {task.resources.map((resource) => (
                        <li key={resource.url}>
                          <a className="text-moss" href={resource.url} rel="noreferrer" target="_blank">{resource.title}</a>
                          {resource.provider === "demo" ? <span className="ml-2 text-xs text-clay">Demo resource</span> : null}
                        </li>
                      ))}
                    </ul>
                    <label className="mt-3 block text-sm">
                      Notes
                      <textarea
                        className="mt-1 w-full rounded-xl border border-line px-3 py-2"
                        onChange={(event) => {
                          setSavedId(null);
                          setNotes((current) => ({ ...current, [task.id]: event.target.value }));
                        }}
                        value={notes[task.id] || ""}
                      />
                    </label>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(["pending", "in_progress", "completed"] as const).map((status) => (
                        <button
                          className={`rounded-full border px-3 py-1 text-sm hover:border-moss disabled:opacity-60 ${
                            task.status === status ? "border-moss bg-[#e5f3ee] text-moss" : "border-line"
                          }`}
                          disabled={busyId === task.id}
                          key={status}
                          onClick={() => update(task, status)}
                          type="button"
                        >
                          Mark {statusLabel(status).toLowerCase()}
                        </button>
                      ))}
                      <button
                        className="rounded-full border border-line px-3 py-1 text-sm hover:border-moss disabled:opacity-60"
                        disabled={busyId === task.id || (notes[task.id] || "") === (task.notes || "")}
                        onClick={() => update(task, task.status)}
                        type="button"
                      >
                        Save notes
                      </button>
                      {savedId === task.id ? <span className="self-center text-xs text-moss">Saved</span> : null}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </main>
  );
}
