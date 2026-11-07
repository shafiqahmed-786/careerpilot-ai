"""Assessment pipeline: profile -> gaps -> search -> narrative -> roadmap."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.ai import enrich_narrative
from app.catalog import CATALOG, DISCLAIMER, RUBRIC_VERSION, normalize_role
from app.gaps import score_gaps
from app.models import (
    Assessment,
    AssessmentJob,
    CompetencyResult,
    LearningResource,
    Profile,
    Roadmap,
    RoadmapTask,
)
from app.roadmap_builder import build_tasks
from app.search import discover_resources


def run_and_persist(db: Session, job: AssessmentJob, profile: Profile) -> tuple[Assessment, Roadmap]:
    role_key, role_title = normalize_role(profile.target_career)
    competencies = CATALOG[role_key]["competencies"]
    gaps = score_gaps(competencies, profile.skills or [])
    focus_names = [gap.name for gap in gaps if gap.status != "sufficient"][: max(1, profile.timeline_weeks // 2)]
    if not focus_names:
        focus_names = [gap.name for gap in gaps[:3]]

    resources = []
    for name in focus_names:
        resources.extend(discover_resources(name, role_title))

    narrative, provider = enrich_narrative(role_title, gaps, resources)
    tasks = build_tasks(role_title, gaps, resources, profile.timeline_weeks, profile.weekly_hours)
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
        overview=narrative.summary,
        provider=provider,
        created_at=now,
    )
    db.add(roadmap)
    db.flush()
    for task in tasks:
        db.add(
            RoadmapTask(
                roadmap_id=roadmap.id,
                user_id=job.user_id,
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
        )
    return assessment, roadmap
