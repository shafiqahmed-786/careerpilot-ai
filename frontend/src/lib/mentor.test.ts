import { describe, expect, it } from "vitest";

import type { MentorMessage } from "./api";
import { applyExchange, canSend, dropPending, pendingUserMessage, providerLabel, splitDemoNote } from "./mentor";

const message = (id: string, role: "user" | "assistant"): MentorMessage => ({
  id,
  role,
  content: id,
  provider: role === "assistant" ? "demo" : null,
  notice: null,
  created_at: "2026-11-07T00:00:00Z",
});

describe("mentor message handling", () => {
  it("replaces the optimistic message with the saved exchange", () => {
    const pending = pendingUserMessage("hello");
    const next = applyExchange([message("a", "user"), pending], pending.id, {
      user_message: message("u1", "user"),
      assistant_message: message("m1", "assistant"),
    });
    expect(next.map((item) => item.id)).toEqual(["a", "u1", "m1"]);
  });

  it("drops the optimistic message when the request fails", () => {
    const pending = pendingUserMessage("hello");
    expect(dropPending([message("a", "user"), pending], pending.id)).toHaveLength(1);
  });

  it("labels the provider honestly", () => {
    expect(providerLabel("groq")).toBe("AI Mentor");
    expect(providerLabel("demo")).toBe("Guided Answer");
    expect(providerLabel(null)).toBe("Guided Answer");
  });

  it("splits the demo-mode note from the answer", () => {
    const parts = splitDemoNote("Do the next task.\n\n_Demo mode: this reply was assembled by a template._");
    expect(parts.body).toBe("Do the next task.");
    expect(parts.note).toContain("Demo mode");
    expect(splitDemoNote("Plain answer").note).toBeNull();
  });

  it("only allows sending real, bounded input", () => {
    expect(canSend("   ", false)).toBe(false);
    expect(canSend("hi", true)).toBe(false);
    expect(canSend("x".repeat(2001), false)).toBe(false);
    expect(canSend("What next?", false)).toBe(true);
  });
});
