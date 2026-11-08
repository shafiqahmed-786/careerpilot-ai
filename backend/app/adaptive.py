"""Progress-aware re-planning helpers (deterministic).

Completed work is treated as evidence: every ADAPT_HOURS_PER_LEVEL completed study hours on a skill
raise its planning level by one, capped at the roadmap target. This adjusts priorities for the next
plan only. It never edits the stored assessment and is not a verified skill measurement.
"""

from __future__ import annotations

from app.catalog import normalize_skill
from app.gaps import GapScore
from app.models import RoadmapTask

ADAPT_HOURS_PER_LEVEL = 6
MODES = {"revise", "intensive", "lighter", "focus"}


def adjusted_hours(weekly_hours: int, mode: str) -> int:
    if mode == "intensive":
        return min(40, -(-weekly_hours * 3 // 2))
    if mode == "lighter":
        return max(1, (weekly_hours * 6) // 10)
    return weekly_hours


def completed_hours_by_skill(tasks: list[RoadmapTask]) -> dict[str, int]:
    hours: dict[str, int] = {}
    for task in tasks:
        if task.status != "completed":
            continue
        for skill in task.skills or []:
            key = normalize_skill(str(skill))
            hours[key] = hours.get(key, 0) + int(task.estimated_hours)
    return hours


def adjust_gaps_for_progress(gaps: list[GapScore], tasks: list[RoadmapTask]) -> list[GapScore]:
    hours = completed_hours_by_skill(tasks)
    adjusted: list[GapScore] = []
    for gap in gaps:
        gained = hours.get(normalize_skill(gap.name), 0) // ADAPT_HOURS_PER_LEVEL
        level = min(gap.target_level, gap.self_reported_level + gained)
        if level == 0:
            status = "missing"
        elif level < gap.target_level:
            status = "improve"
        else:
            status = "sufficient"
        adjusted.append(
            gap.model_copy(
                update={
                    "self_reported_level": level,
                    "status": status,
                    "priority_score": gap.importance * max(0, gap.target_level - level),
                }
            )
        )
    adjusted.sort(key=lambda gap: (-gap.priority_score, -gap.importance, gap.name))
    return adjusted


def put_focus_first(gaps: list[GapScore], focus_skill: str | None) -> list[GapScore]:
    if not focus_skill:
        return gaps
    key = normalize_skill(focus_skill)
    chosen = [gap for gap in gaps if normalize_skill(gap.name) == key]
    return chosen + [gap for gap in gaps if gap not in chosen]


def split_tasks(tasks: list[RoadmapTask]) -> dict[str, list[RoadmapTask]]:
    """completed / in_progress / pending / delayed (pending in a week before the latest completed week)."""
    ordered = sorted(tasks, key=lambda item: item.sort_order)
    completed = [t for t in ordered if t.status == "completed"]
    last_done = max((t.week_number for t in completed), default=0)
    pending = [t for t in ordered if t.status == "pending"]
    return {
        "completed": completed,
        "in_progress": [t for t in ordered if t.status == "in_progress"],
        "pending": pending,
        "delayed": [t for t in pending if t.week_number < last_done],
    }


def plan_window(tasks: list[RoadmapTask], timeline_weeks: int) -> tuple[int, int]:
    """First week and number of weeks the revised plan covers."""
    last_done = max((t.week_number for t in tasks if t.status == "completed"), default=0)
    first = min(last_done + 1, timeline_weeks)
    return first, timeline_weeks - first + 1
