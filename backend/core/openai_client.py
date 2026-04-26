"""OpenAI client factory and JSON-extraction helpers.

The installed OpenAI/httpx versions in some local environments disagree about
the removed `proxies=` httpx keyword. Passing an explicit AsyncClient avoids
OpenAI's compatibility wrapper and keeps all agents on one construction path.

Gemma models (gemma-*) served via the Google AI OpenAI-compatible endpoint do
not support ``response_format={"type":"json_object"}``.  Call
``json_response_format()`` to get the right kwarg dict for the active model,
and ``extract_json`` to strip any markdown fences from the raw response.
"""
from __future__ import annotations

import json
import re

import httpx
from openai import AsyncOpenAI

from config import settings

_GEMMA_PREFIX = "gemma-"


def make_async_openai() -> AsyncOpenAI:
    kwargs: dict = {
        "api_key": settings.openai_api_key,
        "http_client": httpx.AsyncClient(timeout=120.0, follow_redirects=True),
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return AsyncOpenAI(**kwargs)


def is_gemma(model: str = "") -> bool:
    return (model or settings.openai_model).lower().startswith(_GEMMA_PREFIX)


def supports_json_mode(model: str = "") -> bool:
    return not is_gemma(model)


def json_response_format() -> dict:
    """Return the ``response_format`` kwarg dict, or ``{}`` for Gemma models."""
    if supports_json_mode():
        return {"response_format": {"type": "json_object"}}
    return {}


def build_messages(system: str, user: str) -> list[dict]:
    """Build a messages list compatible with the active model.

    Gemma models reject a ``system`` role; fold the system prompt into the
    first user message instead so the model still gets the instructions.
    """
    if is_gemma():
        return [{"role": "user", "content": f"{system}\n\n{user}"}]
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
# Matches backslashes NOT followed by a valid JSON escape character.
_INVALID_ESCAPE_RE = re.compile(r'\\(?!["\\/bfnrtu])')


def _fix_escapes(s: str) -> str:
    """Double-escape lone backslashes that would make JSON invalid (e.g. TeX)."""
    return _INVALID_ESCAPE_RE.sub(r"\\\\", s)


def extract_json(raw: str) -> str:
    """Strip markdown code fences, fix TeX escapes, return the inner JSON string."""
    raw = raw.strip()
    m = _FENCE_RE.search(raw)
    if m:
        raw = m.group(1).strip()
    else:
        start = min(
            (raw.find(c) for c in ("{", "[") if raw.find(c) != -1),
            default=-1,
        )
        end = max(raw.rfind("}"), raw.rfind("]"))
        if start != -1 and end > start:
            raw = raw[start : end + 1]
    return _fix_escapes(raw)
