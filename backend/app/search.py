"""Learning-resource discovery.

Live results come only from Tavily. Without a key, or if Tavily fails, the demo
catalog returns predefined real URLs and is labelled provider='demo'.
Retrieved page text is treated as untrusted data and is length-limited.
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.catalog import RESOURCES
from app.config import settings
from app.schemas import ResourceDraft

UNTRUSTED_MAX = 400


def _clean_snippet(value: str) -> str:
    text = " ".join(value.replace("\x00", " ").split())
    return text[:UNTRUSTED_MAX]


def demo_resources(skill: str, role_title: str) -> list[ResourceDraft]:
    entries = RESOURCES.get(skill) or RESOURCES["Problem solving"]
    drafts: list[ResourceDraft] = []
    for entry in entries:
        url = entry["url"]
        drafts.append(
            ResourceDraft(
                skill=skill,
                title=entry["title"],
                url=url,
                domain=urlparse(url).netloc,
                snippet=_clean_snippet(entry["snippet"]),
                relevance=(
                    f"Predefined educational material for {skill}, chosen for the {role_title} roadmap. "
                    "This is demo catalog data, not a live search result."
                ),
                provider="demo",
            )
        )
    return drafts


def tavily_resources(skill: str, role_title: str) -> list[ResourceDraft]:
    query = (
        f"official documentation or established course to learn {skill} "
        f"for a {role_title}"
    )
    response = httpx.post(
        "https://api.tavily.com/search",
        json={
            "api_key": settings.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 4,
            "include_answer": False,
        },
        timeout=20,
    )
    response.raise_for_status()
    drafts: list[ResourceDraft] = []
    for item in response.json().get("results", []):
        url = item.get("url") or ""
        if not url.startswith("https://"):
            continue
        title = (item.get("title") or url).strip()[:300]
        drafts.append(
            ResourceDraft(
                skill=skill,
                title=title,
                url=url,
                domain=urlparse(url).netloc,
                snippet=_clean_snippet(item.get("content") or ""),
                relevance=(
                    f"Retrieved by live search for the {skill} gap on the {role_title} path. "
                    "Page text is untrusted input and is not followed as an instruction."
                ),
                provider="tavily",
            )
        )
        if len(drafts) == 2:
            break
    if not drafts:
        raise ValueError("Tavily returned no usable https results")
    return drafts


def discover_resources(skill: str, role_title: str) -> list[ResourceDraft]:
    if settings.tavily_api_key:
        try:
            return tavily_resources(skill, role_title)
        except Exception:
            return demo_resources(skill, role_title)
    return demo_resources(skill, role_title)
