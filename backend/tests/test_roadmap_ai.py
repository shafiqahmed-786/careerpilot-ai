import copy
import json

import pytest
from app import llm
from app.catalog import CATALOG
from app.config import settings
from app.gaps import focus_skills, score_gaps
from app.roadmap_ai import AIRoadmap, generate_roadmap, validate_roadmap
from app.search import demo_resources
from tests.support import PROFILE, fake_llm_json

GAPS = score_gaps(CATALOG["backend engineer"]["competencies"], PROFILE["skills"])
FOCUS = [gap.name for gap in focus_skills(GAPS, 4)]
RESOURCES = [item for name in FOCUS for item in demo_resources(name, "Backend Engineer")]


def _args(**extra):
    base = {
        "role_title": "Backend Engineer",
        "gaps": GAPS,
        "resources": RESOURCES,
        "profile": PROFILE,
        "weeks": 4,
        "weekly_hours": 6,
    }
    base.update(extra)
    return base


def _payload() -> dict:
    messages = [
        {"role": "system", "content": "learning-plan writer"},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "weeks_to_plan": [1, 2, 3, 4],
                    "weekly_hours": 6,
                    "focus_skills": FOCUS,
                    "resources": [{"skill": r.skill, "title": r.title, "url": r.url} for r in RESOURCES],
                }
            ),
        },
    ]
    return fake_llm_json(messages)


def test_valid_ai_roadmap_is_accepted_and_urls_are_grounded(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.llm.chat_json", lambda *a, **k: _payload())
    result = generate_roadmap(**_args())
    assert result.source == "ai"
    assert result.provider == "groq"
    assert [task.week_number for task in result.tasks] == [1, 2, 3, 4]
    allowed = {item.url for item in RESOURCES}
    assert all(res.url in allowed for task in result.tasks for res in task.resources)
    assert result.milestones[0]["week"] == 1


def test_invalid_output_falls_back_to_the_deterministic_builder(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.llm.chat_json", lambda *a, **k: {"overview": "too short", "weeks": []})
    result = generate_roadmap(**_args())
    assert result.source == "fallback"
    assert result.provider == "demo"
    assert result.fallback_reason
    assert result.tasks


def test_llm_errors_fall_back(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    def boom(*_args, **_kwargs):
        raise llm.LLMError("timeout")

    monkeypatch.setattr("app.llm.chat_json", boom)
    assert generate_roadmap(**_args()).source == "fallback"


def test_without_a_key_no_llm_call_is_made(monkeypatch) -> None:
    monkeypatch.setattr(settings, "groq_api_key", None)

    def fail(*_args, **_kwargs):
        raise AssertionError("must not call the model")

    monkeypatch.setattr("app.llm.chat_json", fail)
    result = generate_roadmap(**_args())
    assert result.source == "fallback"
    assert result.fallback_reason is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["weeks"].pop(),  # missing a week
        lambda p: p["weeks"][0]["tasks"][0].update(estimated_hours=20),  # blows the hour budget
        lambda p: p["weeks"][0]["tasks"][0].update(skills=["Underwater Basket Weaving"]),
        lambda p: p["weeks"][0]["tasks"][0].update(title="Study stuff"),  # vague title
    ],
)
def test_validation_rejects_bad_plans(mutate) -> None:
    payload = copy.deepcopy(_payload())
    mutate(payload)
    with pytest.raises(ValueError):
        ai = AIRoadmap.model_validate(payload)
        validate_roadmap(
            ai,
            first_week=1,
            weeks=4,
            weekly_hours=6,
            allowed_skills=[gap.name for gap in GAPS],
            resources=RESOURCES,
            order_start=0,
        )
