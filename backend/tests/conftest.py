import os
import tempfile
from pathlib import Path

_DIR = Path(tempfile.mkdtemp(prefix="careerpilot-test-"))
_DB = _DIR / "test.db"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///" + _DB.as_posix()
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = ""
os.environ["TAVILY_API_KEY"] = ""
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import pytest
from alembic import command
from alembic.config import Config
from app.database import engine
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import inspect


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    names = set(inspect(engine).get_table_names())
    expected = {
        "users",
        "profiles",
        "assessment_jobs",
        "assessments",
        "competency_results",
        "learning_resources",
        "roadmaps",
        "roadmap_tasks",
        "mentor_conversations",
        "mentor_messages",
        "resume_analyses",
    }
    missing = expected - names
    assert not missing, missing


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def auth(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
