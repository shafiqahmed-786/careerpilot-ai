import { describe, expect, it } from "vitest";

import { completionPercent, statusLabel } from "./progress";

describe("completionPercent", () => {
  it("is zero when there are no tasks", () => {
    expect(completionPercent(0, 0)).toBe(0);
  });

  it("rounds the share of completed tasks", () => {
    expect(completionPercent(1, 8)).toBe(13);
    expect(completionPercent(8, 8)).toBe(100);
  });
});

describe("statusLabel", () => {
  it("does not describe a self-report as a verified skill", () => {
    expect(statusLabel("missing")).toBe("Not reported");
    expect(statusLabel("sufficient")).toBe("Meets target");
  });
});
