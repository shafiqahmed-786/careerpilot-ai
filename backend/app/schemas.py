from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security import MAX_PASSWORD_BYTES


def normalize_email(value: str) -> str:
    """Validate syntax (no DNS lookup) and return the canonical lower-case address."""
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise ValueError("Enter a valid email address") from exc


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def _valid_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password is too long: at most {MAX_PASSWORD_BYTES} bytes in UTF-8 "
                "(emoji and non-Latin letters use several bytes each)"
            )
        if not value.strip():
            raise ValueError("Password cannot be only spaces")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: datetime


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    proficiency: int = Field(ge=0, le=5)


class ProfileRequest(BaseModel):
    full_name: str = Field(default="", max_length=120)
    education: str = Field(default="", max_length=500)
    experience_level: str = Field(pattern="^(student|fresh_graduate|junior)$")
    skills: list[SkillInput] = Field(default_factory=list, max_length=30)
    projects: str = Field(default="", max_length=4000)
    target_career: str = Field(min_length=2, max_length=120)
    weekly_hours: int = Field(ge=1, le=40)
    timeline_weeks: int = Field(description="4, 8, or 12")

    def timeline_ok(self) -> bool:
        return self.timeline_weeks in {4, 8, 12}


class ProfileResponse(ProfileRequest):
    id: str
    updated_at: datetime


class ResourceResponse(BaseModel):
    id: str
    skill: str
    title: str
    url: str
    domain: str
    snippet: str
    relevance: str
    provider: str


class CompetencyResponse(BaseModel):
    name: str
    importance: int
    target_level: int
    self_reported_level: int
    status: str
    priority_score: int
    why_it_matters: str
    recommendation: str


class AssessmentResponse(BaseModel):
    id: str
    target_career: str
    normalized_role: str
    summary: str
    learn_first_reason: str
    disclaimer: str
    provider: str
    rubric_version: str
    created_at: datetime
    competencies: list[CompetencyResponse]
    resources: list[ResourceResponse]


class TaskResponse(BaseModel):
    id: str
    week_number: int
    objective: str
    skills: list[str]
    title: str
    details: str
    estimated_hours: int
    expected_outcome: str
    completion_criteria: str
    resources: list[dict]
    status: str
    notes: str
    sort_order: int
    completed_at: datetime | None


class TaskUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(pending|in_progress|completed)$")
    notes: str | None = Field(default=None, max_length=2000)


class RoadmapResponse(BaseModel):
    id: str
    title: str
    timeline_weeks: int
    weekly_hours: int
    overview: str
    provider: str
    source: str = "fallback"
    milestones: list[dict] = Field(default_factory=list)
    adapted_count: int = 0
    adaptation_note: str | None = None
    created_at: datetime
    completion_percent: int
    tasks: list[TaskResponse]


class AdaptRequest(BaseModel):
    mode: str = Field(pattern="^(revise|intensive|lighter|focus)$")
    focus_skill: str | None = Field(default=None, max_length=80)


class JobResponse(BaseModel):
    id: str
    kind: str = "assessment"
    status: str
    error: str | None
    rq_job_id: str | None = None
    assessment_id: str | None
    roadmap_id: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ActivityDay(BaseModel):
    date: str
    count: int


class ResumeSummary(BaseModel):
    id: str
    status: str
    provider: str | None
    match_percent: int | None
    skills_found: int
    created_at: datetime


class DashboardResponse(BaseModel):
    latest_job: JobResponse | None = None
    readiness_percent: int | None = None
    skills_identified: int = 0
    critical_gaps: int = 0
    milestones_completed: int = 0
    milestones_total: int = 0
    streak_days: int = 0
    activity: list[ActivityDay] = Field(default_factory=list)
    competencies: list[CompetencyResponse] = Field(default_factory=list)
    resume: ResumeSummary | None = None
    profile: ProfileResponse | None
    assessment: AssessmentResponse | None
    roadmap: RoadmapResponse | None
    completion_percent: int
    next_task: TaskResponse | None
    recently_completed: list[TaskResponse]
    top_gaps: list[CompetencyResponse]
    resources: list[ResourceResponse]


class Narrative(BaseModel):
    """LLM copy only. Scores and URLs are never taken from this object."""

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(min_length=20, max_length=1200)
    learn_first_reason: str = Field(min_length=20, max_length=800)


class ResourceDraft(BaseModel):
    skill: str
    title: str
    url: str
    domain: str
    snippet: str
    relevance: str
    provider: str


class TaskDraft(BaseModel):
    week_number: int
    objective: str
    skills: list[str]
    title: str
    details: str
    estimated_hours: int
    expected_outcome: str
    completion_criteria: str
    resources: list[ResourceDraft]
    sort_order: int


class MentorMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    provider: str | None
    notice: str | None
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MentorMessageResponse]


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class MessageExchange(BaseModel):
    user_message: MentorMessageResponse
    assistant_message: MentorMessageResponse


class MentorStatus(BaseModel):
    mode: str
    model: str | None
    has_profile: bool
    has_roadmap: bool
    has_resume: bool


class ResumeResponse(BaseModel):
    id: str
    filename: str
    status: str
    provider: str | None
    notice: str | None
    error: str | None
    created_at: datetime
    analysis: dict | None
    comparison: dict | None


class ResumeUploadResponse(BaseModel):
    resume_id: str
    job: JobResponse
