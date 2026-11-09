from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import metrics
from app.adaptive import MODES
from app.catalog import CATALOG, normalize_role, normalize_skill
from app.config import settings
from app.database import get_db
from app.models import Assessment, AssessmentJob, Profile, ResumeAnalysis, Roadmap, RoadmapTask, User
from app.queue import enqueue_assessment, enqueue_resume_analysis
from app.schemas import (
    ActivityDay,
    AdaptRequest,
    AssessmentResponse,
    CompetencyResponse,
    DashboardResponse,
    JobResponse,
    LoginRequest,
    ProfileRequest,
    ProfileResponse,
    ResourceResponse,
    ResumeSummary,
    RoadmapResponse,
    SignupRequest,
    TaskResponse,
    TaskUpdateRequest,
    TokenResponse,
    UserResponse,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/v1")


def _token(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.jwt_expire_minutes * 60,
    )


def _profile_out(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        full_name=profile.full_name,
        education=profile.education,
        experience_level=profile.experience_level,
        skills=profile.skills or [],
        projects=profile.projects,
        target_career=profile.target_career,
        weekly_hours=profile.weekly_hours,
        timeline_weeks=profile.timeline_weeks,
        updated_at=profile.updated_at,
    )


def _assessment_out(assessment: Assessment) -> AssessmentResponse:
    competencies = sorted(assessment.competencies, key=lambda item: item.sort_order)
    return AssessmentResponse(
        id=assessment.id,
        target_career=assessment.target_career,
        normalized_role=assessment.normalized_role,
        summary=assessment.summary,
        learn_first_reason=assessment.learn_first_reason,
        disclaimer=assessment.disclaimer,
        provider=assessment.provider,
        rubric_version=assessment.rubric_version,
        created_at=assessment.created_at,
        competencies=[
            CompetencyResponse(
                name=item.name,
                importance=item.importance,
                target_level=item.target_level,
                self_reported_level=item.self_reported_level,
                status=item.status,
                priority_score=item.priority_score,
                why_it_matters=item.why_it_matters,
                recommendation=item.recommendation,
            )
            for item in competencies
        ],
        resources=[
            ResourceResponse(
                id=item.id,
                skill=item.skill,
                title=item.title,
                url=item.url,
                domain=item.domain,
                snippet=item.snippet,
                relevance=item.relevance,
                provider=item.provider,
            )
            for item in assessment.resources
        ],
    )


def _task_out(task: RoadmapTask) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        week_number=task.week_number,
        objective=task.objective,
        skills=task.skills or [],
        title=task.title,
        details=task.details,
        estimated_hours=task.estimated_hours,
        expected_outcome=task.expected_outcome,
        completion_criteria=task.completion_criteria,
        resources=task.resources or [],
        status=task.status,
        notes=task.notes or "",
        sort_order=task.sort_order,
        completed_at=task.completed_at,
    )


def _completion(tasks: list[RoadmapTask]) -> int:
    if not tasks:
        return 0
    done = sum(1 for task in tasks if task.status == "completed")
    return round(done * 100 / len(tasks))


def _roadmap_out(roadmap: Roadmap) -> RoadmapResponse:
    tasks = sorted(roadmap.tasks, key=lambda item: item.sort_order)
    return RoadmapResponse(
        id=roadmap.id,
        title=roadmap.title,
        timeline_weeks=roadmap.timeline_weeks,
        weekly_hours=roadmap.weekly_hours,
        overview=roadmap.overview,
        provider=roadmap.provider,
        source=roadmap.source or "fallback",
        milestones=roadmap.milestones or [],
        adapted_count=roadmap.adapted_count or 0,
        adaptation_note=roadmap.adaptation_note,
        created_at=roadmap.created_at,
        completion_percent=_completion(tasks),
        tasks=[_task_out(task) for task in tasks],
    )


