import { describe, expect, it } from "vitest";

import type { Task } from "./api";
import { currentWeek, groupByWeek, nextTaskId, replaceTask, sourceLabel } from "./roadmap";

const task = (id: string, week: number, status: string, order: number, hours = 3): Task => ({
  id,
  week_number: week,
  objective: `Week ${week} objective`,
  skills: ["SQL"],
  title: id,
  details: "",
  estimated_hours: hours,
  expected_outcome: "",
  completion_criteria: "",
  resources: [],
  status,
  notes: "",
  sort_order: order,
  completed_at: null,
});

describe("roadmap helpers", () => {
  const tasks = [task("a", 1, "completed", 0), task("b", 1, "completed", 1), task("c", 2, "in_progress", 2), task("d", 2, "pending", 3)];

  it("groups tasks by week with progress", () => {
    const groups = groupByWeek(tasks);
    expect(groups.map((g) => [g.week, g.percent, g.hours])).toEqual([
      [1, 100, 6],
      [2, 0, 6],
    ]);
    expect(currentWeek(groups)).toBe(2);
  });

  it("finds the next unfinished task and updates one task in place", () => {
    expect(nextTaskId(tasks)).toBe("c");
    const updated = replaceTask(tasks, { ...tasks[2], status: "completed" });
    expect(nextTaskId(updated)).toBe("d");
    expect(updated[0]).toBe(tasks[0]);
  });

  it("labels the plan source", () => {
    expect(sourceLabel("ai")).toContain("AI-generated");
    expect(sourceLabel("fallback")).toContain("fallback");
  });
});
