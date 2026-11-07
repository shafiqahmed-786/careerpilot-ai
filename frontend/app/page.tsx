import Link from "next/link";

const steps = [
  { n: "01", title: "Profile", text: "Record your education, self-reported skills, and the role you want." },
  { n: "02", title: "Assessment", text: "A background job scores gaps with a written rubric. Levels stay self-reported." },
  { n: "03", title: "Resources", text: "Search finds current learning material, or a labelled demo catalog when no key is set." },
  { n: "04", title: "Roadmap", text: "A four, eight, or twelve week plan is saved, then progress comes from completed tasks." },
];

export default function HomePage() {
  return (
    <main>
      <section className="mx-auto grid max-w-6xl gap-10 px-5 py-16 md:grid-cols-[1.3fr_0.7fr] md:py-24">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.16em] text-moss">CareerPilot AI</p>
          <h1 className="mt-3 max-w-xl font-serif text-5xl leading-tight text-ink md:text-6xl">
            Your career goal. A personalized roadmap. Measurable progress.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">
            CareerPilot turns a target role and the skills you already claim into a research-backed
            study plan. It does not pretend a self-report is a certified assessment.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/signup" className="rounded-full bg-moss px-5 py-2.5 text-white">
              Create an account
            </Link>
            <Link href="/login" className="rounded-full border border-line bg-card px-5 py-2.5">
              Sign in
            </Link>
          </div>
        </div>
        <aside className="rounded-3xl border border-line bg-card p-6 shadow-sm">
          <p className="text-sm text-muted">Example planning result</p>
          <h2 className="mt-2 font-serif text-2xl">Backend Engineer</h2>
          <dl className="mt-5 space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <dt>SQL</dt>
              <dd className="rounded-full bg-[#f6e4dc] px-2 py-0.5 text-clay">Not reported</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Python</dt>
              <dd className="rounded-full bg-[#f3ead2] px-2 py-0.5 text-[#8a5a12]">Below target</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt>Git</dt>
              <dd className="rounded-full bg-[#e5f3ee] px-2 py-0.5 text-moss">Meets target</dd>
            </div>
          </dl>
          <p className="mt-5 text-sm leading-relaxed text-muted">
            Priority = importance × gap. A missing bar means the skill was not on the profile.
          </p>
        </aside>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-5 pb-20 md:grid-cols-4">
        {steps.map((step) => (
          <article key={step.n} className="rounded-2xl border border-line bg-card p-5">
            <p className="font-serif text-2xl text-moss">{step.n}</p>
            <h2 className="mt-2 font-medium">{step.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">{step.text}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
