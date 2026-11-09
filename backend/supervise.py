"""Process supervisor for CareerPilot AI.

Runs Alembic migrations once, then concurrently supervises:
1. RQ background worker (`python -m app.worker`)
2. FastAPI/Uvicorn API server (`python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}`)

If the worker exits unexpectedly, it is restarted with exponential backoff.
If the API exits, the worker is terminated and the supervisor exits with the API's returncode.
On SIGTERM/SIGINT, both processes are gracefully terminated.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [supervisor] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("supervisor")

SHUTDOWN_TIMEOUT_SECONDS = 10.0
INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 30.0
BACKOFF_RESET_HEALTHY_SECONDS = 60.0


def set_working_directory() -> None:
    """Ensure working directory is /app in container or the backend directory locally."""
    container_app = Path("/app")
    if container_app.is_dir() and (container_app / "alembic.ini").is_file():
        os.chdir(str(container_app))
        logger.info("Set working directory to %s", container_app)
    else:
        local_backend = Path(__file__).resolve().parent
        os.chdir(str(local_backend))
        logger.info("Set working directory to %s", local_backend)


def run_migrations() -> None:
    """Run database migrations once before starting any services."""
    logger.info("Running database migrations: alembic upgrade head")
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.error("Migrations failed with exit code %s. Aborting startup.", result.returncode)
        sys.exit(result.returncode)
    logger.info("Database migrations applied successfully.")


def stop_process(proc: subprocess.Popen, name: str, timeout: float = SHUTDOWN_TIMEOUT_SECONDS) -> None:
    """Terminate a process gracefully with SIGTERM, falling back to SIGKILL if needed."""
    if proc.poll() is not None:
        return
    logger.info("Stopping %s (pid %s)...", name, proc.pid)
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
        logger.info("%s stopped cleanly (exit code %s).", name, proc.returncode)
    except subprocess.TimeoutExpired:
        logger.warning("%s did not exit within %ss; killing forcefully...", name, timeout)
        try:
            proc.kill()
            proc.wait(timeout=3.0)
            logger.info("%s killed forcefully.", name)
        except Exception as exc:
            logger.error("Failed to kill %s: %s", name, exc)
    except Exception as exc:
        logger.error("Error stopping %s: %s", name, exc)


def start_worker() -> subprocess.Popen:
    """Start the RQ background worker."""
    cmd = [sys.executable, "-m", "app.worker"]
    logger.info("Starting RQ worker: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def start_api() -> subprocess.Popen:
    """Start FastAPI via Uvicorn on the configured port."""
    port = os.environ.get("PORT", "10000")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    logger.info("Starting FastAPI/Uvicorn on port %s: %s", port, " ".join(cmd))
    return subprocess.Popen(cmd)


def main() -> None:
    set_working_directory()
    run_migrations()

    shutting_down = False
    worker_proc: subprocess.Popen | None = None
    api_proc: subprocess.Popen | None = None

    def handle_signal(sig, _frame):
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        sig_name = signal.Signals(sig).name if hasattr(signal, "Signals") else str(sig)
        logger.info("Received signal %s. Shutting down all managed processes...", sig_name)
        if api_proc:
            stop_process(api_proc, "API")
        if worker_proc:
            stop_process(worker_proc, "RQ Worker")
        logger.info("Supervisor shutdown complete.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_signal)

    # 1. Start worker
    worker_proc = start_worker()
    worker_start_time = time.time()
    worker_backoff = INITIAL_BACKOFF_SECONDS

    # 2. Start API
    api_proc = start_api()

    logger.info(
        "Both processes started (API pid=%s, Worker pid=%s). Supervisor active.",
        api_proc.pid,
        worker_proc.pid,
    )

    # Main supervision loop
    while not shutting_down:
        try:
            time.sleep(1.0)
        except InterruptedError:
            continue

        # Check API health
        api_exit = api_proc.poll()
        if api_exit is not None:
            logger.error("FastAPI/Uvicorn exited unexpectedly with code %s.", api_exit)
            shutting_down = True
            if worker_proc:
                stop_process(worker_proc, "RQ Worker")
            sys.exit(api_exit)

        # Check Worker health
        worker_exit = worker_proc.poll()
        if worker_exit is not None:
            if not shutting_down:
                logger.warning(
                    "RQ worker exited with code %s. Restarting in %.1fs (exponential backoff)...",
                    worker_exit,
                    worker_backoff,
                )
                # Wait backoff while still monitoring API
                sleep_start = time.time()
                while time.time() - sleep_start < worker_backoff and not shutting_down:
                    if api_proc.poll() is not None:
                        logger.error("API exited while waiting to restart worker.")
                        shutting_down = True
                        sys.exit(api_proc.returncode or 1)
                    time.sleep(0.5)

                if not shutting_down:
                    worker_proc = start_worker()
                    worker_start_time = time.time()
                    worker_backoff = min(worker_backoff * 2, MAX_BACKOFF_SECONDS)
        else:
            # If worker has run steadily past the health window, reset backoff
            if (time.time() - worker_start_time) > BACKOFF_RESET_HEALTHY_SECONDS and worker_backoff > INITIAL_BACKOFF_SECONDS:
                worker_backoff = INITIAL_BACKOFF_SECONDS
                logger.info("RQ worker has been healthy for >%ss. Backoff reset.", BACKOFF_RESET_HEALTHY_SECONDS)


if __name__ == "__main__":
    main()
