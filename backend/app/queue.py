import os

from redis import Redis
from rq import Queue, SimpleWorker, Worker

from app.config import settings

QUEUE_NAME = "careerpilot"


def redis_conn() -> Redis:
    return Redis.from_url(settings.redis_url)


def assessment_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=redis_conn())


def enqueue_assessment(job_id: str) -> str:
    job = assessment_queue().enqueue(
        "app.worker.process_assessment_job",
        job_id,
        job_timeout=600,
        result_ttl=500,
        failure_ttl=86_400,
    )
    return job.id


def enqueue_resume_analysis(job_id: str) -> str:
    job = assessment_queue().enqueue(
        "app.worker.process_resume_job",
        job_id,
        job_timeout=600,
        result_ttl=500,
        failure_ttl=86_400,
    )
    return job.id


class _NoDeathPenalty:
    """RQ's default timeout uses SIGALRM, which Windows does not provide."""

    def __init__(self, *_args, **_kwargs) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> bool:
        return False


class WindowsWorker(SimpleWorker):
    """Separate RQ process that does not fork and does not need SIGALRM."""

    death_penalty_class = _NoDeathPenalty


def worker_class():
    # RQ's default worker forks. Windows cannot fork or arm SIGALRM.
    # WindowsWorker is still a separate queue consumer from the API process.
    if os.name == "nt":
        return WindowsWorker
    return Worker


def burst_worker_class():
    if os.name == "nt":
        return WindowsWorker
    return SimpleWorker
