"""OpenAI client factory.

The installed OpenAI/httpx versions in some local environments disagree about
the removed `proxies=` httpx keyword. Passing an explicit AsyncClient avoids
OpenAI's compatibility wrapper and keeps all agents on one construction path.
"""
from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from config import settings


def make_async_openai() -> AsyncOpenAI:
    api_key = settings.openai_api_key
    base_url = settings.openai_base_url
    default_headers: dict[str, str] | None = None

    if _use_openrouter():
        api_key = settings.openrouter_api_key
        base_url = settings.openrouter_base_url
        default_headers = {
            "HTTP-Referer": settings.openrouter_http_referer,
            "X-OpenRouter-Title": settings.openrouter_title,
        }

    kwargs = {
        "api_key": api_key,
        "http_client": httpx.AsyncClient(
            timeout=settings.openai_timeout_seconds,
            follow_redirects=True,
        ),
    }
    if base_url:
        kwargs["base_url"] = base_url
    if default_headers:
        kwargs["default_headers"] = default_headers
    return AsyncOpenAI(
        **kwargs,
    )


def _use_openrouter() -> bool:
    if not settings.openrouter_api_key:
        return False
    if settings.openai_base_url:
        return settings.openai_base_url.rstrip("/") == settings.openrouter_base_url.rstrip("/")
    return settings.openai_model.startswith("google/")
