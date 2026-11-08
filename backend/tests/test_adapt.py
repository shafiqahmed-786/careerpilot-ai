from types import SimpleNamespace

from app.adaptive import adjust_gaps_for_progress, adjusted_hours, plan_window, put_focus_first, split_tasks
from app.catalog import CATALOG
from app.gaps import score_gaps
from fastapi.testclient import TestClient
from tests.conftest import auth, bearer
from tests.support import PROFILE, run_worker, setup_roadmap


def _task(week, status, skills=("SQL",), hours=3, order=0):
    return SimpleNamespace(week_number=week, status=status, skills=list(skills), estimated_hours=hours, sort_order=order)


def test_hours_modes() -> None:
    assert adjusted_hours(6, "revise") == 6
    assert adjusted_hours(6, "intensive") == 9
    assert adjusted_hours(6, "lighter") == 3
    assert adjusted_hours(1, "lighter") == 1
    assert adjusted_hours(30, "intensive") == 40


def test_progress_adjusts_priorities_without_inventing_levels() -> None:
    gaps = score_gaps(CATALOG["backend engineer"]["competencies"], PROFILE["skills"])
    before = next(g for g in gaps if g.name == "SQL")
    done = [_task(1, "completed", ("SQL",), 6), _task(1, "completed", ("SQL",), 6)]
    after = next(g for g in adjust_gaps_for_progress(gaps, done) if g.name == "SQL")
    assert before.self_reported_level == 0
    assert after.self_reported_level == 2  # 12 completed hours // 6
    assert after.priority_score == before.importance * (before.target_level - 2)
    capped = adjust_gaps_for_progress(gaps, [_task(1, "completed", ("SQL",), 40)])
    assert next(g for g in capped if g.name == "SQL").status == "sufficient"


def test_split_window_and_focus() -> None:
    tasks = [
        _task(1, "completed", order=0),
        _task(3, "completed", order=1),
        _task(1, "pending", order=2),
        _task(4, "pending", order=3),
        _task(2, "in_progress", order=4),
    ]
    groups = split_tasks(tasks)
    assert [t.sort_order for t in groups["delayed"]] == [2]  # pending before the latest completed week
    assert plan_window(tasks, 4) == (4, 1)
    assert plan_window([], 8) == (1, 8)
    gaps = score_gaps(CATALOG["backend engineer"]["competencies"], [])
    assert put_focus_first(gaps, "docker")[0].name == "Docker"


def test_adapt_keeps_completed_history_and_replaces_pending(client: TestClient, monkeypatch) -> None:
    token, fake = setup_roadmap(client, monkeypatch, "adapt@example.com")
    before = client.get("/api/v1/roadmaps/current", headers=bearer(token)).json()
    assert before["source"] == "fallback"
    first_two = [task["id"] for task in before["tasks"][:2]]
    for task_id in first_two:
        done = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "completed", "notes": "ok"}, headers=bearer(token))
        assert done.status_code == 200
    pending_before = {t["id"] for t in before["tasks"][2:]}

    job = client.post("/api/v1/roadmaps/current/adapt", json={"mode": "lighter"}, headers=bearer(token))
    assert job.status_code == 202, job.text
    assert job.json()["kind"] == "adapt"
    run_worker(fake)
    status = client.get(f"/api/v1/jobs/{job.json()['id']}", headers=bearer(token)).json()
    assert status["status"] == "completed", status

    after = client.get("/api/v1/roadmaps/current", headers=bearer(token)).json()
    ids = {t["id"] for t in after["tasks"]}
    assert set(first_two) <= ids  # history preserved
    kept = {t["id"]: t for t in after["tasks"] if t["id"] in first_two}
    assert all(t["status"] == "completed" and t["notes"] == "ok" for t in kept.values())
    assert not (pending_before & ids)  # unstarted tasks were replaced
    assert after["adapted_count"] == 1
    assert after["weekly_hours"] == 3
    assert "lighter" in after["adaptation_note"]
    last_done_week = max(t["week_number"] for t in kept.values())
    new_tasks = [t for t in after["tasks"] if t["id"] not in first_two]
    assert new_tasks and all(t["week_number"] >= min(last_done_week + 1, after["timeline_weeks"]) for t in new_tasks)
    assert len({t["sort_order"] for t in after["tasks"]}) == len(after["tasks"])


def test_adapt_validation_and_ownership(client: TestClient, monkeypatch) -> None:
    token, _fake = setup_roadmap(client, monkeypatch, "adapt-val@example.com")
    bad = client.post("/api/v1/roadmaps/current/adapt", json={"mode": "focus", "focus_skill": "Origami"}, headers=bearer(token))
    assert bad.status_code == 422
    missing = client.post("/api/v1/roadmaps/current/adapt", json={"mode": "focus"}, headers=bearer(token))
    assert missing.status_code == 422
    unknown_mode = client.post("/api/v1/roadmaps/current/adapt", json={"mode": "turbo"}, headers=bearer(token))
    assert unknown_mode.status_code == 422
    good = client.post("/api/v1/roadmaps/current/adapt", json={"mode": "focus", "focus_skill": "docker"}, headers=bearer(token))
    assert good.status_code == 202
    newcomer = auth(client, "adapt-new@example.com")
    assert client.post("/api/v1/roadmaps/current/adapt", json={"mode": "revise"}, headers=bearer(newcomer)).status_code == 409
    assert client.post("/api/v1/roadmaps/current/adapt", json={"mode": "revise"}).status_code == 401
