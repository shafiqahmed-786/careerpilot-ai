"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { ErrorNote, btnPrimary, inputClass } from "@/components/ui";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("expired")) setError("Your session expired. Please sign in again.");
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const result = await api<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      setToken(result.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5">
      <div className="mb-8 flex items-center justify-between">
        <Link className="flex items-center gap-2" href="/">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-sm font-bold text-[#0b0d14]">C</span>
          <span className="font-semibold">CareerPilot AI</span>
        </Link>
        <ThemeToggle />
      </div>
      <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
      <form className="mt-6 space-y-4" noValidate onSubmit={onSubmit}>
        <label className="block text-sm">
          Email
          <input autoComplete="email" className={`${inputClass} mt-1`} onChange={(e) => setEmail(e.target.value)} required type="email" value={email} />
        </label>
        <label className="block text-sm">
          Password
          <input autoComplete="current-password" className={`${inputClass} mt-1`} onChange={(e) => setPassword(e.target.value)} required type="password" value={password} />
        </label>
        <ErrorNote message={error} />
        <button className={`${btnPrimary} w-full`} disabled={pending} type="submit">{pending ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="mt-6 text-sm text-muted">No account? <Link className="text-accent" href="/signup">Create one</Link></p>
    </main>
  );
}
