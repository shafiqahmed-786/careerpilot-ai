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
  resources: { title: string; url: string; domain?: string; provider?: string }[];
  status: string;
  notes: string;
  sort_order: number;
};

export type Roadmap = {
  id: string;
  title: string;
  timeline_weeks: number;
  weekly_hours: number;
  overview: string;
  provider: string;
  completion_percent: number;
  tasks: Task[];
};

export type Job = {
  id: string;
  status: string;
  error: string | null;
  assessment_id: string | null;
  roadmap_id: string | null;
};

export type Dashboard = {
  profile: Profile | null;
  assessment: Assessment | null;
  roadmap: Roadmap | null;
  completion_percent: number;
  next_task: Task | null;
  recently_completed: Task[];
  top_gaps: Competency[];
  resources: Resource[];
};

const TOKEN_KEY = "careerpilot_token";

export function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${apiBase()}${path}`, { ...options, headers });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : "Request failed";
    throw new Error(message);
  }
  return data as T;
}
