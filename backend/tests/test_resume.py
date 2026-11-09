import pytest
from app.config import settings
from app.database import SessionLocal
from app.models import ResumeAnalysis
from app.resume_analysis import (
    MAX_BYTES,
    ResumeAnalysisResult,
    ResumeError,
    SkillEvidence,
    compare_to_role,
    extract_text,
    ground_skills,
    heuristic_analysis,
)
from fastapi.testclient import TestClient
from tests.conftest import auth, bearer
from tests.support import (
    PROFILE,
    RESUME_EVIDENCE,
    RESUME_LINES,
    fake_llm_json,
    make_docx,
    make_pdf,
    run_worker,
    use_fake_redis,
)

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TEXT = "\n".join(RESUME_LINES)


def test_extracts_docx_and_pdf() -> None:
    docx = extract_text("cv.docx", DOCX, make_docx(RESUME_LINES))
    assert "Notes API" in docx and "pytest" in docx
    pdf = extract_text("cv.pdf", "application/pdf", make_pdf(RESUME_LINES))
    assert "Python" in pdf


@pytest.mark.parametrize(
    ("name", "ctype", "data", "status"),
    [
        ("cv.txt", "text/plain", b"hello" * 50, 415),
        ("cv.exe", "application/octet-stream", b"MZ" + b"0" * 100, 415),
        ("cv.pdf", "text/plain", b"%PDF-1.4 " + b"x" * 100, 415),
        ("cv.pdf", "application/pdf", b"not really a pdf" * 10, 415),
        ("cv.docx", DOCX, b"not a zip" * 10, 415),
        ("cv.pdf", "application/pdf", b"", 422),
        ("cv.pdf", "application/pdf", b"%PDF-" + b"0" * (MAX_BYTES + 1), 413),
        ("cv.pdf", "application/pdf", b"%PDF-1.4\n" + b"garbage " * 40, 422),
        ("cv.docx", DOCX, b"PK\x03\x04" + b"0" * 100, 422),
    ],
    ids=[
        "wrong-ext-txt",
        "exe-header",
        "pdf-wrong-mime",
        "pdf-corrupt-header",
        "docx-corrupt-zip",
        "empty-pdf",
        "oversized-pdf",
        "pdf-garbage-body",
        "docx-truncated-zip",
    ],
)
def test_rejects_bad_uploads(name, ctype, data, status) -> None:
    with pytest.raises(ResumeError) as error:
        extract_text(name, ctype, data)
    assert error.value.status_code == status


def test_rejects_documents_without_text() -> None:
    with pytest.raises(ResumeError) as error:
        extract_text("cv.docx", DOCX, make_docx(["x"]))
    assert "No readable text" in error.value.message


def test_keyword_analysis_separates_evidence_from_listed_skills() -> None:
    result = heuristic_analysis(TEXT)
    by_name = {skill.name.lower(): skill for skill in result.skills}
    assert by_name["python"].evidence_level == "demonstrated"
    assert RESUME_EVIDENCE[:40] in by_name["python"].evidence[0]
    assert by_name["docker"].evidence_level == "listed"
    assert result.projects and result.projects[0].name == "Notes API"
    assert result.education


def test_grounding_downgrades_unsupported_claims() -> None:
    claimed = ResumeAnalysisResult(
        overview="A short overview of the resume.",
        skills=[
            SkillEvidence(name="Python", evidence_level="demonstrated", evidence=[RESUME_EVIDENCE], usage="Built a REST API with Python"),
            SkillEvidence(name="Kubernetes", evidence_level="demonstrated", evidence=["Ran a 40-node cluster"], usage="Ran a cluster"),
            SkillEvidence(name="Docker", evidence_level="demonstrated", evidence=["made up quote"], usage="Used Docker"),
            SkillEvidence(name="Rust", evidence_level="listed"),
        ],
    )
    grounded = {s.name: s for s in ground_skills(claimed, TEXT).skills}
    assert grounded["Python"].evidence_level == "demonstrated"
    assert grounded["Kubernetes"].evidence_level == "inferred" and grounded["Kubernetes"].confidence == "low"
    assert grounded["Docker"].evidence_level == "listed" and grounded["Docker"].evidence == []
    assert grounded["Rust"].evidence_level == "inferred"


