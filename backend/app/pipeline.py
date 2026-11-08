"""Assessment pipeline: profile -> gaps -> search -> narrative -> roadmap."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.adaptive import (
    adjust_gaps_for_progress,
    adjusted_hours,
    completed_hours_by_skill,
    plan_window,
    put_focus_first,
    split_tasks,
)
from app.ai import enrich_narrative
from app.catalog import CATALOG, DISCLAIMER, RUBRIC_VERSION, normalize_role, normalize_skill
from app.gaps import focus_skills, score_gaps
from app.models import (
    Assessment,
    AssessmentJob,
    CompetencyResult,
    LearningResource,
    Profile,
    ResumeAnalysis,
    Roadmap,
    RoadmapTask,
)
from app.resume_analysis import evidence_summary
from app.roadmap_ai import generate_roadmap
from app.schemas import ResourceDraft, TaskDraft
from app.search import discover_resources


def latest_resume_evidence(db: Session, user_id: str) -> dict | None:
    row = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user_id, ResumeAnalysis.status == "completed")
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )
    return evidence_summary(row.analysis) if row else None


def _profile_dict(profile: Profile) -> dict:
    return {
        "experience_level": profile.experience_level,
        "education": profile.education,
        "projects": profile.projects,
    }


def _task_row(roadmap_id: str, user_id: str, task: TaskDraft) -> RoadmapTask:
    return RoadmapTask(
        roadmap_id=roadmap_id,
        user_id=user_id,
        week_number=task.week_number,
        objective=task.objective,
        skills=task.skills,
        title=task.title,
        details=task.details,
        estimated_hours=task.estimated_hours,
        expected_outcome=task.expected_outcome,
        completion_criteria=task.completion_criteria,
        resources=[item.model_dump() for item in task.resources],
        status="pending",
        notes="",
        sort_order=task.sort_order,
    )


def run_and_persist(db: Session, job: AssessmentJob, profile: Profile) -> tuple[Assessment, Roadmap]:
    role_key, role_title = normalize_role(profile.target_career)
    competencies = CATALOG[role_key]["competencies"]
    gaps = score_gaps(competencies, profile.skills or [])
    # The same focus list drives resource discovery and the roadmap, so every task has resources.
    focus_names = [gap.name for gap in focus_skills(gaps, profile.timeline_weeks)]

    resources = []
    for name in focus_names:
        resources.extend(discover_resources(name, role_title))

    narrative, provider = enrich_narrative(role_title, gaps, resources)
    # The LLM writes the plan text from the deterministic gaps and verified resources.
    # If its output fails validation the deterministic builder is used and the roadmap is labelled "fallback".
    plan = generate_roadmap(
        role_title=role_title,
        gaps=gaps,
        resources=resources,
        profile=_profile_dict(profile),
        weeks=profile.timeline_weeks,
        weekly_hours=profile.weekly_hours,
        resume=latest_resume_evidence(db, job.user_id),
    )
    tasks = plan.tasks
    now = datetime.now(UTC)

    assessment = Assessment(
        user_id=job.user_id,
        job_id=job.id,
        target_career=profile.target_career,
        normalized_role=role_title,
        summary=narrative.summary,
        learn_first_reason=narrative.learn_first_reason,
        disclaimer=DISCLAIMER,
        provider=provider,
        rubric_version=RUBRIC_VERSION,
        created_at=now,
    )
    db.add(assessment)
    db.flush()

    for index, gap in enumerate(gaps):
        db.add(
            CompetencyResult(
                assessment_id=assessment.id,
                user_id=job.user_id,
                name=gap.name,
                importance=gap.importance,
                target_level=gap.target_level,
                self_reported_level=gap.self_reported_level,
                status=gap.status,
                priority_score=gap.priority_score,
                why_it_matters=gap.why_it_matters,
                recommendation=gap.recommendation,
                sort_order=index,
            )
        )
    for resource in resources:
        db.add(
            LearningResource(
                assessment_id=assessment.id,
                user_id=job.user_id,
                skill=resource.skill,
                title=resource.title,
                url=resource.url,
                domain=resource.domain,
                snippet=resource.snippet,
                relevance=resource.relevance,
                provider=resource.provider,
            )
        )

    roadmap = Roadmap(
        user_id=job.user_id,
        assessment_id=assessment.id,
        title=f"{role_title} · {profile.timeline_weeks}-week plan",
        timeline_weeks=profile.timeline_weeks,
        weekly_hours=profile.weekly_hours,
        overview=plan.overview or narrative.summary,
        provider=plan.provider,
        source=plan.source,
        milestones=plan.milestones,
        created_at=now,
    )
    db.add(roadmap)
    db.flush()
    for task in tasks:
        db.add(_task_row(roadmap.id, job.user_id, task))
    return assessment, roadmap


def _stored_resources(db: Session, assessment_id: str) -> list[ResourceDraft]:
    rows = db.query(LearningResource).filter(LearningResource.assessment_id == assessment_id).all()
    return [
        ResourceDraft(
            skill=row.skill, title=row.title, url=row.url, domain=row.domain,
            snippet=row.snippet, relevance=row.relevance, provider=row.provider,
        )
        for row in rows
    ]


MODE_TEXT = {
    "revise": "Revise the plan using the progress evidence. Keep the same weekly hours.",
    "intensive": "The learner asked for a more intensive schedule. Use the larger weekly hour budget.",
    "lighter": "The learner asked for a lighter workload. Use the smaller weekly hour budget and fewer tasks.",
    "focus": "The learner asked to focus on one weak skill. Make it the main thread of every week.",
}


def run_adaptation(db: Session, job: AssessmentJob, profile: Profile) -> tuple[str, Roadmap]:
    """Replace the unstarted tasks of the current roadmap with a plan based on actual progress.

    Completed and in-progress tasks are kept untouched, so history is preserved.
    """
    roadmap = (
        db.query(Roadmap).filter(Roadmap.user_id == job.user_id).order_by(Roadmap.created_at.desc()).first()
    )
    if roadmap is None:
        raise ValueError("There is no roadmap to adapt. Generate an assessment first.")
    params = job.params or {}
    mode = params.get("mode") if params.get("mode") in MODE_TEXT else "revise"
    focus_skill = params.get("focus_skill") or None

    role_key, role_title = normalize_role(profile.target_career)
    base = score_gaps(CATALOG[role_key]["competencies"], profile.skills or [])
    existing = sorted(roadmap.tasks, key=lambda item: item.sort_order)
    groups = split_tasks(existing)
    gaps = put_focus_first(adjust_gaps_for_progress(base, existing), focus_skill if mode == "focus" else None)

    first_week, weeks = plan_window(existing, roadmap.timeline_weeks)
    hours = adjusted_hours(roadmap.weekly_hours, mode)
    focus_names = [gap.name for gap in focus_skills(gaps, weeks)]

    resources = _stored_resources(db, roadmap.assessment_id)
    have = {normalize_skill(item.skill) for item in resources}
    for name in focus_names:
        if normalize_skill(name) not in have:
            fresh = discover_resources(name, role_title)
            resources.extend(fresh)
            for item in fresh:
                db.add(
                    LearningResource(
                        assessment_id=roadmap.assessment_id, user_id=job.user_id, skill=item.skill,
                        title=item.title, url=item.url, domain=item.domain, snippet=item.snippet,
                        relevance=item.relevance, provider=item.provider,
                    )
                )

    def brief(rows: list[RoadmapTask]) -> list[dict]:
        return [{"title": t.title, "week": t.week_number, "skills": t.skills, "hours": t.estimated_hours} for t in rows[:12]]

    progress = {
        "mode": mode,
        "completed": brief(groups["completed"]),
        "in_progress": brief(groups["in_progress"]),
        "delayed_not_started": brief(groups["delayed"]),
        "completed_hours_by_skill": completed_hours_by_skill(existing),
    }
    order_start = max((t.sort_order for t in existing), default=-1) + 1
    plan = generate_roadmap(
        role_title=role_title,
        gaps=gaps,
        resources=resources,
        profile=_profile_dict(profile),
        weeks=weeks,
        first_week=first_week,
        weekly_hours=hours,
        order_start=order_start,
        resume=latest_resume_evidence(db, job.user_id),
        progress=progress,
        instruction=MODE_TEXT[mode],
    )

    removed = groups["pending"]
    for task in removed:
        db.delete(task)
    db.flush()
    for task in plan.tasks:
        db.add(_task_row(roadmap.id, job.user_id, task))

    kept_milestones = [m for m in (roadmap.milestones or []) if int(m.get("week", 0)) < first_week]
    roadmap.milestones = kept_milestones + plan.milestones
    roadmap.weekly_hours = hours
    roadmap.provider = plan.provider
    roadmap.source = plan.source
    if plan.overview:
        roadmap.overview = plan.overview
    roadmap.adapted_count = (roadmap.adapted_count or 0) + 1
    top_gaps = [f"{g.name} ({g.priority_score})" for g in gaps if g.status != "sufficient"][:3]
    top = ", ".join(top_gaps) or "none"
    roadmap.adaptation_note = (
        f"Mode: {mode}. Kept {len(groups['completed'])} completed and {len(groups['in_progress'])} in-progress tasks, "
        f"replaced {len(removed)} unstarted tasks. New plan: weeks {first_week}-{roadmap.timeline_weeks} at {hours}h/week "
        f"({'AI-generated' if plan.source == 'ai' else 'template fallback'}). "
        f"Progress-adjusted priorities: {top}."
    )
    return roadmap.assessment_id, roadmap
