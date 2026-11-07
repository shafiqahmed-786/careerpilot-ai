"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearToken, getToken } from "@/lib/api";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/onboarding", label: "Profile" },
];

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    setSignedIn(Boolean(getToken()));
  }, [pathname]);

  return (
    <header className="border-b border-line bg-card/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4">
        <Link href={signedIn ? "/dashboard" : "/"} className="font-serif text-xl tracking-tight">
          CareerPilot AI
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {signedIn
            ? links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={pathname === link.href ? "text-moss" : "text-muted hover:text-ink"}
                >
                  {link.label}
                </Link>
              ))
            : null}
          {signedIn ? (
            <button
              className="rounded-full border border-line px-3 py-1 text-muted hover:text-ink"
              onClick={() => {
                clearToken();
                router.push("/");
              }}
              type="button"
            >
              Sign out
            </button>
          ) : (
            <Link href="/login" className="rounded-full bg-moss px-3 py-1 text-white">
              Sign in
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
