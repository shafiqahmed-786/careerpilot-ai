import fakeredis
from app.queue import burst_worker_class
from fastapi.testclient import TestClient
from rq import Queue
from tests.conftest import auth, bearer

PROFILE = {
    "full_name": "Asha Raman",
    "education": "B.Tech Computer Science",
    "experience_level": "fresh_graduate",
    "skills": [
        {"name": "Python", "proficiency": 3},
        {"name": "Git", "proficiency": 2},
    ],
    "projects": "Built a notes API in a college course.",
    "target_career": "Backend Engineer",
    "weekly_hours": 6,
    "timeline_weeks": 4,
}


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_signup_login_and_me(client: TestClient) -> None:
    token = auth(client, "ada@example.com")
    me = client.get("/api/v1/auth/me", headers=bearer(token))
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"
    login = client.post("/api/v1/auth/login", json={"email": "ada@example.com", "password": "password123"})
    assert login.status_code == 200
    bad = client.post("/api/v1/auth/login", json={"email": "ada@example.com", "password": "wrong-password"})
    assert bad.status_code == 401


def test_profile_and_protected_route(client: TestClient) -> None:
    denied = client.get("/api/v1/profile")
    assert denied.status_code == 401
    token = auth(client, "profile@example.com")
    saved = client.put("/api/v1/profile", json=PROFILE, headers=bearer(token))
    assert saved.status_code == 200, saved.text
    assert saved.json()["target_career"] == "Backend Engineer"
    loaded = client.get("/api/v1/profile", headers=bearer(token))
    assert loaded.json()["skills"][0]["name"] == "Python"


def test_worker_persists_roadmap_and_ownership(client: TestClient, monkeypatch) -> None:
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr("app.queue.redis_conn", lambda: fake)
    owner = auth(client, "owner@example.com")
    other = auth(client, "other@example.com")
    assert client.put("/api/v1/profile", json=PROFILE, headers=bearer(owner)).status_code == 200

    created = client.post("/api/v1/assessments", headers=bearer(owner))
    assert created.status_code == 202, created.text
    job_id = created.json()["id"]
    assert created.json()["status"] == "queued"

    worker = burst_worker_class()([Queue("careerpilot", connection=fake)], connection=fake)
    worker.work(burst=True)

    job = client.get(f"/api/v1/jobs/{job_id}", headers=bearer(owner))
    assert job.status_code == 200, job.text
    assert job.json()["status"] == "completed"
    hidden = client.get(f"/api/v1/jobs/{job_id}", headers=bearer(other))
    assert hidden.status_code == 404

    assessment = client.get("/api/v1/assessments/latest", headers=bearer(owner))
    assert assessment.status_code == 200
    body = assessment.json()
    assert body["normalized_role"] == "Backend Engineer"
    assert body["provider"] == "demo"
    assert body["rubric_version"] == "importance-x-gap-v1"
    sql = next(item for item in body["competencies"] if item["name"] == "SQL")
    assert sql["status"] == "missing"
    assert sql["self_reported_level"] == 0
    assert all(resource["provider"] == "demo" for resource in body["resources"])
    assert all(resource["url"].startswith("https://") for resource in body["resources"])
    assert client.get("/api/v1/assessments/latest", headers=bearer(other)).json() is None

    roadmap = client.get("/api/v1/roadmaps/current", headers=bearer(owner))
    assert roadmap.status_code == 200
    plan = roadmap.json()
    assert plan["timeline_weeks"] == 4
    assert plan["completion_percent"] == 0
    assert plan["tasks"]
    task_id = plan["tasks"][0]["id"]

    stolen = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "completed", "notes": "not yours"},
        headers=bearer(other),
    )
    assert stolen.status_code == 404

    updated = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "completed", "notes": "Finished the reading notes."},
        headers=bearer(owner),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert updated.json()["notes"] == "Finished the reading notes."

    dashboard = client.get("/api/v1/dashboard", headers=bearer(owner))
    assert dashboard.status_code == 200
    board = dashboard.json()
    assert board["completion_percent"] > 0
    assert board["recently_completed"][0]["id"] == task_id
    assert board["profile"]["target_career"] == "Backend Engineer"
    assert board["top_gaps"]
