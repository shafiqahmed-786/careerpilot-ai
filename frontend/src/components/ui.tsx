import type { ReactNode } from "react";

export const inputClass =
  "w-full rounded-lg border border-line bg-raised px-3 py-2 text-sm text-ink placeholder:text-muted focus:border-accent focus:outline-none";
export const btnPrimary =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-[#0b0d14] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50";
export const btnGhost =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-line bg-raised px-3 py-1.5 text-sm text-ink transition hover:border-accent/60 disabled:cursor-not-allowed disabled:opacity-50";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-xl border border-line bg-surface p-5 ${className}`}>{children}</section>;
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-2xl text-sm text-muted">{subtitle}</p> : null}
      </div>
      {actions}
    </header>
  );
}

const TONES: Record<string, string> = {
  good: "bg-good/10 text-good border-good/30",
  warn: "bg-warn/10 text-warn border-warn/30",
  bad: "bg-bad/10 text-bad border-bad/30",
  accent: "bg-accent/10 text-accent border-accent/30",
  neutral: "bg-raised text-muted border-line",
};

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: keyof typeof TONES }) {
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${TONES[tone]}`}>{children}</span>;
}

export function AiBadge({ live, label }: { live: boolean; label?: string }) {
  return <Badge tone={live ? "accent" : "warn"}>{label ?? (live ? "Live AI" : "Demo mode")}</Badge>;
}

export function ProgressBar({ value, tone = "accent" }: { value: number; tone?: "accent" | "good" | "warn" }) {
  const color = tone === "good" ? "bg-good" : tone === "warn" ? "bg-warn" : "bg-accent";
  return (
    <div className="h-1.5 w-full rounded-full bg-raised" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <div className={`h-1.5 rounded-full transition-all duration-500 ${color}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Skeleton({ className = "h-4 w-full" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function PageSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}

export function EmptyState({ title, text, action }: { title: string; text: string; action?: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-line bg-surface px-6 py-12 text-center">
      <h2 className="text-lg font-medium">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted">{text}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  if (!message) return null;
  return (
    <p className="rounded-lg border border-bad/30 bg-bad/10 px-3 py-2 text-sm text-bad" role="alert">
      {message}
    </p>
  );
}

export function Spinner() {
  return <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden />;
}

export function Ring({ value, label, size = 112 }: { value: number | null; label?: string; size?: number }) {
  const r = (size - 12) / 2;
  const c = 2 * Math.PI * r;
  const pct = value ?? 0;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#232833" strokeWidth={8} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="#7c8bff"
          strokeWidth={8}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c - (c * pct) / 100}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-semibold">{value === null ? "—" : `${value}%`}</div>
        {label ? <div className="text-[10px] uppercase tracking-wide text-muted">{label}</div> : null}
      </div>
    </div>
  );
}
