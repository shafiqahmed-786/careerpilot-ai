import type { ActivityDay, Competency } from "@/lib/api";

export function SkillBars({ items }: { items: Competency[] }) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.name}>
          <div className="mb-1 flex justify-between text-xs">
            <span>{item.name}</span>
            <span className="text-muted">
              {item.self_reported_level} / target {item.target_level}
            </span>
          </div>
          <div className="relative h-2 rounded-full bg-raised">
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-accent transition-all duration-700"
              style={{ width: `${(item.self_reported_level / 5) * 100}%` }}
            />
            <div className="absolute -top-0.5 h-3 w-0.5 bg-warn" style={{ left: `${(item.target_level / 5) * 100}%` }} title="Roadmap target" />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function ActivityBars({ days }: { days: ActivityDay[] }) {
  const max = Math.max(1, ...days.map((day) => day.count));
  return (
    <div className="flex h-24 items-end gap-1" aria-label="Tasks completed per day, last 14 days">
      {days.map((day) => (
        <div key={day.date} className="group flex flex-1 flex-col items-center justify-end" title={`${day.date}: ${day.count} completed`}>
          <div
            className={`w-full rounded-sm transition-all ${day.count ? "bg-accent" : "bg-raised"}`}
            style={{ height: `${day.count ? 12 + (day.count / max) * 80 : 6}%` }}
          />
        </div>
      ))}
    </div>
  );
}
