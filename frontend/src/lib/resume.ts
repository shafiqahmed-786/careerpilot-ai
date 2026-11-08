import type { SkillEvidence } from "@/lib/api";

export const MAX_RESUME_BYTES = 5 * 1024 * 1024;

export function validateResumeFile(file: { name: string; size: number }): string | null {
  const name = file.name.toLowerCase();
  if (!name.endsWith(".pdf") && !name.endsWith(".docx")) return "Upload a PDF or DOCX file.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_RESUME_BYTES) return "The file is larger than 5 MB.";
  return null;
}

export function evidenceLabel(level: string): string {
  if (level === "demonstrated") return "Demonstrated";
  if (level === "listed") return "Listed, no evidence";
  if (level === "inferred") return "Inferred, low confidence";
  return "Not found";
}

export function groupSkills(skills: SkillEvidence[]): Record<"demonstrated" | "listed" | "inferred", SkillEvidence[]> {
  const groups: Record<"demonstrated" | "listed" | "inferred", SkillEvidence[]> = {
    demonstrated: [],
    listed: [],
    inferred: [],
  };
  for (const skill of skills) groups[skill.evidence_level].push(skill);
  return groups;
}

export function categoriesOf(skills: SkillEvidence[]): string[] {
  return Array.from(new Set(skills.map((skill) => skill.category || "Other"))).sort();
}
