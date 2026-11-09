"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge, Card, ErrorNote, PageHeader, PageSkeleton, btnGhost, btnPrimary, inputClass } from "@/components/ui";
import { api, clearToken, type Profile, type ResumeResult } from "@/lib/api";
import { useTheme } from "@/lib/theme";

export default function SettingsPage() {
  const router = useRouter();
  const { theme, toggle } = useTheme();

  const [email, setEmail] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [resume, setResume] = useState<ResumeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Preference states
  const [weeklyHours, setWeeklyHours] = useState<number>(10);
  const [savingPace, setSavingPace] = useState(false);
  const [remindersEnabled, setRemindersEnabled] = useState(true);
  const [deletingResume, setDeletingResume] = useState(false);

  useEffect(() => {
    // Load persisted notification preference
    const savedReminders = localStorage.getItem("cp-reminders-enabled");
    if (savedReminders !== null) {
      setRemindersEnabled(savedReminders === "true");
    }

    Promise.all([
      api<{ email: string }>("/api/v1/auth/me"),
      api<Profile | null>("/api/v1/profile").catch(() => null),
      api<ResumeResult | null>("/api/v1/resume/latest").catch(() => null),
    ])
      .then(([me, prof, res]) => {
        setEmail(me.email);
        if (prof) {
          setProfile(prof);
          setWeeklyHours(prof.weekly_hours || 10);
        }
        if (res) {
          setResume(res);
        }
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function handleReminderToggle() {
    const next = !remindersEnabled;
    setRemindersEnabled(next);
    localStorage.setItem("cp-reminders-enabled", String(next));
    flashSuccess(next ? "Milestone reminders enabled." : "Milestone reminders disabled.");
  }

  function flashSuccess(msg: string) {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(""), 4000);
  }

  async function handleSavePace() {
    if (!profile) return;
    setSavingPace(true);
    setError("");
    try {
      const updated = await api<Profile>("/api/v1/profile", {
        method: "PUT",
        body: JSON.stringify({
          full_name: profile.full_name,
          education: profile.education,
          experience_level: profile.experience_level,
          skills: profile.skills,
          projects: profile.projects,
          target_career: profile.target_career,
          weekly_hours: weeklyHours,
          timeline_weeks: profile.timeline_weeks,
        }),
      });
      setProfile(updated);
      flashSuccess(`Study pace updated to ${weeklyHours} hours per week.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update study pace");
    } finally {
      setSavingPace(false);
    }
  }

  async function handleDeleteResume() {
    if (!resume) return;
    if (!confirm("Are you sure you want to permanently delete your saved resume analysis?")) return;
    setDeletingResume(true);
    setError("");
    try {
      await api(`/api/v1/resume/${resume.id}`, { method: "DELETE" });
      setResume(null);
      flashSuccess("Your resume analysis data has been permanently deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete resume analysis");
    } finally {
      setDeletingResume(false);
    }
  }

  function handleSignOut() {
    clearToken();
    router.push("/login");
  }

  if (loading) return <PageSkeleton />;

  return (
    <>
      <PageHeader
        title="Settings"
        subtitle="Manage your account, learning preferences, and privacy controls."
      />

      <div className="max-w-3xl space-y-6">
        <ErrorNote message={error} />

        {successMessage ? (
          <div className="rounded-lg border border-good/30 bg-good/10 px-4 py-3 text-sm text-good" role="status">
            {successMessage}
          </div>
        ) : null}

        {/* 1. Account Section */}
        <Card>
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div>
              <h2 className="text-base font-semibold">Account</h2>
              <p className="mt-0.5 text-xs text-muted">Your identity and career profile details</p>
            </div>
            <button
              className="text-xs text-muted transition hover:text-bad"
              onClick={handleSignOut}
              type="button"
            >
              Sign out
            </button>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted">Email address</p>
              <p className="mt-1 font-medium">{email || "—"}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted">Target Career Role</p>
              <p className="mt-1 font-medium">{profile?.target_career || "Not set"}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted">Experience Level</p>
              <p className="mt-1 capitalize">{profile?.experience_level?.replace("_", " ") || "Not set"}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted">Education</p>
              <p className="mt-1">{profile?.education || "Not set"}</p>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3 border-t border-line pt-4">
            <Link className={btnPrimary} href="/onboarding">
              Edit Career Profile & Goals
            </Link>
            <button className={btnGhost} onClick={handleSignOut} type="button">
              Sign out
            </button>
          </div>
        </Card>

        {/* 2. Preferences Section */}
        <Card>
          <h2 className="text-base font-semibold">Preferences</h2>
          <p className="mt-0.5 text-xs text-muted">Customize your interface and learning experience</p>

          <div className="mt-5 space-y-6">
            {/* Theme Selector */}
            <div>
              <label className="text-sm font-medium">Appearance & Theme</label>
              <p className="text-xs text-muted">Choose your preferred application visual style</p>

              <div className="mt-3 grid grid-cols-2 gap-3 sm:max-w-md">
                <button
                  type="button"
                  onClick={() => { if (theme !== "light") toggle(); }}
                  className={`flex items-center gap-3 rounded-xl border p-3 text-left transition ${
                    theme === "light"
                      ? "border-accent bg-accent/10 shadow-sm"
                      : "border-line bg-raised hover:border-accent/40"
                  }`}
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface text-base">☀</span>
                  <div>
                    <p className="text-sm font-medium">Light Mode</p>
                    <p className="text-xs text-muted">Clean & bright</p>
                  </div>
                  {theme === "light" ? (
                    <span className="ml-auto"><Badge tone="accent">Active</Badge></span>
                  ) : null}
                </button>

                <button
                  type="button"
                  onClick={() => { if (theme !== "dark") toggle(); }}
                  className={`flex items-center gap-3 rounded-xl border p-3 text-left transition ${
                    theme === "dark"
                      ? "border-accent bg-accent/10 shadow-sm"
                      : "border-line bg-raised hover:border-accent/40"
                  }`}
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface text-base">☾</span>
                  <div>
                    <p className="text-sm font-medium">Dark Mode</p>
                    <p className="text-xs text-muted">Reduced eye strain</p>
                  </div>
                  {theme === "dark" ? (
                    <span className="ml-auto"><Badge tone="accent">Active</Badge></span>
                  ) : null}
                </button>
              </div>
            </div>

            {/* Learning Pace */}
            <div className="border-t border-line pt-4">
              <label className="text-sm font-medium" htmlFor="study-hours">
                Weekly Learning Commitment
              </label>
              <p className="text-xs text-muted">Adjust how many hours you plan to spend learning each week</p>

              <div className="mt-3 flex flex-wrap items-center gap-3">
                <select
                  id="study-hours"
                  className={`${inputClass} !w-44`}
                  value={weeklyHours}
                  onChange={(e) => setWeeklyHours(Number(e.target.value))}
                >
                  <option value={5}>5 hours / week</option>
                  <option value={10}>10 hours / week</option>
                  <option value={15}>15 hours / week</option>
                  <option value={20}>20 hours / week</option>
                  <option value={30}>30 hours / week</option>
                </select>

                <button
                  type="button"
                  className={btnGhost}
                  disabled={savingPace || Boolean(profile && weeklyHours === profile.weekly_hours)}
                  onClick={handleSavePace}
                >
                  {savingPace ? "Saving…" : "Save Pace"}
                </button>
              </div>
            </div>

            {/* Notifications */}
            <div className="border-t border-line pt-4">
              <label className="text-sm font-medium">Notifications & Reminders</label>
              <p className="text-xs text-muted">Manage your milestone and progress reminder alerts</p>

              <div className="mt-3 space-y-3">
                <label className="flex cursor-pointer items-start gap-3 text-sm">
                  <input
                    type="checkbox"
                    checked={remindersEnabled}
                    onChange={handleReminderToggle}
                    className="mt-0.5 h-4 w-4 rounded border-line accent-accent"
                  />
                  <div>
                    <p className="font-medium">Roadmap milestone reminders</p>
                    <p className="text-xs text-muted">Receive in-app alerts when tasks in your weekly plan are due.</p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </Card>

        {/* 3. Data & Privacy Section */}
        <Card>
          <h2 className="text-base font-semibold">Data & Privacy</h2>
          <p className="mt-0.5 text-xs text-muted">How your data is handled, stored, and protected</p>

          <div className="mt-4 space-y-4 text-sm">
            <div className="rounded-lg bg-raised p-4">
              <p className="font-medium text-ink">Resume Privacy & Processing</p>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                Uploaded resume files are read in-memory to identify demonstrated skills and project evidence.
                Raw resume text is automatically purged upon analysis completion. The original file is never stored on disk,
                and your resume content is never used to train public AI models.
              </p>
            </div>

            <div className="rounded-lg bg-raised p-4">
              <p className="font-medium text-ink">Saved Information</p>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                We store your profile preferences, self-reported skills, calculated roadmap milestones, and mentor conversations
                privately in your account. You retain full control over your career data at all times.
              </p>
            </div>

            <div className="border-t border-line pt-4">
              <p className="font-medium text-ink">Resume Data Management</p>
              {resume ? (
                <div className="mt-2 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-surface p-3">
                  <div>
                    <p className="text-sm font-medium">{resume.filename}</p>
                    <p className="text-xs text-muted">
                      Analyzed on {new Date(resume.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link href="/resume-analyzer" className={btnGhost}>
                      View in Analyzer
                    </Link>
                    <button
                      type="button"
                      disabled={deletingResume}
                      onClick={handleDeleteResume}
                      className="inline-flex items-center justify-center rounded-lg border border-bad/30 bg-bad/10 px-3 py-1.5 text-xs font-medium text-bad transition hover:bg-bad/20 disabled:opacity-50"
                    >
                      {deletingResume ? "Deleting…" : "Delete Resume Analysis"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mt-2 flex items-center justify-between rounded-lg border border-line bg-surface p-3">
                  <p className="text-xs text-muted">No resume analysis currently stored in your account.</p>
                  <Link href="/resume-analyzer" className={btnGhost}>
                    Upload Resume
                  </Link>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* 4. Help & Support Section */}
        <Card>
          <h2 className="text-base font-semibold">Help & Support</h2>
          <p className="mt-0.5 text-xs text-muted">Guidance, methodology, and assistance</p>

          <div className="mt-4 space-y-4 text-sm leading-relaxed text-muted">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-line bg-raised p-3">
                <p className="font-medium text-ink">1. Objective Scoring</p>
                <p className="mt-1 text-xs">
                  Competency gaps are determined by standardized industry rubrics, ensuring unbiased evaluation.
                </p>
              </div>
              <div className="rounded-lg border border-line bg-raised p-3">
                <p className="font-medium text-ink">2. Adaptive Roadmap</p>
                <p className="mt-1 text-xs">
                  Your weekly learning milestones dynamically adjust as you mark tasks completed.
                </p>
              </div>
              <div className="rounded-lg border border-line bg-raised p-3">
                <p className="font-medium text-ink">3. AI Career Mentor</p>
                <p className="mt-1 text-xs">
                  Context-aware guidance ready to answer technical and career questions whenever you need help.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
              <p className="text-xs">
                Questions or feedback about your career trajectory?
              </p>
              <a
                href="mailto:support@careerpilot.ai"
                className={`${btnGhost} text-xs`}
              >
                Contact Support
              </a>
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}
