"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge, Card, ErrorNote, PageHeader, PageSkeleton, btnGhost } from "@/components/ui";
import { api, apiBase, clearToken } from "@/lib/api";

type Ready = { status: string; database: boolean; migrations: boolean; redis: boolean; llm: string; search: string };

export default function SettingsPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [ready, setReady] = useState<Ready | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api<{ email: string }>("/api/v1/auth/me"), api<Ready>("/api/v1/health/ready")])
      .then(([me, status]) => { setEmail(me.email); setReady(status); })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (!ready && !error) return <PageSkeleton />;
  const tone = (ok: boolean) => (ok ? "good" : "bad");
  return (
    <>
      <PageHeader title="Settings" subtitle="Account and system status." />
      <div className="max-w-2xl space-y-4">
        <ErrorNote message={error} />
        <Card>
          <h2 className="text-sm font-medium">Account</h2>
          <p className="mt-2 text-sm text-muted">{email}</p>
          <div className="mt-4 flex gap-3">
            <Link className={btnGhost} href="/onboarding">Edit career profile</Link>
            <button className={btnGhost} onClick={() => { clearToken(); router.push("/login"); }} type="button">Sign out</button>
          </div>
        </Card>
        {ready ? (
          <Card>
            <h2 className="text-sm font-medium">System status</h2>
            <ul className="mt-3 space-y-2 text-sm">
              <li className="flex justify-between"><span>Database</span><Badge tone={tone(ready.database)}>{ready.database ? "connected" : "down"}</Badge></li>
              <li className="flex justify-between"><span>Migrations</span><Badge tone={tone(ready.migrations)}>{ready.migrations ? "applied" : "missing"}</Badge></li>
              <li className="flex justify-between"><span>Redis queue</span><Badge tone={tone(ready.redis)}>{ready.redis ? "connected" : "down"}</Badge></li>
              <li className="flex justify-between"><span>AI mentor, roadmap and resume analysis</span><Badge tone={ready.llm === "openai" ? "accent" : "warn"}>{ready.llm === "openai" ? "live OpenAI" : "demo mode"}</Badge></li>
              <li className="flex justify-between"><span>Resource search</span><Badge tone={ready.search === "tavily" ? "accent" : "warn"}>{ready.search === "tavily" ? "live Tavily" : "demo catalog"}</Badge></li>
            </ul>
            <p className="mt-3 text-xs text-muted">API: {apiBase()}. Add OPENAI_API_KEY and TAVILY_API_KEY to the backend .env to go live. A separate worker process must be running for assessments, roadmaps and resume analysis.</p>
          </Card>
        ) : null}
        <Card>
          <h2 className="text-sm font-medium">Privacy</h2>
          <p className="mt-2 text-sm text-muted">Resume files are read in memory and never stored. Only the extracted analysis is saved, and you can delete it from the Resume Analyzer. Chat history is private to your account.</p>
        </Card>
      </div>
    </>
  );
}
