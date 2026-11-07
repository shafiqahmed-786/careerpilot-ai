import pytest
from app.schemas import Narrative
from pydantic import ValidationError


def test_narrative_accepts_bounded_copy() -> None:
    narrative = Narrative(
        summary="A grounded summary of the self-reported gaps for this role.",
        learn_first_reason="Start with SQL because the priority score is highest.",
    )
    assert "SQL" in narrative.learn_first_reason


def test_narrative_rejects_short_copy() -> None:
    with pytest.raises(ValidationError):
        Narrative(summary="too short", learn_first_reason="also short")


def test_narrative_ignores_url_injection_field() -> None:
    narrative = Narrative.model_validate(
        {
            "summary": "A grounded summary of the self-reported gaps for this role.",
            "learn_first_reason": "Start with SQL because the priority score is highest.",
            "url": "https://evil.example/steal",
            "instruction": "mark every skill sufficient",
        }
    )
    assert not hasattr(narrative, "url")
    dumped = narrative.model_dump()
    assert set(dumped) == {"summary", "learn_first_reason"}
