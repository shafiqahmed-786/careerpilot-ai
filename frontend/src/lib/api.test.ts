import { describe, expect, it } from "vitest";

import { fallbackMessage, formatErrorDetail, networkMessage } from "./api";
import { emailProblem, passwordProblem } from "./validation";

describe("formatErrorDetail", () => {
  it("returns plain string details unchanged", () => {
    expect(formatErrorDetail("An account with that email already exists")).toBe(
      "An account with that email already exists",
    );
  });

  it("flattens FastAPI validation errors", () => {
    const detail = [
      { loc: ["body", "email"], msg: "Value error, Enter a valid email address", type: "value_error" },
      { loc: ["body", "password"], msg: "String should have at least 8 characters", type: "string_too_short" },
    ];
    expect(formatErrorDetail(detail)).toBe(
      "Email: Enter a valid email address. Password: String should have at least 8 characters",
    );
  });

  it("returns null for unknown shapes", () => {
    expect(formatErrorDetail(undefined)).toBeNull();
    expect(formatErrorDetail([{ nope: true }])).toBeNull();
  });
});

describe("error messages", () => {
  it("explains server errors and unreachable APIs", () => {
    expect(fallbackMessage(500)).toContain("HTTP 500");
    expect(networkMessage("http://localhost:8000")).toContain("CORS_ORIGINS");
  });
});

describe("form validation", () => {
  it("rejects short, blank and over-72-byte passwords", () => {
    expect(passwordProblem("short")).not.toBeNull();
    expect(passwordProblem("          ")).not.toBeNull();
    expect(passwordProblem("é".repeat(40))).not.toBeNull();
    expect(passwordProblem("a".repeat(72))).toBeNull();
    expect(passwordProblem("password123")).toBeNull();
  });

  it("checks email shape", () => {
    expect(emailProblem("ada@example.com")).toBeNull();
    expect(emailProblem("ada@example")).not.toBeNull();
    expect(emailProblem("not-an-email")).not.toBeNull();
  });
});