def test_role_comparison_is_deterministic() -> None:
    skills = [
        SkillEvidence(name="Python", evidence_level="demonstrated", evidence=["x"]),
        SkillEvidence(name="PostgreSQL", evidence_level="listed"),
    ]
    first = compare_to_role("Backend Engineer", skills, [])
    assert first == compare_to_role("Backend Engineer", skills, [])
    assert first["evidence_coverage_percent"] == 30  # (5 x 1 + 5 x 0.5) / 25
    status = {item["name"]: item["status"] for item in first["competencies"]}
    assert status["Python"] == "demonstrated" and status["SQL"] == "listed" and status["Git"] == "missing"
    assert "Git" in first["priorities"] or "HTTP APIs" in first["priorities"]
    assert "sum(importance" in first["formula"]


def _upload(client: TestClient, token: str, name="cv.docx", ctype=DOCX, data=None):
    return client.post(
        "/api/v1/resume/analyze",
        files={"file": (name, data if data is not None else make_docx(RESUME_LINES), ctype)},
        headers=bearer(token),
    )


def test_upload_endpoint_validation(client: TestClient, monkeypatch) -> None:
    use_fake_redis(monkeypatch)
    assert client.post("/api/v1/resume/analyze", files={"file": ("cv.docx", b"x", DOCX)}).status_code == 401
    token = auth(client, "resume-validate@example.com")
    assert _upload(client, token, "cv.exe", "application/octet-stream", b"MZ" * 40).status_code == 415
    assert _upload(client, token, "cv.docx", DOCX, b"").status_code == 422
    assert _upload(client, token, "cv.docx", DOCX, b"PK" + b"0" * 80).status_code == 422


def test_resume_pipeline_demo_mode_and_privacy(client: TestClient, monkeypatch) -> None:
    fake = use_fake_redis(monkeypatch)
    token = auth(client, "resume-demo@example.com")
    other = auth(client, "resume-other@example.com")
    assert client.put("/api/v1/profile", json=PROFILE, headers=bearer(token)).status_code == 200
    queued = _upload(client, token)
    assert queued.status_code == 202, queued.text
    body = queued.json()
    assert body["job"]["kind"] == "resume"
    with SessionLocal() as db:
        assert db.get(ResumeAnalysis, body["resume_id"]).source_text  # held only until the worker runs
    run_worker(fake)

    job = client.get(f"/api/v1/jobs/{body['job']['id']}", headers=bearer(token)).json()
    assert job["status"] == "completed", job
    latest = client.get("/api/v1/resume/latest", headers=bearer(token)).json()
    assert latest["status"] == "completed"
    assert latest["provider"] == "demo" and "keyword" in latest["notice"].lower()
    assert latest["comparison"]["target_role"] == "Backend Engineer"
    assert latest["comparison"]["evidence_coverage_percent"] == 82
    with SessionLocal() as db:
        assert db.get(ResumeAnalysis, body["resume_id"]).source_text is None  # raw text dropped after analysis

    assert client.get("/api/v1/resume/latest", headers=bearer(other)).json() is None
    assert client.delete(f"/api/v1/resume/{body['resume_id']}", headers=bearer(other)).status_code == 404
    assert client.post(f"/api/v1/resume/{body['resume_id']}/apply-to-profile", headers=bearer(other)).status_code == 404
    dash = client.get("/api/v1/dashboard", headers=bearer(token)).json()
    assert dash["resume"]["match_percent"] == 82 and dash["skills_identified"] >= 4


def test_resume_live_analysis_is_grounded(client: TestClient, monkeypatch) -> None:
    fake = use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.llm.chat_json", fake_llm_json)
    token = auth(client, "resume-live@example.com")
    resp = _upload(client, token)
    assert resp.status_code == 202
    resume_id = resp.json()["resume_id"]
    run_worker(fake)

    latest = client.get("/api/v1/resume/latest", headers=bearer(token)).json()
    assert latest["id"] == resume_id
    assert latest["status"] == "completed"
    assert latest["provider"] == "groq" and latest["notice"] is None
    skills = {s["name"]: s for s in latest["analysis"]["skills"]}
    assert skills["Python"]["evidence_level"] == "demonstrated"
    assert skills["Kubernetes"]["evidence_level"] == "inferred"  # fabricated quote rejected
    assert latest["comparison"] is None  # no target career yet, so no role comparison

    # Verify dedicated GET by resume_id endpoint returns identical persisted result
    by_id = client.get(f"/api/v1/resume/{resume_id}", headers=bearer(token)).json()
    assert by_id["id"] == resume_id
    assert by_id["status"] == "completed"
    assert by_id["provider"] == "groq"
    assert by_id["analysis"] == latest["analysis"]


