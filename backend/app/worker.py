"""RQ entrypoint. Run in a separate process from the API."""

from datetime import UTC, datetime

from app.database import SessionLocal
from app.models import AssessmentJob, Profile
from app.pipeline import run_and_persist
from app.queue import QUEUE_NAME, redis_conn, worker_class


def process_assessment_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(AssessmentJob, job_id)
        if job is None or job.status == "completed":
            return
        profile = db.query(Profile).filter(Profile.user_id == job.user_id).one()
        job.status = "running"
        job.started_at = datetime.now(UTC)
        job.error = None
        db.commit()

        assessment, roadmap = run_and_persist(db, job, profile)
        job.status = "completed"
        job.assessment_id = assessment.id
        job.roadmap_id = roadmap.id
        job.finished_at = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(AssessmentJob, job_id)
        if job is not None and job.status != "completed":
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.finished_at = datetime.now(UTC)
            db.commit()
        raise
    finally:
        db.close()


def main() -> None:
    connection = redis_conn()
    worker = worker_class()([QUEUE_NAME], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
