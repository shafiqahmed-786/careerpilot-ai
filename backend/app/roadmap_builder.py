from app.gaps import GapScore, focus_skills
from app.schemas import ResourceDraft, TaskDraft


def build_tasks(
    role_title: str,
    gaps: list[GapScore],
    resources: list[ResourceDraft],
    timeline_weeks: int,
    weekly_hours: int,
) -> list[TaskDraft]:
    selected = focus_skills(gaps, timeline_weeks)
    by_skill: dict[str, list[ResourceDraft]] = {}
    for resource in resources:
        by_skill.setdefault(resource.skill, []).append(resource)

    weights = [1] * len(selected)
    remaining = timeline_weeks - len(selected)
    index = 0
    while remaining > 0:
        weights[index % len(weights)] += 1
        remaining -= 1
        index += 1

    hours = max(1, weekly_hours)
    tasks: list[TaskDraft] = []
    week = 1
    order = 0
    for skill_gap, span in zip(selected, weights, strict=True):
        skill_resources = by_skill.get(skill_gap.name, [])
        for offset in range(span):
            objective = (
                f"Week {week}: move {skill_gap.name} toward the {role_title} target "
                f"of {skill_gap.target_level} (you reported {skill_gap.self_reported_level})."
            )
            outcome = (
                f"You can explain {skill_gap.name} and complete a small exercise without copying a tutorial line by line."
            )
            if hours == 1:
                splits = [1]
            else:
                first = max(1, hours // 2)
                splits = [first, max(1, hours - first)]
            titles = [
                f"Study {skill_gap.name} with the linked material",
                f"Practice {skill_gap.name} on a small {role_title.lower()} task",
            ]
            details = [
                f"{skill_gap.why_it_matters} Read the linked material and write five bullets in your own words.",
                (
                    f"{skill_gap.recommendation} Build a small exercise that uses {skill_gap.name}. "
                    f"This is week {offset + 1} of {span} on this skill."
                ),
            ]
            criteria = [
                f"Notes in your own words cover the core idea of {skill_gap.name}, and you opened the linked resource.",
                f"The exercise runs, and you can point to where {skill_gap.name} is used.",
            ]
            for piece in range(len(splits)):
                tasks.append(
                    TaskDraft(
                        week_number=week,
                        objective=objective,
                        skills=[skill_gap.name],
                        title=titles[piece],
                        details=details[piece],
                        estimated_hours=splits[piece],
                        expected_outcome=outcome,
                        completion_criteria=criteria[piece],
                        resources=skill_resources,
                        sort_order=order,
                    )
                )
                order += 1
            week += 1
    return tasks
