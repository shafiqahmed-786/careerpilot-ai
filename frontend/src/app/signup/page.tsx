"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ErrorNote, btnPrimary, inputClass } from "@/components/ui";
import { api, setToken } from "@/lib/api";
import { emailProblem, passwordProblem } from "@/lib/validation";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const problem = emailProblem(email) ?? passwordProblem(password);
    if (problem) {
      setError(problem);
      return;
    }
    setPending(true);
    try {
      const result = await api<{ access_token: string }>("/api/v1/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      setToken(result.access_token);
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5">
      <Link className="mb-8 flex items-center gap-2" href="/">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-sm font-bold text-[#0b0d14]">C</span>
        <span className="font-semibold">CareerPilot AI</span>
      </Link>
      <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
      <form className="mt-6 space-y-4" noValidate onSubmit={onSubmit}>
        <label className="block text-sm">
          Email
          <input autoComplete="email" className={`${inputClass} mt-1`} onChange={(e) => setEmail(e.target.value)} required type="email" value={email} />
        </label>
        <label className="block text-sm">
          Password
          <input autoComplete="new-password" className={`${inputClass} mt-1`} onChange={(e) => setPassword(e.target.value)} required type="password" value={password} />
          <span className="mt-1 block text-xs text-muted">At least 8 characters, at most 72 bytes.</span>
        </label>
        <ErrorNote message={error} />
        <button className={`${btnPrimary} w-full`} disabled={pending} type="submit">{pending ? "Creating account…" : "Create account"}</button>
      </form>
      <p className="mt-6 text-sm text-muted">Already registered? <Link className="text-accent" href="/login">Sign in</Link></p>
    </main>
  );
}
