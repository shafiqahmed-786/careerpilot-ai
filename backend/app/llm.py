"""Thin Groq chat client used by the mentor, resume analysis and roadmap generation.

Calls Groq's OpenAI-compatible /chat/completions API with configured model and timeout.
Prompts and responses are never logged, because they contain profile and resume content.
API keys are never exposed in error messages or logs.
Callers must treat any failure as "use the deterministic fallback".
"""

from __future__ import annotations

import json
import logging
import re
import time

import httpx

from app.config import settings

logger = logging.getLogger("careerpilot.llm")


class LLMError(Exception):
    """Raised for any failure to obtain a usable model response."""


def available() -> bool:
    return bool(settings.groq_api_key)


def _extract_json_string(raw: str) -> str:
    """Extract valid JSON from raw model output, handling fences and preamble/postamble text."""
    cleaned = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace : last_brace + 1].strip()
    return cleaned


def chat(
    messages: list[dict],
    *,
    json_mode: bool = False,
    temperature: float = 0.3,
    max_tokens: int = 1200,
    timeout: float = 45.0,
    max_retries: int = 1,
) -> str:
    if not settings.groq_api_key:
        logger.warning("LLM request skipped: Groq is not configured")
        raise LLMError("Groq is not configured")

    logger.info("Executing LLM request provider=groq model=%s json_mode=%s", settings.groq_model, json_mode)

    payload: dict = {
        "model": settings.groq_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    url = f"{settings.groq_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=headers, json=payload)

            if response.status_code == 401:
                logger.error("Groq authentication failed provider=groq model=%s status=401", settings.groq_model)
                raise LLMError("Groq authentication failed: invalid API key")
            elif response.status_code == 404:
                logger.error("Groq model not found provider=groq model=%s status=404", settings.groq_model)
                raise LLMError(f"Groq model '{settings.groq_model}' is unavailable or not found")
            elif response.status_code == 429:
                logger.warning("Groq rate limit exceeded provider=groq model=%s status=429", settings.groq_model)
                raise LLMError("Groq rate limit or quota exceeded")
            elif response.status_code >= 500 and attempt < max_retries:
                logger.warning("Groq server error status=%s retry attempt=%s", response.status_code, attempt + 1)
                time.sleep(1.0)
                continue

            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                logger.warning("Groq response was empty provider=groq model=%s", settings.groq_model)
                raise LLMError("The Groq response was empty")

            logger.info("LLM request succeeded provider=groq model=%s status=%s", settings.groq_model, response.status_code)
            return content

        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(1.0)
                continue
            logger.warning("Groq request timed out provider=groq model=%s", settings.groq_model)
            raise LLMError("The Groq request timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("Groq HTTP error provider=groq model=%s status=%s", settings.groq_model, exc.response.status_code)
            raise LLMError(f"Groq returned HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(1.0)
                continue
            logger.warning("Groq response read error provider=groq model=%s err=%s", settings.groq_model, str(exc)[:100])
            raise LLMError("The Groq response could not be read") from exc

    logger.warning("Groq request failed after retries provider=groq model=%s", settings.groq_model)
    raise LLMError(f"Groq request failed: {last_exc}")


def chat_json(messages: list[dict], **kwargs) -> dict:
    content = chat(messages, json_mode=True, **kwargs)
    cleaned = _extract_json_string(content)
    try:
        data = json.loads(cleaned)
    except ValueError as exc:
        raise LLMError("The model did not return valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("The model returned JSON that is not an object")
    return data
