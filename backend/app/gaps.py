"""Skill-gap scoring.

Rubric (importance-x-gap-v1):
- importance: 1-5, how much the competency matters for the target role.
- target_level: 1-5, the self-study target on this roadmap, not a certified bar.
- self_reported_level: 0-5, copied from the user profile. 0 means not reported.
- gap = max(0, target_level - self_reported_level)
- priority_score = importance * gap
- missing: self_reported_level == 0 and target_level > 0
- improve: 0 < self_reported_level < target_level
- sufficient: self_reported_level >= target_level

Scores compare a self-report with the rubric. They do not verify skill.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.catalog import normalize_skill


class GapScore(BaseModel):
    name: str
    importance: int = Field(ge=1, le=5)
    target_level: int = Field(ge=1, le=5)
    self_reported_level: int = Field(ge=0, le=5)
    status: str
    priority_score: int = Field(ge=0)
    why_it_matters: str
    recommendation: str


def self_level_map(skills: list[dict]) -> dict[str, int]:
    levels: dict[str, int] = {}
    for item in skills:
        name = normalize_skill(str(item.get("name", "")))
        if not name:
            continue
        level = int(item.get("proficiency", 0))
        level = max(0, min(5, level))
        levels[name] = max(levels.get(name, 0), level)
    return levels


def score_gaps(competencies: list[dict], skills: list[dict]) -> list[GapScore]:
    reported = self_level_map(skills)
    scored: list[GapScore] = []
    for item in competencies:
        name = item["name"]
        self_level = reported.get(normalize_skill(name), 0)
        target = int(item["target_level"])
        importance = int(item["importance"])
        gap = max(0, target - self_level)
        if self_level == 0:
            status = "missing"
            recommendation = (
                f"Start {name} from the fundamentals. It is not in your self-reported skills."
            )
        elif self_level < target:
            status = "improve"
            recommendation = (
                f"Raise {name} from a self-reported {self_level} toward {target}. "
                "This compares your entry with the roadmap target, and it is not a verified score."
            )
        else:
            status = "sufficient"
            recommendation = (
                f"Your self-reported level for {name} meets this roadmap target. Keep practicing it in context."
            )
        scored.append(
            GapScore(
                name=name,
                importance=importance,
                target_level=target,
                self_reported_level=self_level,
                status=status,
                priority_score=importance * gap,
                why_it_matters=item["why"],
                recommendation=recommendation,
            )
        )
    scored.sort(key=lambda gap: (-gap.priority_score, -gap.importance, gap.name))
    return scored


def focus_skills(gaps: list[GapScore], timeline_weeks: int) -> list[GapScore]:
    actionable = [gap for gap in gaps if gap.status != "sufficient"]
    if not actionable:
        actionable = list(gaps)
    count = min(len(actionable), max(1, timeline_weeks // 2))
    return actionable[:count]
