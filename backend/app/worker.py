"""RQ entrypoint. Run in a separate process from the API."""

import logging
from datetime import UTC, datetime

from app.database import SessionLocal
from app.models import AssessmentJob, Profile, ResumeAnalysis
from app.pipeline import run_adaptation, run_and_persist
from app.queue import QUEUE_NAME, redis_conn, worker_class
from app.resume_analysis import analyze_text, compare_to_role


def process_assessment_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(AssessmentJob, job_id)
        if job is None or job.status == "completed":
            return
        job.status = "running"
        job.started_at = datetime.now(UTC)
        job.error = None
        db.commit()

        if job.kind == "resume":
            run_resume_job(db, job)
        else:
            profile = db.query(Profile).filter(Profile.user_id == job.user_id).one()
            if job.kind == "adapt":
                assessment_id, roadmap = run_adaptation(db, job, profile)
            else:
                assessment, roadmap = run_and_persist(db, job, profile)
                assessment_id = assessment.id
            job.assessment_id = assessment_id
            job.roadmap_id = roadmap.id
        job.status = "completed"
        job.finished_at = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(AssessmentJob, job_id)
        if job is not None and job.status != "completed":
            job.status = "failed"
            if job.kind == "resume":
                # Exception text can echo resume content, so only a fixed message is stored or shown.
                known = isinstance(exc, ValueError) and str(exc).startswith("The uploaded resume text")
                job.error = str(exc) if known else "The resume analysis failed. Upload the file again."
                _fail_resume(db, job, job.error)
            else:
                job.error = str(exc)[:2000]
            job.finished_at = datetime.now(UTC)
            db.commit()
        raise
    finally:
        db.close()


def run_resume_job(db, job: AssessmentJob) -> None:
    resume = db.get(ResumeAnalysis, (job.params or {}).get("resume_id"))
    if resume is None or resume.user_id != job.user_id or not resume.source_text:
        raise ValueError("The uploaded resume text is no longer available. Upload it again.")
    profile = db.query(Profile).filter(Profile.user_id == job.user_id).first()
    target = profile.target_career if profile and profile.target_career.strip() else None
    analysis, provider, notice = analyze_text(resume.source_text, target)
    resume.analysis = analysis.model_dump()
    resume.comparison = (
        compare_to_role(target, analysis.skills, analysis.recommended_projects) if target else None
    )
    resume.provider = provider
    resume.notice = notice
    resume.status = "completed"
    resume.source_text = None  # keep the structured analysis, drop the extracted text


def _fail_resume(db, job: AssessmentJob, message: str) -> None:
    resume = db.get(ResumeAnalysis, (job.params or {}).get("resume_id"))
    if resume is not None:
        resume.status = "failed"
        resume.error = message
        resume.source_text = None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    connection = redis_conn()
    worker = worker_class()([QUEUE_NAME], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
