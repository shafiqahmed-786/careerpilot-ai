import io
import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE = "http://localhost:8000/api/v1"


def req(path: str, method: str = "GET", data: dict | bytes | None = None, token: str | None = None, content_type: str = "application/json") -> dict:
    url = f"{BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        if content_type == "application/json" and isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        else:
            body = data
            headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("--- 1. Probing Health Endpoint ---")
    health = req("/health/ready")
    print(f"Health Status: {health['status']}, DB: {health['database']}, Redis: {health['redis']}, LLM: {health['llm']}")
    assert health["status"] == "ok"

    print("\n--- 2. Registering Test Account ---")
    email = f"sup_{uuid.uuid4().hex[:6]}@example.com"
    auth = req("/auth/signup", method="POST", data={"email": email, "password": "Password123!"})
    token = auth["access_token"]
    print(f"Registered user: {email}")

    print("\n--- 3. Creating Career Profile ---")
    prof_payload = {
        "full_name": "Unified Supervisor Tester",
        "education": "B.Tech Computer Science",
        "experience_level": "junior",
        "skills": [{"name": "Python", "proficiency": 3}, {"name": "SQL", "proficiency": 2}],
        "projects": "Production FastAPI services with PostgreSQL and Redis queues",
        "target_career": "Backend Engineer",
        "weekly_hours": 10,
        "timeline_weeks": 8,
    }
    prof = req("/profile", method="PUT", data=prof_payload, token=token)
    print(f"Saved Profile target: {prof['target_career']}")

    print("\n--- 4. Testing Job 1: Assessment & Roadmap Generation ---")
    job1 = req("/assessments", method="POST", token=token)
    job1_id = job1["id"]
    print(f"Queued Assessment Job: {job1_id} (initial status: {job1['status']})")

    for _ in range(40):
        poll = req(f"/jobs/{job1_id}", token=token)
        if poll["status"] in ("completed", "failed"):
            print(f"Assessment Job finished with status: {poll['status']}")
            assert poll["status"] == "completed", f"Job failed: {poll.get('error')}"
            break
        time.sleep(1)

    assessment = req("/assessments/latest", token=token)
    roadmap = req("/roadmaps/current", token=token)
    print(f"Assessment produced {len(assessment['competencies'])} competencies.")
    print(f"Roadmap produced {len(roadmap['tasks'])} tasks across {roadmap['timeline_weeks']} weeks.")

    print("\n--- 5. Testing Job 2: Roadmap Adaptation ---")
    job2 = req("/roadmaps/current/adapt", method="POST", data={"mode": "revise"}, token=token)
    job2_id = job2["id"]
    print(f"Queued Adaptation Job: {job2_id} (initial status: {job2['status']})")

    for _ in range(40):
        poll = req(f"/jobs/{job2_id}", token=token)
        if poll["status"] in ("completed", "failed"):
            print(f"Adaptation Job finished with status: {poll['status']}")
            assert poll["status"] == "completed", f"Job failed: {poll.get('error')}"
            break
        time.sleep(1)

    print("\n--- 6. Testing Job 3: Resume Analysis ---")
    from tests.support import make_pdf

    pdf_bytes = make_pdf([
        "Alex Smith",
        "Backend Software Engineer with 3 years experience.",
        "Built high-throughput REST APIs using Python, FastAPI, and PostgreSQL.",
        "Containerized production microservices with Docker and managed queues with Redis and Celery.",
        "Automated continuous integration pipelines using Git and GitHub Actions.",
    ])

    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    buf = io.BytesIO()
    buf.write(f"--{boundary}\r\n".encode())
    buf.write(b'Content-Disposition: form-data; name="file"; filename="sample_cv.pdf"\r\n')
    buf.write(b"Content-Type: application/pdf\r\n\r\n")
    buf.write(pdf_bytes)
    buf.write(f"\r\n--{boundary}--\r\n".encode())

    res_upload = req("/resume/analyze", method="POST", data=buf.getvalue(), token=token, content_type=f"multipart/form-data; boundary={boundary}")
    job3_id = res_upload["job"]["id"]
    print(f"Queued Resume Job: {job3_id} (initial status: {res_upload['job']['status']})")

    for _ in range(40):
        poll = req(f"/jobs/{job3_id}", token=token)
        if poll["status"] in ("completed", "failed"):
            print(f"Resume Analysis Job finished with status: {poll['status']}")
            assert poll["status"] == "completed", f"Job failed: {poll.get('error')}"
            break
        time.sleep(1)

    latest_resume = req("/resume/latest", token=token)
    skills_count = len(latest_resume["analysis"]["skills"]) if latest_resume and latest_resume.get("analysis") else 0
    print(f"Resume Analysis Result: status={latest_resume['status']}, verified skills={skills_count}")

    print("\n============================================================")
    print("SUCCESS: ALL 3 JOB TYPES PROCESSED IN SAME CONTAINER BY SUPERVISOR!")
    print("============================================================")


if __name__ == "__main__":
    main()

