import Link from "next/link";

const layers = [
  { n: "01", title: "Understand", text: "Profile, projects and resume are analyzed. Skills count as demonstrated only when your resume shows them used." },
  { n: "02", title: "Reason and plan", text: "A fixed rubric scores your gaps. An AI writes a weekly roadmap from those scores and verified learning links." },
  { n: "03", title: "Guide and adapt", text: "A mentor that knows your gaps and progress answers questions, and your plan is revised as you complete tasks." },
];

export default function HomePage() {
  return (
    <main>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <span className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-sm font-bold text-[#0b0d14]">C</span>
          <span className="font-semibold">CareerPilot AI</span>
        </span>
        <nav className="flex gap-3 text-sm">
          <Link className="rounded-lg px-3 py-1.5 text-muted hover:text-ink" href="/login">Sign in</Link>
          <Link className="rounded-lg bg-accent px-3 py-1.5 font-medium text-[#0b0d14]" href="/signup">Get started</Link>
        </nav>
      </header>
      <section className="mx-auto grid max-w-6xl gap-10 px-5 py-16 md:grid-cols-[1.2fr_0.8fr] md:py-24">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-accent">AI career intelligence</p>
          <h1 className="mt-3 max-w-xl text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
            Know where you stand. Know what to learn next.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">
            CareerPilot turns your target role, skills and resume into a personalized weekly roadmap, then keeps guiding you as you progress.
            Scores are rule-based and self-reported levels are never presented as verified ability.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/signup" className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-[#0b0d14] hover:brightness-110">Create an account</Link>
            <Link href="/login" className="rounded-lg border border-line bg-surface px-5 py-2.5 text-sm hover:border-accent/60">Sign in</Link>
          </div>
        </div>
        <aside className="rounded-xl border border-line bg-surface p-6">
          <p className="text-xs text-muted">Example assessment</p>
          <h2 className="mt-1 text-lg font-medium">Backend Engineer</h2>
          <dl className="mt-5 space-y-3 text-sm">
            {[["SQL", "Not reported", "text-bad border-bad/30 bg-bad/10"], ["Python", "Below target", "text-warn border-warn/30 bg-warn/10"], ["Git", "Meets target", "text-good border-good/30 bg-good/10"]].map(([n, l, c]) => (
              <div key={n} className="flex items-center justify-between"><dt>{n}</dt><dd className={`rounded-full border px-2 py-0.5 text-xs ${c}`}>{l}</dd></div>
            ))}
          </dl>
          <p className="mt-5 text-xs leading-relaxed text-muted">Priority = importance × gap, calculated in code. The AI explains and plans; it never invents the numbers.</p>
        </aside>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-5 pb-20 md:grid-cols-3">
        {layers.map((l) => (
          <article key={l.n} className="rounded-xl border border-line bg-surface p-5">
            <p className="text-sm text-accent">{l.n}</p>
            <h2 className="mt-2 font-medium">{l.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">{l.text}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
