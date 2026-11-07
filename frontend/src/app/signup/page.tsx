"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

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
    <main className="mx-auto max-w-md px-5 py-16">
      <h1 className="font-serif text-4xl">Create your account</h1>
      <p className="mt-2 text-muted">Passwords are hashed. Sessions use a signed token that expires.</p>
      <form className="mt-8 space-y-4" noValidate onSubmit={onSubmit}>
        <label className="block text-sm">
          Email
          <input
            autoComplete="email"
            className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            autoComplete="new-password"
            className="mt-1 w-full rounded-xl border border-line bg-card px-3 py-2"
            minLength={8}
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          <span className="mt-1 block text-xs text-muted">At least 8 characters, at most 72 bytes.</span>
        </label>
        {error ? (
          <p className="text-sm text-clay" role="alert">
            {error}
          </p>
        ) : null}
        <button className="w-full rounded-full bg-moss py-2.5 text-white disabled:opacity-60" disabled={pending} type="submit">
          {pending ? "Creating account…" : "Continue to profile"}
        </button>
      </form>
      <p className="mt-4 text-sm text-muted">
        Already registered? <Link className="text-moss" href="/login">Sign in</Link>
      </p>
    </main>
  );
}
