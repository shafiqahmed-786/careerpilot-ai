"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { api, getToken, type Skill } from "@/lib/api";

const emptySkill = (): Skill => ({ name: "", proficiency: 1 });

export default function OnboardingPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [education, setEducation] = useState("");
  const [experience, setExperience] = useState("student");
  const [skills, setSkills] = useState<Skill[]>([emptySkill()]);
  const [projects, setProjects] = useState("");
  const [target, setTarget] = useState("Backend Engineer");
  const [hours, setHours] = useState(6);
  const [weeks, setWeeks] = useState(8);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<{
      full_name: string;
      education: string;
      experience_level: string;
      skills: Skill[];
      projects: string;
      target_career: string;
      weekly_hours: number;
      timeline_weeks: number;
    } | null>("/api/v1/profile")
      .then((profile) => {
        if (!profile) return;
        setFullName(profile.full_name);
        setEducation(profile.education);
        setExperience(profile.experience_level);
        setSkills(profile.skills.length ? profile.skills : [emptySkill()]);
        setProjects(profile.projects);
        setTarget(profile.target_career);
        setHours(profile.weekly_hours);
        setWeeks(profile.timeline_weeks);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [router]);

  function updateSkill(index: number, patch: Partial<Skill>) {
    setSkills((current) => current.map((skill, i) => (i === index ? { ...skill, ...patch } : skill)));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    const cleaned = skills
      .map((skill) => ({
        name: skill.name.trim(),
        proficiency: Math.max(0, Math.min(5, Math.round(Number(skill.proficiency) || 0))),
      }))
      .filter((skill) => skill.name);
    try {
      await api("/api/v1/profile", {
        method: "PUT",
        body: JSON.stringify({
          full_name: fullName,
          education,
          experience_level: experience,
          skills: cleaned,
          projects,
          target_career: target,
          weekly_hours: Number(hours),
          timeline_weeks: Number(weeks),
        }),
      });
      await api("/api/v1/assessments", { method: "POST" });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the profile");
    } finally {
      setPending(false);
    }
  }

  if (loading) return <main className="mx-auto max-w-3xl px-5 py-16 text-muted">Loading profile…</main>;

  return (
    <main className="mx-auto max-w-3xl px-5 py-12">
      <h1 className="font-serif text-4xl">Career profile</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Skill levels are what you report. CareerPilot uses them as planning inputs and does not treat them as verified ability.
      </p>
      <form className="mt-8 space-y-5" onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm">
            Full name
            <input className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2" onChange={(e) => setFullName(e.target.value)} value={fullName} />
          </label>
          <label className="text-sm">
            Experience
            <select className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2" onChange={(e) => setExperience(e.target.value)} value={experience}>
              <option value="student">Student</option>
              <option value="fresh_graduate">Fresh graduate</option>
              <option value="junior">Junior</option>
            </select>
          </label>
        </div>
        <label className="block text-sm">
          Education
          <input className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2" onChange={(e) => setEducation(e.target.value)} value={education} />
        </label>
        <label className="block text-sm">
          Target career
          <input className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2" onChange={(e) => setTarget(e.target.value)} required value={target} />
        </label>
        <fieldset className="space-y-3">
          <legend className="text-sm">Self-reported skills</legend>
          {skills.map((skill, index) => (
            <div className="grid grid-cols-[1fr_140px] gap-3" key={index}>
              <input
                aria-label={`Skill ${index + 1}`}
                className="rounded-xl border border-line bg-card px-3 py-2"
                onChange={(e) => updateSkill(index, { name: e.target.value })}
                placeholder="Python"
                value={skill.name}
              />
              <label className="text-sm text-muted">
                Level 0–5
                <input
                  className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2"
                  max={5}
                  min={0}
                  onChange={(e) => updateSkill(index, { proficiency: Number(e.target.value) })}
                  type="number"
                  value={skill.proficiency}
                />
              </label>
            </div>
          ))}
          <div className="flex gap-4 text-sm">
            <button className="text-moss" onClick={() => setSkills((current) => [...current, emptySkill()])} type="button">
              Add skill
            </button>
            {skills.length > 1 ? (
              <button className="text-muted" onClick={() => setSkills((current) => current.slice(0, -1))} type="button">
                Remove last
              </button>
            ) : null}
          </div>
        </fieldset>
        <label className="block text-sm">
          Projects or experience
          <textarea className="mt-1 min-h-28 w-full rounded-xl border border-line bg-card px-3 py-2" onChange={(e) => setProjects(e.target.value)} value={projects} />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm">
            Weekly study hours
            <input className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2" max={40} min={1} onChange={(e) => setHours(Number(e.target.value))} type="number" value={hours} />
          </label>
          <label className="text-sm">
            Timeline
            <select className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2" onChange={(e) => setWeeks(Number(e.target.value))} value={weeks}>
              <option value={4}>4 weeks</option>
              <option value={8}>8 weeks</option>
              <option value={12}>12 weeks</option>
            </select>
          </label>
        </div>
        {error ? (
          <p className="text-sm text-clay" role="alert">
            {error}
          </p>
        ) : null}
        <button className="rounded-full bg-moss px-5 py-2.5 text-white disabled:opacity-60" disabled={pending} type="submit">
          {pending ? "Building your plan…" : "Save and generate roadmap"}
        </button>
      </form>
    </main>
  );
}
