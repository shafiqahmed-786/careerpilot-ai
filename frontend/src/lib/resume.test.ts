import { describe, expect, it } from "vitest";

import type { SkillEvidence } from "./api";
import { categoriesOf, evidenceLabel, groupSkills, validateResumeFile } from "./resume";

const skill = (name: string, level: SkillEvidence["evidence_level"], category = "Languages"): SkillEvidence => ({
  name,
  category,
  evidence_level: level,
  evidence: [],
  confidence: "medium",
});

describe("resume upload state", () => {
  it("accepts PDF and DOCX within the size limit", () => {
    expect(validateResumeFile({ name: "CV.PDF", size: 1000 })).toBeNull();
    expect(validateResumeFile({ name: "cv.docx", size: 5 * 1024 * 1024 })).toBeNull();
  });

  it("rejects other types, empty files and oversized files", () => {
    expect(validateResumeFile({ name: "cv.txt", size: 10 })).toMatch(/PDF or DOCX/);
    expect(validateResumeFile({ name: "cv.pdf", size: 0 })).toMatch(/empty/);
    expect(validateResumeFile({ name: "cv.pdf", size: 5 * 1024 * 1024 + 1 })).toMatch(/5 MB/);
  });

  it("groups skills by how well they are supported", () => {
    const groups = groupSkills([skill("Python", "demonstrated"), skill("Docker", "listed"), skill("Rust", "inferred")]);
    expect(groups.demonstrated.map((s) => s.name)).toEqual(["Python"]);
    expect(groups.listed).toHaveLength(1);
    expect(groups.inferred).toHaveLength(1);
    expect(evidenceLabel("listed")).toContain("no evidence");
    expect(categoriesOf([skill("A", "listed", "Tools"), skill("B", "listed", "Languages"), skill("C", "listed", "Tools")])).toEqual([
      "Languages",
      "Tools",
    ]);
  });
});
