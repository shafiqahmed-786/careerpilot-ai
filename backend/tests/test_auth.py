from datetime import UTC, datetime, timedelta

import jwt
from app.config import settings
from app.security import hash_password, verify_password
from fastapi.testclient import TestClient
from tests.conftest import auth, bearer


def test_signup_normalizes_email_and_rejects_duplicates(client: TestClient) -> None:
    auth(client, "  Mixed.Case@Example.com ")
    login = client.post("/api/v1/auth/login", json={"email": "mixed.case@example.com", "password": "password123"})
    assert login.status_code == 200
    duplicate = client.post(
        "/api/v1/auth/signup", json={"email": "MIXED.CASE@example.com", "password": "password123"}
    )
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]


def test_concurrent_duplicate_signup_returns_409(client: TestClient, monkeypatch) -> None:
    auth(client, "race@example.com")
    # Simulate the race: the existence check misses, so the unique index has to reject the insert.
    monkeypatch.setattr("app.api._find_user_by_email", lambda _db, _email: None)
    response = client.post("/api/v1/auth/signup", json={"email": "race@example.com", "password": "password123"})
    assert response.status_code == 409
    monkeypatch.undo()
    # The session was rolled back cleanly, so the API keeps working.
    assert client.post("/api/v1/auth/login", json={"email": "race@example.com", "password": "password123"}).status_code == 200


def test_invalid_email_is_rejected(client: TestClient) -> None:
    for email in ["not-an-email", "a@b", "@example.com", "spaces in@example.com"]:
        response = client.post("/api/v1/auth/signup", json={"email": email, "password": "password123"})
        assert response.status_code == 422, email


def test_weak_and_overlong_passwords_are_rejected(client: TestClient) -> None:
    short = client.post("/api/v1/auth/signup", json={"email": "short@example.com", "password": "short"})
    assert short.status_code == 422
    blank = client.post("/api/v1/auth/signup", json={"email": "blank@example.com", "password": " " * 10})
    assert blank.status_code == 422
    too_long_ascii = client.post("/api/v1/auth/signup", json={"email": "long@example.com", "password": "a" * 73})
    assert too_long_ascii.status_code == 422
    # 40 characters but 80 bytes in UTF-8: bcrypt would see only the first 72 bytes.
    too_long_bytes = client.post("/api/v1/auth/signup", json={"email": "bytes@example.com", "password": "é" * 40})
    assert too_long_bytes.status_code == 422


def test_password_at_the_byte_limit_works(client: TestClient) -> None:
    password = "a" * 72
    auth(client, "limit@example.com", password)
    ok = client.post("/api/v1/auth/login", json={"email": "limit@example.com", "password": password})
    assert ok.status_code == 200
    # An overlong login attempt is a plain 401, not a server error.
    too_long = client.post("/api/v1/auth/login", json={"email": "limit@example.com", "password": password + "b"})
    assert too_long.status_code == 401


def test_login_unknown_user(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert response.status_code == 401


def test_invalid_and_expired_tokens(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me", headers=bearer("garbage")).status_code == 401
    expired = jwt.encode(
        {"sub": "someone", "exp": datetime.now(UTC) - timedelta(minutes=1)}, settings.jwt_secret, algorithm="HS256"
    )
    response = client.get("/api/v1/auth/me", headers=bearer(expired))
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
    unknown_user = jwt.encode(
        {"sub": "no-such-user", "exp": datetime.now(UTC) + timedelta(minutes=5)}, settings.jwt_secret, algorithm="HS256"
    )
    assert client.get("/api/v1/auth/me", headers=bearer(unknown_user)).status_code == 401


def test_password_hashing_helpers() -> None:
    hashed = hash_password("password123")
    assert hashed != "password123"
    assert verify_password("password123", hashed)
    assert not verify_password("password124", hashed)
    assert not verify_password("a" * 100, hashed)


def test_ready_reports_database_and_migrations(client: TestClient) -> None:
    body = client.get("/api/v1/health/ready").json()
    assert body["database"] is True
    assert body["migrations"] is True
    assert body["llm"] == "demo"
    assert body["search"] == "demo"


def test_local_origin_is_allowed_on_any_port(client: TestClient) -> None:
    response = client.options(
        "/api/v1/auth/signup",
        headers={"Origin": "http://127.0.0.1:3001", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3001"