def test_resume_and_assessment_job_dispatch_dedicated_processors(client: TestClient, monkeypatch) -> None:
    """Regression test: resume uploads must enqueue process_resume_job, not process_assessment_job."""
    fake = use_fake_redis(monkeypatch)
    token = auth(client, "dispatch-test@example.com")
    assert client.put("/api/v1/profile", json=PROFILE, headers=bearer(token)).status_code == 200

    # 1. Resume analysis enqueue check
    resume_resp = _upload(client, token)
    assert resume_resp.status_code == 202
    resume_rq_id = resume_resp.json()["job"]["id"]

    from rq import Queue
    q = Queue("careerpilot", connection=fake)
    rq_resume_job = q.fetch_job(resume_resp.json()["job"].get("rq_job_id") or resume_rq_id)
    assert rq_resume_job is not None
    assert rq_resume_job.func_name == "app.worker.process_resume_job"
    # The RQ job must target process_resume_job
    all_jobs = q.get_jobs()
    assert len(all_jobs) == 1
    assert all_jobs[0].func_name == "app.worker.process_resume_job"

    # 2. Assessment enqueue check
    assessment_resp = client.post("/api/v1/assessments", headers=bearer(token))
    assert assessment_resp.status_code == 202
    all_jobs = q.get_jobs()
    assert len(all_jobs) == 2
    assessment_rq_job = next(j for j in all_jobs if j.func_name == "app.worker.process_assessment_job")
    assert assessment_rq_job.func_name == "app.worker.process_assessment_job"


def test_failed_resume_analysis_cannot_silently_appear_as_demo(client: TestClient, monkeypatch) -> None:
    """Regression test: failed live resume analysis must fail cleanly and never silently produce a completed demo."""
    fake = use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    from app.llm import LLMError

    def fail_llm(*args, **kwargs):
        raise LLMError("Groq upstream connection failure")

    monkeypatch.setattr("app.llm.chat_json", fail_llm)
    token = auth(client, "resume-fail@example.com")
    resp = _upload(client, token)
    assert resp.status_code == 202
    job_id = resp.json()["job"]["id"]
    resume_id = resp.json()["resume_id"]

    # Run worker: should handle failure gracefully, marking job and resume as failed
    run_worker(fake)

    # Job status must be failed
    job = client.get(f"/api/v1/jobs/{job_id}", headers=bearer(token)).json()
    assert job["status"] == "failed"

    # Resume status must be failed, NOT completed as demo!
    latest = client.get("/api/v1/resume/latest", headers=bearer(token)).json()
    assert latest["status"] == "failed"
    assert latest["provider"] != "demo"
    assert "failed" in (latest["error"] or "").lower()

    # And getting by ID returns failed status
    by_id = client.get(f"/api/v1/resume/{resume_id}", headers=bearer(token)).json()
    assert by_id["status"] == "failed"


def test_apply_to_profile(client: TestClient, monkeypatch) -> None:
    fake = use_fake_redis(monkeypatch)
    token = auth(client, "resume-apply@example.com")
    assert client.put("/api/v1/profile", json=PROFILE, headers=bearer(token)).status_code == 200
    resume_id = _upload(client, token).json()["resume_id"]
    run_worker(fake)
    latest = client.get("/api/v1/resume/latest", headers=bearer(token)).json()
    assert latest["status"] == "completed"

    applied = client.post(f"/api/v1/resume/{resume_id}/apply-to-profile", headers=bearer(token))
    assert applied.status_code == 200, applied.text
    skills = {s["name"].lower(): s["proficiency"] for s in applied.json()["skills"]}
    assert skills["python"] == 3  # existing self-report is never overwritten
    assert skills["docker"] == 1  # listed without evidence starts at the lowest level
