import json
import logging

import httpx
import pytest
from app.config import settings
from app.llm import LLMError, _extract_error_diagnostics, chat, chat_json


def test_extract_error_diagnostics_handles_groq_400():
    groq_400_body = {
        "error": {
            "message": "Failed to generate JSON. Please adjust your prompt.",
            "type": "invalid_request_error",
            "code": "json_validate_failed",
            "failed_generation": "max completion tokens reached before generating a valid document",
        }
    }
    response = httpx.Response(
        status_code=400,
        headers={"x-request-id": "req_test_12345"},
        content=json.dumps(groq_400_body).encode("utf-8"),
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    msg, err_type, err_code, failed_gen = _extract_error_diagnostics(response)
    assert "Failed to generate JSON" in msg
    assert err_type == "invalid_request_error"
    assert err_code == "json_validate_failed"
    assert "max completion tokens reached" in failed_gen


def test_chat_payload_uses_max_completion_tokens(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "gsk_dummy_test_secret_key_12345")
    captured_payload = None

    def fake_post(url, headers, json):
        nonlocal captured_payload
        captured_payload = json
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-test",
                "choices": [{"message": {"role": "assistant", "content": '{"result": "ok"}'}}],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("httpx.Client.post", lambda self, url, headers, json: fake_post(url, headers, json))

    chat([{"role": "user", "content": "Return JSON"}], json_mode=True, max_completion_tokens=5000)

    assert captured_payload is not None
    assert "max_completion_tokens" in captured_payload
    assert captured_payload["max_completion_tokens"] == 5000
    assert captured_payload["response_format"] == {"type": "json_object"}


def test_chat_maps_deprecated_max_tokens_to_max_completion_tokens(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "gsk_dummy_test_secret_key_12345")
    captured_payload = None

    def fake_post(url, headers, json):
        nonlocal captured_payload
        captured_payload = json
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-test",
                "choices": [{"message": {"role": "assistant", "content": "Hello"}}],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("httpx.Client.post", lambda self, url, headers, json: fake_post(url, headers, json))

    chat([{"role": "user", "content": "Hello"}], max_tokens=2500)

    assert captured_payload is not None
    assert "max_completion_tokens" in captured_payload
    assert captured_payload["max_completion_tokens"] == 2500


def test_groq_400_diagnostic_logging_does_not_leak_secrets(monkeypatch, caplog):
    monkeypatch.setattr(settings, "groq_api_key", "gsk_super_secret_key_that_must_not_leak")
    secret_prompt = "PRIVATE_RESUME_TEXT_FOR_SECRET_CANDIDATE"

    groq_err_resp = httpx.Response(
        status_code=400,
        headers={"x-request-id": "req_groq_diag_999"},
        json={
            "error": {
                "message": "Failed to generate JSON. max completion tokens reached.",
                "type": "invalid_request_error",
                "code": "json_validate_failed",
                "failed_generation": "max completion tokens reached before generating a valid document",
            }
        },
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    monkeypatch.setattr("httpx.Client.post", lambda *a, **k: groq_err_resp)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(LLMError) as exc_info:
            chat_json([{"role": "user", "content": secret_prompt}], max_completion_tokens=100)

    # 1. Error raised should not expose internal prompts or API keys
    assert "gsk_super_secret_key" not in str(exc_info.value)
    assert secret_prompt not in str(exc_info.value)
    assert "Groq returned HTTP 400" in str(exc_info.value)

    # 2. Log must contain diagnostic metadata (request_id, status, type, code)
    log_text = caplog.text
    assert "req_groq_diag_999" in log_text
    assert "status=400" in log_text
    assert "json_validate_failed" in log_text
    assert "invalid_request_error" in log_text

    # 3. Log must never leak the API key or secret resume content
    assert "gsk_super_secret_key" not in log_text
    assert secret_prompt not in log_text