def _commit(db: Session) -> None:
    """Commit, rolling the session back first if the database rejects the write."""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _job_out(job: AssessmentJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        kind=job.kind or "assessment",
        status=job.status,
        error=job.error,
        rq_job_id=job.rq_job_id,
        assessment_id=job.assessment_id,
        roadmap_id=job.roadmap_id,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _latest_job(db: Session, user_id: str) -> AssessmentJob | None:
    return (
        db.query(AssessmentJob)
        .filter(AssessmentJob.user_id == user_id)
        .order_by(AssessmentJob.created_at.desc())
        .first()
    )


def _find_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def _latest_assessment(db: Session, user_id: str) -> Assessment | None:
    return (
        db.query(Assessment)
        .filter(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .first()
    )


def _latest_roadmap(db: Session, user_id: str) -> Roadmap | None:
    return (
        db.query(Roadmap)
        .filter(Roadmap.user_id == user_id)
        .order_by(Roadmap.created_at.desc())
        .first()
    )


@router.post("/auth/signup", response_model=TokenResponse, status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # SignupRequest has already validated and lower-cased the email and checked the password length.
    email = body.email
    if _find_user_by_email(db, email) is not None:
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(email=email, password_hash=hash_password(body.password), created_at=datetime.now(UTC))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Two concurrent signups can both pass the check above. The unique index decides the winner.
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with that email already exists") from exc
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return _token(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = body.email.strip().lower()
    user = _find_user_by_email(db, email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return _token(user)


@router.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/profile", response_model=ProfileResponse | None)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileResponse | None:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile is None:
        return None
    return _profile_out(profile)


@router.put("/profile", response_model=ProfileResponse)
def save_profile(
    body: ProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    if body.timeline_weeks not in {4, 8, 12}:
        raise HTTPException(status_code=422, detail="Timeline must be 4, 8, or 12 weeks")
    skills = []
    seen: set[str] = set()
    for skill in body.skills:
        key = skill.name.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        skills.append({"name": skill.name.strip(), "proficiency": skill.proficiency})
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    now = datetime.now(UTC)
    if profile is None:
        profile = Profile(user_id=user.id, updated_at=now)
        db.add(profile)
    profile.full_name = body.full_name.strip()
    profile.education = body.education.strip()
    profile.experience_level = body.experience_level
    profile.skills = skills
    profile.projects = body.projects.strip()
    profile.target_career = body.target_career.strip()
    profile.weekly_hours = body.weekly_hours
    profile.timeline_weeks = body.timeline_weeks
    profile.updated_at = now
    _commit(db)
    db.refresh(profile)
    return _profile_out(profile)


def create_and_enqueue(db: Session, user_id: str, kind: str, params: dict | None = None) -> AssessmentJob:
    """Insert a job row and put its id on the Redis queue. The worker does the actual work."""
    job = AssessmentJob(user_id=user_id, kind=kind, params=params, status="queued", created_at=datetime.now(UTC))
    db.add(job)
    _commit(db)
    db.refresh(job)
    try:
        if kind == "resume":
            job.rq_job_id = enqueue_resume_analysis(job.id)
        else:
            job.rq_job_id = enqueue_assessment(job.id)
        _commit(db)
    except Exception as exc:
        db.rollback()
        job.status = "failed"
        job.error = f"Could not enqueue background job: {exc}"[:2000]
        _commit(db)
        raise HTTPException(
            status_code=503,
            detail="The job queue is unavailable. Start Redis (docker compose up -d redis) and the RQ worker.",
        ) from exc
    db.refresh(job)
    return job


@router.post("/assessments", response_model=JobResponse, status_code=202)
def create_assessment(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile is None or not profile.target_career.strip():
        raise HTTPException(status_code=400, detail="Complete your career profile before requesting an assessment")
    return _job_out(create_and_enqueue(db, user.id, "assessment"))


@router.post("/roadmaps/current/adapt", response_model=JobResponse, status_code=202)
def adapt_roadmap(
    body: AdaptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Explicit action: re-plan the unstarted part of the roadmap from actual progress."""
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    roadmap = _latest_roadmap(db, user.id)
    if profile is None or roadmap is None:
        raise HTTPException(status_code=409, detail="Generate an assessment and roadmap before adapting it")
    if body.mode not in MODES:
        raise HTTPException(status_code=422, detail="Unknown adaptation mode")
    focus = (body.focus_skill or "").strip() or None
    if body.mode == "focus":
        role_key, _title = normalize_role(profile.target_career)
        names = {normalize_skill(item["name"]): item["name"] for item in CATALOG[role_key]["competencies"]}
        if focus is None or normalize_skill(focus) not in names:
            raise HTTPException(status_code=422, detail="Choose one of the skills for your target role")
        focus = names[normalize_skill(focus)]
    return _job_out(create_and_enqueue(db, user.id, "adapt", {"mode": body.mode, "focus_skill": focus}))


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobResponse:
    job = db.get(AssessmentJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_out(job)


@router.get("/assessments/latest", response_model=AssessmentResponse | None)
def latest_assessment(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResponse | None:
    assessment = _latest_assessment(db, user.id)
    if assessment is None:
        return None
    return _assessment_out(assessment)


@router.get("/roadmaps/current", response_model=RoadmapResponse | None)
def current_roadmap(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapResponse | None:
    roadmap = _latest_roadmap(db, user.id)
    if roadmap is None:
        return None
    return _roadmap_out(roadmap)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    body: TaskUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    task = db.get(RoadmapTask, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.status is not None:
        task.status = body.status
        task.completed_at = datetime.now(UTC) if body.status == "completed" else None
    if body.notes is not None:
        task.notes = body.notes
    _commit(db)
    db.refresh(task)
    return _task_out(task)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardResponse:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    assessment = _latest_assessment(db, user.id)
    roadmap = _latest_roadmap(db, user.id)
    job = _latest_job(db, user.id)
    tasks = sorted(roadmap.tasks, key=lambda item: item.sort_order) if roadmap else []
    next_task = next((task for task in tasks if task.status != "completed"), None)
    recent = sorted(
        (task for task in tasks if task.status == "completed" and task.completed_at is not None),
        key=lambda task: task.completed_at,
        reverse=True,
    )[:5]
    assessment_out = _assessment_out(assessment) if assessment else None
    top_gaps = []
    resources = []
    if assessment_out is not None:
        top_gaps = [item for item in assessment_out.competencies if item.status != "sufficient"][:4]
        resources = assessment_out.resources[:6]
    competencies = assessment_out.competencies if assessment_out else []
    resume_row = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )
    resume_summary = None
    if resume_row is not None:
        resume_summary = ResumeSummary(
            id=resume_row.id,
            status=resume_row.status,
            provider=resume_row.provider,
            match_percent=(resume_row.comparison or {}).get("evidence_coverage_percent"),
            skills_found=len((resume_row.analysis or {}).get("skills", [])),
            created_at=resume_row.created_at,
        )
    done_weeks, total_weeks = metrics.milestones(tasks)
    return DashboardResponse(
        readiness_percent=metrics.readiness_percent(competencies) if competencies else None,
        skills_identified=metrics.skills_identified(
            profile.skills if profile else [],
            resume_row.analysis if resume_row is not None and resume_row.status == "completed" else None,
        ),
        critical_gaps=sum(1 for item in competencies if item.status != "sufficient" and item.importance >= 4),
        milestones_completed=done_weeks,
        milestones_total=total_weeks,
        streak_days=metrics.streak_days(tasks),
        activity=[ActivityDay(**day) for day in metrics.activity_days(tasks)],
        competencies=competencies,
        resume=resume_summary,
        latest_job=_job_out(job) if job else None,
        profile=_profile_out(profile) if profile else None,
        assessment=assessment_out,
        roadmap=_roadmap_out(roadmap) if roadmap else None,
        completion_percent=_completion(tasks),
        next_task=_task_out(next_task) if next_task else None,
        recently_completed=[_task_out(task) for task in recent],
        top_gaps=top_gaps,
        resources=resources,
    )
