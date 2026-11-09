import io
import json
import zipfile

import fakeredis
from app.queue import burst_worker_class
from fastapi.testclient import TestClient
from rq import Queue
from tests.conftest import auth, bearer

PROFILE = {
    "full_name": "Asha Raman",
    "education": "B.Tech Computer Science",
    "experience_level": "fresh_graduate",
    "skills": [{"name": "Python", "proficiency": 3}, {"name": "Git", "proficiency": 2}],
    "projects": "Built a notes API in a college course.",
    "target_career": "Backend Engineer",
    "weekly_hours": 6,
    "timeline_weeks": 4,
}

RESUME_LINES = [
    "Asha Raman",
    "Skills",
    "Python, SQL, Docker",
    "Projects",
    "Notes API",
    "- Built a REST API with Python and PostgreSQL and wrote pytest tests for every endpoint",
    "Education",
    "B.Tech Computer Science, 2025",
]
RESUME_EVIDENCE = "Built a REST API with Python and PostgreSQL and wrote pytest tests for every endpoint"


def make_docx(lines: list[str]) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in lines)
    xml = f'<?xml version="1.0"?><w:document xmlns:w="x"><w:body>{body}</w:body></w:document>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def make_pdf(lines: list[str]) -> bytes:
    def esc(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream = "BT /F1 11 Tf 14 TL 72 720 Td " + " ".join(f"({esc(line)}) Tj T*" for line in lines) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for index, item in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n{item}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def run_worker(fake: fakeredis.FakeRedis) -> None:
    burst_worker_class()([Queue("careerpilot", connection=fake)], connection=fake).work(burst=True)


def use_fake_redis(monkeypatch) -> fakeredis.FakeRedis:
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr("app.queue.redis_conn", lambda: fake)
    return fake


def setup_roadmap(client: TestClient, monkeypatch, email: str, profile: dict | None = None):
    """Signup, save a profile, run the assessment through the real queue and worker."""
    fake = use_fake_redis(monkeypatch)
    token = auth(client, email)
    assert client.put("/api/v1/profile", json=profile or PROFILE, headers=bearer(token)).status_code == 200
    job = client.post("/api/v1/assessments", headers=bearer(token))
    assert job.status_code == 202, job.text
    run_worker(fake)
    done = client.get(f"/api/v1/jobs/{job.json()['id']}", headers=bearer(token)).json()
    assert done["status"] == "completed", done
    return token, fake


def fake_llm_json(messages: list[dict], **_kwargs) -> dict:
    """Stands in for Groq JSON mode. Picks the response by the system prompt."""
    system = messages[0]["content"]
    if "learning-plan writer" in system:
        spec = json.loads(messages[1]["content"].splitlines()[0])
        focus = spec["focus_skills"]
        weeks = []
        for index, week in enumerate(spec["weeks_to_plan"]):
            skill = focus[index % len(focus)]
            urls = [r["url"] for r in spec["resources"] if r["skill"] == skill][:1]
            weeks.append(
                {
                    "week_number": week,
                    "objective": f"Ship one small, tested {skill} deliverable in week {week}.",
                    "milestone": f"{skill} deliverable merged",
                    "tasks": [
                        {
                            "title": f"Build a small {skill} exercise with tests",
                            "details": f"Implement a focused {skill} exercise, add automated checks, and write a short README.",
                            "skills": [skill],
                            "estimated_hours": spec["weekly_hours"],
                            "expected_outcome": f"A working {skill} exercise you can explain and demo.",
                            "completion_criteria": f"The {skill} exercise runs, has at least three passing checks, and a README.",
                            "resource_urls": urls + ["https://invented.example/not-a-real-resource"],
                        }
                    ],
                }
            )
        return {"overview": "A personalized plan that starts from your highest-priority gaps and ships something each week.", "weeks": weeks}
    if "analyze a resume" in system:
        return {
            "overview": "Backend-leaning student resume with one API project.",
            "education": ["B.Tech Computer Science, 2025"],
            "experience": [],
            "projects": [{"name": "Notes API", "summary": "REST API with tests", "technologies": ["Python", "PostgreSQL"]}],
            "skills": [
                {"name": "Python", "category": "Languages", "evidence_level": "demonstrated",
                 "evidence": [RESUME_EVIDENCE], "usage": "Built a REST API with Python", "confidence": "high"},
                {"name": "Docker", "category": "DevOps", "evidence_level": "listed", "evidence": [], "confidence": "low"},
                {"name": "Kubernetes", "category": "DevOps", "evidence_level": "demonstrated",
                 "evidence": ["Orchestrated a 40-node Kubernetes cluster"], "usage": "Ran a cluster", "confidence": "high"},
            ],
            "achievements": [],
            "strengths": ["Has a tested API project"],
            "improvements": ["Add measurable results"],
            "potential_gaps": ["Git"],
            "recommended_projects": ["Add authentication and CI to the Notes API"],
        }
    return {
        "summary": "Your plan targets the biggest self-reported gaps first and keeps every priority score rule-based.",
        "learn_first_reason": "Start with the skill that has the highest importance multiplied by remaining gap.",
    }
