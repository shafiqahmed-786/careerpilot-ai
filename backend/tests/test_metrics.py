from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from app.metrics import activity_days, milestones, readiness_percent, skills_identified, streak_days

TODAY = date(2026, 11, 7)


def _done(days_ago: int):
    stamp = datetime(2026, 11, 7, 12, tzinfo=UTC) - timedelta(days=days_ago)
    return SimpleNamespace(completed_at=stamp, week_number=1, status="completed")


def test_readiness_is_a_documented_formula() -> None:
    comps = [
        SimpleNamespace(importance=5, target_level=4, self_reported_level=2),
        SimpleNamespace(importance=3, target_level=3, self_reported_level=5),  # capped at target
    ]
    assert readiness_percent(comps) == round(100 * (5 * 2 + 3 * 3) / (5 * 4 + 3 * 3))
    assert readiness_percent([]) is None


def test_streak_only_counts_real_completions() -> None:
    assert streak_days([], today=TODAY) == 0
    assert streak_days([_done(0), _done(1), _done(2), _done(4)], today=TODAY) == 3
    assert streak_days([_done(1), _done(2)], today=TODAY) == 2  # yesterday still counts
    assert streak_days([_done(3)], today=TODAY) == 0


def test_activity_window() -> None:
    days = activity_days([_done(0), _done(0), _done(2)], days=7, today=TODAY)
    assert len(days) == 7 and days[-1] == {"date": "2026-11-07", "count": 2}
    assert days[-3]["count"] == 1


def test_milestones_and_skill_counts() -> None:
    tasks = [
        SimpleNamespace(week_number=1, status="completed"),
        SimpleNamespace(week_number=1, status="completed"),
        SimpleNamespace(week_number=2, status="pending"),
    ]
    assert milestones(tasks) == (1, 2)
    resume = {"skills": [{"name": "PostgreSQL", "evidence_level": "demonstrated"}, {"name": "Rust", "evidence_level": "inferred"}]}
    assert skills_identified([{"name": "SQL"}, {"name": "Python"}], resume) == 2  # PostgreSQL is SQL; inferred is ignored
