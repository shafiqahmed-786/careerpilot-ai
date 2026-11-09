import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.api import router
from app.config import settings
from app.database import engine
from app.routes_mentor import router as mentor_router
from app.routes_resume import router as resume_router

logger = logging.getLogger("careerpilot")

# Any localhost or 127.0.0.1 port is allowed outside production, so `next dev` on 3001 or a
# 127.0.0.1 URL does not fail with an opaque "Failed to fetch". Production uses CORS_ORIGINS only.
LOCAL_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.app_env == "production" and settings.jwt_secret == "dev-only-change-me":
        raise RuntimeError("Set JWT_SECRET before running with APP_ENV=production")
    yield


app = FastAPI(title="CareerPilot AI", version="1.0.0", lifespan=lifespan)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Database error: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The database is unavailable or not migrated. Start PostgreSQL "
                "(docker compose up -d postgres) and run `alembic upgrade head` in backend/."
            )
        },
    )


@app.middleware("http")
async def unhandled_error_middleware(request: Request, call_next):
    # Registered before CORSMiddleware so it sits inside it. A 500 built here still carries CORS
    # headers, so the browser shows the real status instead of "Failed to fetch".
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error. Check the API logs."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=None if settings.app_env == "production" else LOCAL_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(mentor_router)
app.include_router(resume_router)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "careerpilot-ai"}


@app.get("/api/v1/health/ready")
def ready() -> dict:
    database = True
    migrated = False
    redis_ok = True
    db_error = None
    redis_error = None
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        migrated = inspect(engine).has_table("users")
    except Exception as exc:
        database = False
        db_error = str(exc)[:200]
    try:
        from app.queue import redis_conn

        redis_conn().ping()
    except Exception as exc:
        redis_ok = False
        redis_error = str(exc)[:200]
    status = "ok" if database and migrated and redis_ok else "degraded"
    return {
        "status": status,
        "database": database,
        "migrations": migrated,
        "redis": redis_ok,
        "llm": settings.llm_mode,
        "llm_model": settings.groq_model if settings.llm_mode == "groq" else None,
        "search": settings.search_mode,
        "database_error": db_error,
        "redis_error": redis_error,
    }
