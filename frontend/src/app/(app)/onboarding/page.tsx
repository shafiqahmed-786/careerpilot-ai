"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { Card, ErrorNote, PageHeader, PageSkeleton, btnGhost, btnPrimary, inputClass } from "@/components/ui";
import { api, type Profile, type Skill } from "@/lib/api";

const emptySkill = (): Skill => ({ name: "", proficiency: 1 });

export default function ProfilePage() {
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
  const [saved, setSaved] = useState(false);
  const [pending, setPending] = useState<"" | "save" | "generate">("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Profile | null>("/api/v1/profile")
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
  }, []);

  function updateSkill(index: number, patch: Partial<Skill>) {
    setSkills((current) => current.map((skill, i) => (i === index ? { ...skill, ...patch } : skill)));
  }

  async function submit(event: FormEvent, generate: boolean) {
    event.preventDefault();
    setPending(generate ? "generate" : "save");
    setError("");
    setSaved(false);
    const cleaned = skills
      .map((skill) => ({ name: skill.name.trim(), proficiency: Math.max(0, Math.min(5, Math.round(Number(skill.proficiency) || 0))) }))
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
      if (generate) {
        await api("/api/v1/assessments", { method: "POST" });
        router.push("/dashboard");
      } else {
        setSaved(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the profile");
    } finally {
      setPending("");
    }
  }

  if (loading) return <PageSkeleton />;

  return (
    <>
      <PageHeader
        title="My Career Profile"
        subtitle="Skill levels are what you report. CareerPilot uses them as planning inputs and never treats them as verified ability."
      />
      <form className="max-w-3xl space-y-5" onSubmit={(e) => submit(e, true)}>
        <Card className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              Full name
              <input className={`${inputClass} mt-1`} onChange={(e) => setFullName(e.target.value)} value={fullName} />
            </label>
            <label className="text-sm">
              Experience
              <select className={`${inputClass} mt-1`} onChange={(e) => setExperience(e.target.value)} value={experience}>
                <option value="student">Student</option>
                <option value="fresh_graduate">Fresh graduate</option>
                <option value="junior">Junior</option>
              </select>
            </label>
          </div>
          <label className="block text-sm">
            Education
            <input className={`${inputClass} mt-1`} onChange={(e) => setEducation(e.target.value)} value={education} />
          </label>
          <label className="block text-sm">
            Target career
            <input className={`${inputClass} mt-1`} onChange={(e) => setTarget(e.target.value)} placeholder="AI Engineer, Backend Engineer, Data Analyst…" required value={target} />
          </label>
        </Card>
        <Card>
          <fieldset className="space-y-3">
            <legend className="mb-1 text-sm font-medium">Self-reported skills</legend>
            {skills.map((skill, index) => (
              <div className="grid grid-cols-[1fr_120px] gap-3" key={index}>
                <input aria-label={`Skill ${index + 1}`} className={inputClass} onChange={(e) => updateSkill(index, { name: e.target.value })} placeholder="Python" value={skill.name} />
                <input aria-label={`Level for skill ${index + 1} (0 to 5)`} className={inputClass} max={5} min={0} onChange={(e) => updateSkill(index, { proficiency: Number(e.target.value) })} type="number" value={skill.proficiency} />
              </div>
            ))}
            <p className="text-xs text-muted">Level 0–5. 1 = beginner, 3 = comfortable, 5 = expert.</p>
            <div className="flex gap-3">
              <button className={btnGhost} onClick={() => setSkills((c) => [...c, emptySkill()])} type="button">Add skill</button>
              {skills.length > 1 ? <button className={btnGhost} onClick={() => setSkills((c) => c.slice(0, -1))} type="button">Remove last</button> : null}
            </div>
          </fieldset>
        </Card>
        <Card className="space-y-4">
          <label className="block text-sm">
            Projects or experience
            <textarea className={`${inputClass} mt-1 min-h-28`} maxLength={4000} onChange={(e) => setProjects(e.target.value)} value={projects} />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              Weekly study hours
              <input className={`${inputClass} mt-1`} max={40} min={1} onChange={(e) => setHours(Number(e.target.value))} type="number" value={hours} />
            </label>
            <label className="text-sm">
              Timeline
              <select className={`${inputClass} mt-1`} onChange={(e) => setWeeks(Number(e.target.value))} value={weeks}>
                <option value={4}>4 weeks</option>
                <option value={8}>8 weeks</option>
                <option value={12}>12 weeks</option>
              </select>
            </label>
          </div>
        </Card>
        <ErrorNote message={error} />
        {saved ? <p className="text-sm text-good" role="status">Profile saved.</p> : null}
        <div className="flex flex-wrap gap-3">
          <button className={btnPrimary} disabled={pending !== ""} type="submit">
            {pending === "generate" ? "Building your plan…" : "Save and generate roadmap"}
          </button>
          <button className={btnGhost} disabled={pending !== ""} onClick={(e) => submit(e, false)} type="button">
            {pending === "save" ? "Saving…" : "Save profile only"}
          </button>
        </div>
      </form>
    </>
  );
}
