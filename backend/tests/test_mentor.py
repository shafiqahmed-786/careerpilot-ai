from app.config import settings
from app.database import SessionLocal
from app.llm import LLMError
from app.mentor import HISTORY_WINDOW, build_context, context_text
from app.models import User
from fastapi.testclient import TestClient
from tests.conftest import auth, bearer
from tests.support import PROFILE, setup_roadmap


def _conversation(client: TestClient, token: str) -> str:
    created = client.post("/api/v1/mentor/conversations", headers=bearer(token))
    assert created.status_code == 201, created.text
    return created.json()["id"]


def _ask(client: TestClient, token: str, conversation_id: str, text: str):
    return client.post(
        f"/api/v1/mentor/conversations/{conversation_id}/messages", json={"content": text}, headers=bearer(token)
    )


def _context_for(email: str) -> dict:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        return build_context(db, user)


def test_conversations_are_private(client: TestClient) -> None:
    owner = auth(client, "mentor-owner@example.com")
    other = auth(client, "mentor-other@example.com")
    conversation_id = _conversation(client, owner)
    assert _ask(client, owner, conversation_id, "hello").status_code == 200
    assert client.get(f"/api/v1/mentor/conversations/{conversation_id}", headers=bearer(other)).status_code == 404
    assert _ask(client, other, conversation_id, "hi").status_code == 404
    assert client.delete(f"/api/v1/mentor/conversations/{conversation_id}", headers=bearer(other)).status_code == 404
    assert client.get("/api/v1/mentor/conversations", headers=bearer(other)).json() == []
    listing = client.get("/api/v1/mentor/conversations", headers=bearer(owner)).json()
    assert [item["id"] for item in listing] == [conversation_id]
    assert client.get("/api/v1/mentor/conversations").status_code == 401


def test_demo_mode_is_explicit_and_uses_the_roadmap(client: TestClient, monkeypatch) -> None:
    token, _fake = setup_roadmap(client, monkeypatch, "mentor-demo@example.com")
    assert client.get("/api/v1/mentor/status", headers=bearer(token)).json()["mode"] == "demo"
    next_task = client.get("/api/v1/dashboard", headers=bearer(token)).json()["next_task"]
    conversation_id = _conversation(client, token)
    reply = _ask(client, token, conversation_id, "What should I focus on this week?").json()
    assistant = reply["assistant_message"]
    assert assistant["provider"] == "demo"
    assert "Demo mode" in assistant["content"]
    assert next_task["title"] in assistant["content"]
    detail = client.get(f"/api/v1/mentor/conversations/{conversation_id}", headers=bearer(token)).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    assert detail["title"].startswith("What should I focus")


def test_context_is_scoped_to_the_user(client: TestClient, monkeypatch) -> None:
    setup_roadmap(client, monkeypatch, "ctx-a@example.com")
    auth(client, "ctx-b@example.com")
    a = _context_for("ctx-a@example.com")
    b = _context_for("ctx-b@example.com")
    assert a["profile"]["target_career"] == "Backend Engineer"
    assert a["roadmap"]["total_tasks"] > 0
    assert b == {"profile": None, "assessment": None, "roadmap": None, "resume": None}
    assert "Asha" not in context_text(b)


def test_live_answers_receive_context_and_progress(client: TestClient, monkeypatch) -> None:
    token, _fake = setup_roadmap(client, monkeypatch, "mentor-live@example.com")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    seen: list[list[dict]] = []

    def fake_chat(messages, **_kwargs):
        seen.append(messages)
        return "Start with the next roadmap task."

    monkeypatch.setattr("app.llm.chat", fake_chat)
    roadmap = client.get("/api/v1/roadmaps/current", headers=bearer(token)).json()
    first, second = roadmap["tasks"][0], roadmap["tasks"][1]
    conversation_id = _conversation(client, token)

    answer = _ask(client, token, conversation_id, "What next?").json()["assistant_message"]
    assert answer["provider"] == "openai"
    system = seen[-1][0]["content"]
    assert "<user_context>" in system and "Backend Engineer" in system and first["title"] in system
    assert "Python (3/5)" in system  # self-reported skills reach the model

    client.patch(f"/api/v1/tasks/{first['id']}", json={"status": "completed"}, headers=bearer(token))
    _ask(client, token, conversation_id, "What now?")
    system = seen[-1][0]["content"]
    assert f"1/{len(roadmap['tasks'])} tasks completed" in system
    assert "recently completed: " + first["title"] in system
    assert second["title"] in system


def test_history_window_is_bounded(client: TestClient, monkeypatch) -> None:
    token = auth(client, "mentor-window@example.com")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    seen: list[list[dict]] = []
    monkeypatch.setattr("app.llm.chat", lambda messages, **_k: seen.append(messages) or "ok")
    conversation_id = _conversation(client, token)
    for index in range(HISTORY_WINDOW + 4):
        assert _ask(client, token, conversation_id, f"question {index}").status_code == 200
    assert len(seen[-1]) <= HISTORY_WINDOW + 1  # system prompt + bounded history


def test_model_failure_keeps_the_question_and_labels_the_fallback(client: TestClient, monkeypatch) -> None:
    token = auth(client, "mentor-fail@example.com")
    assert client.put("/api/v1/profile", json=PROFILE, headers=bearer(token)).status_code == 200
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    def boom(*_args, **_kwargs):
        raise LLMError("timeout")

    monkeypatch.setattr("app.llm.chat", boom)
    conversation_id = _conversation(client, token)
    reply = _ask(client, token, conversation_id, "Am I ready to apply for internships?")
    assert reply.status_code == 200
    assistant = reply.json()["assistant_message"]
    assert assistant["provider"] == "demo"
    assert assistant["notice"]
    assert "cannot verify readiness" in assistant["content"]
    detail = client.get(f"/api/v1/mentor/conversations/{conversation_id}", headers=bearer(token)).json()
    assert len(detail["messages"]) == 2


def test_message_validation(client: TestClient) -> None:
    token = auth(client, "mentor-valid@example.com")
    conversation_id = _conversation(client, token)
    assert _ask(client, token, conversation_id, "").status_code == 422
    assert _ask(client, token, conversation_id, "   ").status_code == 422
    assert _ask(client, token, conversation_id, "x" * 2001).status_code == 422
