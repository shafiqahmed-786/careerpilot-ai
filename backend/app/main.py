from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import router
from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.app_env == "production" and settings.jwt_secret == "dev-only-change-me":
        raise RuntimeError("Set JWT_SECRET before running with APP_ENV=production")
    yield


app = FastAPI(title="CareerPilot AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "careerpilot-ai"}


@app.get("/api/v1/health/ready")
def ready() -> dict:
    database = True
    redis_ok = True
    db_error = None
    redis_error = None
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        database = False
        db_error = str(exc)[:200]
    try:
        from app.queue import redis_conn

        redis_conn().ping()
    except Exception as exc:
        redis_ok = False
        redis_error = str(exc)[:200]
    status = "ok" if database and redis_ok else "degraded"
    return {
        "status": status,
        "database": database,
        "redis": redis_ok,
        "llm": settings.llm_mode,
        "search": settings.search_mode,
        "database_error": db_error,
        "redis_error": redis_error,
    }
