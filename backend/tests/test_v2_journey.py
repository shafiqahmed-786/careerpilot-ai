from app.config import settings
from fastapi.testclient import TestClient
from tests.conftest import auth, bearer
from tests.support import PROFILE, RESUME_LINES, fake_llm_json, make_docx, run_worker, use_fake_redis

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_full_ai_journey(client: TestClient, monkeypatch) -> None:
    """Signup, profile, resume, AI roadmap, mentor, task completion, adapted guidance (OpenAI mocked)."""
    fake = use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr("app.llm.chat_json", fake_llm_json)
    prompts: list[str] = []

    def fake_chat(messages, **_kwargs):
        prompts.append(messages[0]["content"])
        return "Work on the next task in your roadmap."

    monkeypatch.setattr("app.llm.chat", fake_chat)

    token = auth(client, "journey2@example.com")
    headers = bearer(token)
    assert client.put("/api/v1/profile", json=PROFILE, headers=headers).status_code == 200

    upload = client.post(
        "/api/v1/resume/analyze", files={"file": ("cv.docx", make_docx(RESUME_LINES), DOCX)}, headers=headers
    )
    assert upload.status_code == 202, upload.text
    assert client.post("/api/v1/assessments", headers=headers).status_code == 202
    run_worker(fake)  # resume job and assessment job go through the real queue

    resume = client.get("/api/v1/resume/latest", headers=headers).json()
    assert resume["status"] == "completed" and resume["provider"] == "openai"
    assert resume["comparison"]["target_role"] == "Backend Engineer"

    assessment = client.get("/api/v1/assessments/latest", headers=headers).json()
    assert assessment["provider"] == "openai"
    sql = next(c for c in assessment["competencies"] if c["name"] == "SQL")
    assert sql["self_reported_level"] == 0  # the resume never changes the deterministic score

    roadmap = client.get("/api/v1/roadmaps/current", headers=headers).json()
    assert roadmap["source"] == "ai" and roadmap["provider"] == "openai"
    assert [m["week"] for m in roadmap["milestones"]] == [1, 2, 3, 4]
    urls = {r["url"] for r in assessment["resources"]}
    assert all(res["url"] in urls for task in roadmap["tasks"] for res in task["resources"])
    assert not any("invented.example" in res["url"] for task in roadmap["tasks"] for res in task["resources"])

    conversation = client.post("/api/v1/mentor/conversations", headers=headers).json()["id"]
    ask = f"/api/v1/mentor/conversations/{conversation}/messages"
    first = client.post(ask, json={"content": "What should I focus on this week?"}, headers=headers)
    assert first.json()["assistant_message"]["provider"] == "openai"
    task = roadmap["tasks"][0]
    assert task["title"] in prompts[-1] and "RESUME (openai)" in prompts[-1]

    done = client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "completed", "notes": "shipped"}, headers=headers)
    assert done.status_code == 200
    client.post(ask, json={"content": "What now?"}, headers=headers)
    assert f"1/{len(roadmap['tasks'])} tasks completed" in prompts[-1]

    board = client.get("/api/v1/dashboard", headers=headers).json()
    assert board["streak_days"] == 1 and board["milestones_total"] == 4
    assert board["activity"][-1]["count"] == 1
    assert board["readiness_percent"] is not None and board["resume"]["status"] == "completed"

    adapt = client.post("/api/v1/roadmaps/current/adapt", json={"mode": "intensive"}, headers=headers)
    assert adapt.status_code == 202
    run_worker(fake)
    after = client.get("/api/v1/roadmaps/current", headers=headers).json()
    assert after["adapted_count"] == 1 and after["weekly_hours"] == 9 and after["source"] in {"ai", "fallback"}
    assert any(t["id"] == task["id"] and t["status"] == "completed" for t in after["tasks"])
