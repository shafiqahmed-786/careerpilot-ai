"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { api, clearToken, getToken } from "@/lib/api";
import { PageSkeleton } from "@/components/ui";

const NAV = [
  { href: "/dashboard", label: "Dashboard", d: "M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z" },
  { href: "/onboarding", label: "My Career Profile", d: "M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0" },
  { href: "/resume-analyzer", label: "Resume Analyzer", d: "M7 3h8l4 4v14H7zM14 3v5h5M10 13h6M10 17h6" },
  { href: "/assessment", label: "Skill Assessment", d: "M4 20V10M10 20V4M16 20v-8M22 20H2" },
  { href: "/roadmap", label: "Learning Roadmap", d: "M5 4a2 2 0 100 4 2 2 0 000-4zM19 16a2 2 0 100 4 2 2 0 000-4zM7 6h6a4 4 0 010 8h-2a4 4 0 000 8" },
  { href: "/mentor", label: "AI Career Mentor", d: "M4 5h16v11H9l-5 4z" },
  { href: "/settings", label: "Settings", d: "M12 15a3 3 0 100-6 3 3 0 000 6zM19 12l2-1-2-4-2 1-2-1V5h-4v2l-2 1-2-1-2 4 2 1v2l-2 1 2 4 2-1 2 1v2h4v-2l2-1 2 1 2-4-2-1z" },
];

function Icon({ d }: { d: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<{ email: string }>("/api/v1/auth/me")
      .then((me) => setEmail(me.email))
      .catch(() => undefined);
  }, [router]);

  useEffect(() => setOpen(false), [pathname]);

  function logout() {
    clearToken();
    router.push("/login");
  }

  const nav = (
    <nav className="flex-1 space-y-0.5 px-3" aria-label="Main">
      {NAV.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
              active ? "bg-accent/10 text-accent" : "text-muted hover:bg-raised hover:text-ink"
            }`}
          >
            <Icon d={item.d} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  const sidebar = (
    <div className="flex h-full flex-col">
      <Link href="/dashboard" className="flex items-center gap-2 px-6 py-5">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-sm font-bold text-[#0b0d14]">C</span>
        <span className="font-semibold tracking-tight">CareerPilot AI</span>
      </Link>
      {nav}
      <div className="border-t border-line p-4">
        <p className="truncate text-sm" title={email ?? ""}>
          {email ?? "…"}
        </p>
        <button className="mt-2 text-xs text-muted hover:text-ink" onClick={logout} type="button">
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen md:pl-64">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-line bg-surface md:block">{sidebar}</aside>
      <div className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-paper/90 px-4 py-3 backdrop-blur md:hidden">
        <span className="font-semibold">CareerPilot AI</span>
        <button className="rounded-lg border border-line px-3 py-1 text-sm" onClick={() => setOpen((v) => !v)} type="button" aria-expanded={open}>
          Menu
        </button>
      </div>
      {open ? (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true">
          <button className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} aria-label="Close menu" type="button" />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-line bg-surface">{sidebar}</aside>
        </div>
      ) : null}
      <main key={pathname} className="mx-auto max-w-6xl animate-fade-in px-4 py-8 md:px-8">
        {email === null && !getToken() ? <PageSkeleton /> : children}
      </main>
    </div>
  );
}
