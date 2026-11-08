"""Thin OpenAI chat client used by the mentor, resume analysis and roadmap generation.

Every call has a hard timeout. Prompts and responses are never logged, because they contain
profile and resume content. Callers must treat any failure as "use the deterministic fallback".
"""

from __future__ import annotations

import json

import httpx

from app.config import settings


class LLMError(Exception):
    """Raised for any failure to obtain a usable model response."""


def available() -> bool:
    return bool(settings.openai_api_key)


def chat(
    messages: list[dict],
    *,
    json_mode: bool = False,
    temperature: float = 0.3,
    max_tokens: int = 1200,
    timeout: float = 45.0,
) -> str:
    if not settings.openai_api_key:
        raise LLMError("OpenAI is not configured")
    payload: dict = {
        "model": settings.openai_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        response = httpx.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except httpx.TimeoutException as exc:
        raise LLMError("The OpenAI request timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise LLMError(f"OpenAI returned HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise LLMError("The OpenAI response could not be read") from exc
    if not isinstance(content, str) or not content.strip():
        raise LLMError("The OpenAI response was empty")
    return content


def chat_json(messages: list[dict], **kwargs) -> dict:
    content = chat(messages, json_mode=True, **kwargs)
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise LLMError("The model did not return valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("The model returned JSON that is not an object")
    return data
