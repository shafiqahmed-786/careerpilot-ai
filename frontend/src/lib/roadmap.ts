import type { Task } from "@/lib/api";

export type WeekGroup = {
  week: number;
  objective: string;
  tasks: Task[];
  completed: number;
  total: number;
  percent: number;
  hours: number;
};

export function groupByWeek(tasks: Task[]): WeekGroup[] {
  const weeks = new Map<number, Task[]>();
  for (const task of [...tasks].sort((a, b) => a.sort_order - b.sort_order)) {
    weeks.set(task.week_number, [...(weeks.get(task.week_number) ?? []), task]);
  }
  return Array.from(weeks.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([week, items]) => {
      const completed = items.filter((task) => task.status === "completed").length;
      return {
        week,
        objective: items[0].objective,
        tasks: items,
        completed,
        total: items.length,
        percent: Math.round((completed * 100) / items.length),
        hours: items.reduce((sum, task) => sum + task.estimated_hours, 0),
      };
    });
}

/** The first week that still has unfinished work. */
export function currentWeek(groups: WeekGroup[]): number | null {
  return groups.find((group) => group.completed < group.total)?.week ?? null;
}

export function nextTaskId(tasks: Task[]): string | null {
  return [...tasks].sort((a, b) => a.sort_order - b.sort_order).find((task) => task.status !== "completed")?.id ?? null;
}

export function replaceTask(tasks: Task[], updated: Task): Task[] {
  return tasks.map((task) => (task.id === updated.id ? updated : task));
}

export function sourceLabel(source: string): string {
  return source === "ai" ? "AI-generated plan" : "Template plan (deterministic fallback)";
}
