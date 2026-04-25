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
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        http_client=httpx.AsyncClient(timeout=60.0, follow_redirects=True),
    )
