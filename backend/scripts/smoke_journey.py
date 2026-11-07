"""One local pass through signup, queue, worker, and task completion.

Uses DATABASE_URL and REDIS_URL from the environment. Does not print secrets.
"""

import time
import uuid

from fastapi.testclient import TestClient
from rq import Queue

from app.main import app
from app.queue import redis_conn, worker_class


def main() -> None:
    redis_conn().ping()
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    client = TestClient(app)
    signup = client.post("/api/v1/auth/signup", json={"email": email, "password": "password123"})
    if signup.status_code != 201:
        raise SystemExit(signup.text)
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    profile = {
        "full_name": "Smoke User",
        "education": "B.Tech",
        "experience_level": "fresh_graduate",
        "skills": [{"name": "Python", "proficiency": 3}],
        "projects": "Notes API",
        "target_career": "Backend Engineer",
        "weekly_hours": 6,
        "timeline_weeks": 4,
    }
    saved = client.put("/api/v1/profile", json=profile, headers=headers)
    if saved.status_code != 200:
        raise SystemExit(saved.text)
    created = client.post("/api/v1/assessments", headers=headers)
    if created.status_code != 202:
        raise SystemExit(created.text)
    connection = redis_conn()
    worker = worker_class()([Queue("careerpilot", connection=connection)], connection=connection)
    worker.work(burst=True)
    job = {"status": "queued"}
    for _ in range(30):
        job = client.get(f"/api/v1/jobs/{created.json()['id']}", headers=headers).json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(1)
    assessment = client.get("/api/v1/assessments/latest", headers=headers).json()
    roadmap = client.get("/api/v1/roadmaps/current", headers=headers).json()
    task_id = roadmap["tasks"][0]["id"]
    updated = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "completed", "notes": "smoke"},
        headers=headers,
    )
    if updated.status_code != 200:
        raise SystemExit(updated.text)
    board = client.get("/api/v1/dashboard", headers=headers).json()
    ready = client.get("/api/v1/health/ready").json()
    providers = sorted({item["provider"] for item in assessment["resources"]})
    print("job_status", job["status"])
    print("narrative", assessment["provider"])
    print("role", assessment["normalized_role"])
    print("resource_providers", providers)
    print("resource_count", len(assessment["resources"]))
    print("https", all(item["url"].startswith("https://") for item in assessment["resources"]))
    print("completion", board["completion_percent"])
    print("ready", ready["status"], ready["database"], ready["redis"], ready["llm"], ready["search"])


if __name__ == "__main__":
    main()
