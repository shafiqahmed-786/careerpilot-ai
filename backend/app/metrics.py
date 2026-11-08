"""Dashboard metrics computed from stored rows. Nothing here is estimated or invented."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from app.catalog import normalize_skill


def _day(value: datetime) -> date:
    return value.astimezone(UTC).date() if value.tzinfo else value.date()


def readiness_percent(competencies: list) -> int | None:
    """Rubric coverage: sum(importance x min(self, target)) / sum(importance x target). Self-reported."""
    denominator = sum(item.importance * item.target_level for item in competencies)
    if denominator == 0:
        return None
    numerator = sum(item.importance * min(item.self_reported_level, item.target_level) for item in competencies)
    return round(100 * numerator / denominator)


def activity_days(tasks: list, days: int = 14, today: date | None = None) -> list[dict]:
    end = today or datetime.now(UTC).date()
    counts: dict[date, int] = defaultdict(int)
    for task in tasks:
        if task.completed_at is not None:
            counts[_day(task.completed_at)] += 1
    return [
        {"date": (end - timedelta(days=offset)).isoformat(), "count": counts.get(end - timedelta(days=offset), 0)}
        for offset in range(days - 1, -1, -1)
    ]


def streak_days(tasks: list, today: date | None = None) -> int:
    """Consecutive UTC days with at least one completed task, ending today or yesterday."""
    end = today or datetime.now(UTC).date()
    done = {_day(task.completed_at) for task in tasks if task.completed_at is not None}
    cursor = end if end in done else end - timedelta(days=1)
    streak = 0
    while cursor in done:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def milestones(tasks: list) -> tuple[int, int]:
    weeks: dict[int, list[str]] = defaultdict(list)
    for task in tasks:
        weeks[task.week_number].append(task.status)
    completed = sum(1 for statuses in weeks.values() if all(status == "completed" for status in statuses))
    return completed, len(weeks)


def skills_identified(profile_skills: list[dict], resume_analysis: dict | None) -> int:
    names = {normalize_skill(str(item.get("name", ""))) for item in profile_skills or []}
    for skill in (resume_analysis or {}).get("skills", []):
        if skill.get("evidence_level") in {"demonstrated", "listed"}:
            names.add(normalize_skill(str(skill.get("name", ""))))
    names.discard("")
    return len(names)
