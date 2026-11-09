export type Skill = { name: string; proficiency: number };

export type Profile = {
  id: string;
  full_name: string;
  education: string;
  experience_level: "student" | "fresh_graduate" | "junior";
  skills: Skill[];
  projects: string;
  target_career: string;
  weekly_hours: number;
  timeline_weeks: number;
};

export type Competency = {
  name: string;
  importance: number;
  target_level: number;
  self_reported_level: number;
  status: string;
  priority_score: number;
  why_it_matters: string;
  recommendation: string;
};

export type Resource = {
  id: string;
  skill: string;
  title: string;
  url: string;
  domain: string;
  snippet: string;
  relevance: string;
  provider: string;
};

export type Assessment = {
  id: string;
  created_at: string;
  target_career: string;
  normalized_role: string;
  summary: string;
  learn_first_reason: string;
  disclaimer: string;
  provider: string;
  rubric_version: string;
  competencies: Competency[];
  resources: Resource[];
};

export type TaskResource = { title: string; url: string; domain?: string; provider?: string };

export type Task = {
  id: string;
  week_number: number;
  objective: string;
  skills: string[];
  title: string;
  details: string;
  estimated_hours: number;
  expected_outcome: string;
  completion_criteria: string;
  resources: TaskResource[];
  status: string;
  notes: string;
  sort_order: number;
  completed_at: string | null;
};

export type Roadmap = {
  id: string;
  title: string;
  timeline_weeks: number;
  weekly_hours: number;
  overview: string;
  provider: string;
  source: string;
  milestones: { week: number; title: string }[];
  adapted_count: number;
  adaptation_note: string | null;
  completion_percent: number;
  tasks: Task[];
};

export type Job = {
  id: string;
  kind: string;
  status: string;
  error: string | null;
  rq_job_id?: string | null;
  assessment_id: string | null;
  roadmap_id: string | null;
  created_at: string;
};

export type ActivityDay = { date: string; count: number };

export type ResumeSummary = {
  id: string;
  status: string;
  provider: string | null;
  match_percent: number | null;
  skills_found: number;
  created_at: string;
};

export type Dashboard = {
  latest_job: Job | null;
  readiness_percent: number | null;
  skills_identified: number;
  critical_gaps: number;
  milestones_completed: number;
  milestones_total: number;
  streak_days: number;
  activity: ActivityDay[];
  competencies: Competency[];
  resume: ResumeSummary | null;
  profile: Profile | null;
  assessment: Assessment | null;
  roadmap: Roadmap | null;
  completion_percent: number;
  next_task: Task | null;
  recently_completed: Task[];
  top_gaps: Competency[];
  resources: Resource[];
};

export type MentorMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  provider: string | null;
  notice: string | null;
  created_at: string;
};

export type ConversationSummary = { id: string; title: string; created_at: string; updated_at: string };
export type ConversationDetail = ConversationSummary & { messages: MentorMessage[] };
export type MentorStatus = {
  mode: "groq" | "demo" | string;
  model: string | null;
  has_profile: boolean;
  has_roadmap: boolean;
  has_resume: boolean;
};

export type SkillEvidence = {
  name: string;
  category: string;
  evidence_level: "demonstrated" | "listed" | "inferred";
  evidence: string[];
  usage?: string;
  confidence: "high" | "medium" | "low";
};

export type ResumeAnalysisData = {
  overview: string;
  education: string[];
  experience: string[];
  projects: { name: string; summary: string; technologies: string[] }[];
  skills: SkillEvidence[];
  achievements: string[];
  strengths: string[];
  improvements: string[];
  potential_gaps: string[];
  recommended_projects: string[];
};

export type ResumeComparison = {
  target_role: string;
  evidence_coverage_percent: number;
  formula: string;
  summary: string;
  competencies: {
    name: string;
    importance: number;
    status: "demonstrated" | "listed" | "inferred" | "missing";
    evidence: string[];
    why_it_matters: string;
  }[];
  priorities: string[];
  recommended_projects: string[];
};

export type ResumeResult = {
  id: string;
  filename: string;
  status: string;
  provider: string | null;
  notice: string | null;
  error: string | null;
  created_at: string;
  analysis: ResumeAnalysisData | null;
  comparison: ResumeComparison | null;
};

const TOKEN_KEY = "careerpilot_token";
const AUTH_PATHS = ["/api/v1/auth/login", "/api/v1/auth/signup"];

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function apiBase(): string {
  return (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

const FIELD_LABELS: Record<string, string> = {
  email: "Email",
  password: "Password",
  full_name: "Full name",
  target_career: "Target career",
  weekly_hours: "Weekly hours",
  timeline_weeks: "Timeline",
  experience_level: "Experience",
  skills: "Skills",
};

/** Turns a FastAPI `detail` (string or list of validation errors) into one readable sentence. */
export function formatErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (!Array.isArray(detail)) return null;
  const messages: string[] = [];
  for (const item of detail) {
    if (!item || typeof item !== "object") continue;
    const entry = item as { loc?: unknown[]; msg?: unknown };
    if (typeof entry.msg !== "string") continue;
    const message = entry.msg.replace(/^Value error,\s*/, "");
    const field = (entry.loc || []).filter((part): part is string => typeof part === "string" && part !== "body");
    const key = field[0] ?? "";
    const label = FIELD_LABELS[key] ?? key;
    messages.push(label && !message.toLowerCase().startsWith(label.toLowerCase()) ? `${label}: ${message}` : message);
  }
  return messages.length ? messages.join(". ") : null;
}

export function fallbackMessage(status: number): string {
  if (status === 401) return "Your session is not valid. Please sign in again.";
  if (status === 403) return "You do not have access to that.";
  if (status === 404) return "That item was not found.";
  if (status === 429) return "Too many requests. Wait a moment and try again.";
  if (status >= 500) return `The server hit an error (HTTP ${status}). Check the API logs.`;
  return `Request failed (HTTP ${status}).`;
}

export function networkMessage(base: string): string {
  return (
    `Cannot reach the CareerPilot API at ${base}. Check that the backend is running ` +
    "(GET /api/v1/health), that NEXT_PUBLIC_API_URL points to it, and that CORS_ORIGINS includes this site."
  );
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${apiBase()}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(networkMessage(apiBase()), 0);
  }

  const text = await response.text();
  let data: unknown = null;
  let parsed = true;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      parsed = false;
    }
  }

  if (!response.ok) {
    if (response.status === 401 && token && !AUTH_PATHS.includes(path)) {
      clearToken();
      if (typeof window !== "undefined") window.location.assign("/login?expired=1");
    }
    const detail = parsed && data && typeof data === "object" ? (data as { detail?: unknown }).detail : null;
    throw new ApiError(formatErrorDetail(detail) ?? fallbackMessage(response.status), response.status);
  }
  if (!parsed) {
    throw new ApiError("The API returned an unexpected response. Is NEXT_PUBLIC_API_URL pointing at the CareerPilot API?", response.status);
  }
  return data as T;
}
