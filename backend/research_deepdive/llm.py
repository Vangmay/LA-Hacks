"""Deep-dive-only OpenAI-compatible LLM client."""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time
from typing import Any

import httpx
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from config import settings

from .config import DeepDiveConfig, ModelProfile
from .models import AgentModelRole


THINKING_ROLES = {
    AgentModelRole.DIRECTOR,
    AgentModelRole.INVESTIGATOR,
    AgentModelRole.CRITIQUE,
    AgentModelRole.REVISION,
    AgentModelRole.FINALIZATION,
}

LIGHT_ROLES = {
    AgentModelRole.SEARCH_SUBAGENT,
    AgentModelRole.EXTRACTION_HELPER,
    AgentModelRole.FORMATTING_HELPER,
    AgentModelRole.DEDUPE_HELPER,
    AgentModelRole.METADATA_CLASSIFIER,
}


def _settings_key_value(env_name: str) -> str:
    normalized = env_name.lower()
    if hasattr(settings, normalized):
        return str(getattr(settings, normalized) or "")
    return ""


def resolve_api_key(env_name: str) -> str:
    value = os.getenv(env_name) or _settings_key_value(env_name)
    if not value:
        raise RuntimeError(f"missing API key for {env_name}")
    return value


class DeepDiveLLMProvider:
    """Thin chat-completions wrapper for OpenAI and compatible providers."""

    def __init__(self, config: DeepDiveConfig) -> None:
        self.config = config
        self._clients: dict[str, AsyncOpenAI] = {}
        self._request_locks: dict[str, asyncio.Lock] = {}
        self._last_request_at: dict[str, float] = {}

    def profile_for(self, role: AgentModelRole) -> ModelProfile:
        if role in THINKING_ROLES:
            return self.config.thinking_profile
        if role in LIGHT_ROLES:
            return self.config.light_profile
        raise ValueError(f"unmapped model role: {role}")

    def _client_for(self, profile: ModelProfile) -> AsyncOpenAI:
        key = f"{profile.api_key_env}|{profile.base_url}"
        if key not in self._clients:
            kwargs: dict[str, Any] = {}
            if profile.base_url:
                kwargs["base_url"] = profile.base_url
            self._clients[key] = AsyncOpenAI(
                api_key=resolve_api_key(profile.api_key_env),
                http_client=httpx.AsyncClient(
                    timeout=profile.timeout_seconds,
                    follow_redirects=True,
                ),
                **kwargs,
            )
        return self._clients[key]

    async def chat_json(
        self,
        *,
        role: AgentModelRole,
        messages: list[dict[str, str]],
        require_json: bool = True,
    ) -> dict[str, Any]:
        profile = self.profile_for(role)
        if not profile.model:
            raise RuntimeError(f"missing model name for {role.value}")

        kwargs: dict[str, Any] = {
            "model": profile.model,
            "messages": messages,
            "max_tokens": profile.max_output_tokens,
        }
        if require_json:
            kwargs["response_format"] = {"type": "json_object"}
        if profile.reasoning_effort:
            kwargs["reasoning_effort"] = profile.reasoning_effort

        response = await self._chat_completion(profile, kwargs)
        content = normalize_model_content(response.choices[0].message.content or "")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"{profile.provider}:{profile.model} returned non-JSON content: {content[:500]}"
            ) from exc

    async def chat_markdown(
        self,
        *,
        role: AgentModelRole,
        messages: list[dict[str, str]],
    ) -> str:
        profile = self.profile_for(role)
        if not profile.model:
            raise RuntimeError(f"missing model name for {role.value}")
        kwargs: dict[str, Any] = {
            "model": profile.model,
            "messages": messages,
            "max_tokens": profile.max_output_tokens,
        }
        if profile.reasoning_effort:
            kwargs["reasoning_effort"] = profile.reasoning_effort
        response = await self._chat_completion(profile, kwargs)
        return strip_provider_thoughts(response.choices[0].message.content or "")

    async def _chat_completion(self, profile: ModelProfile, kwargs: dict[str, Any]) -> Any:
        for attempt in range(1, self.config.model_max_retries + 1):
            await self._pace_profile(profile)
            try:
                return await asyncio.wait_for(
                    self._client_for(profile).chat.completions.create(**kwargs),
                    timeout=profile.timeout_seconds,
                )
            except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
                if attempt == self.config.model_max_retries:
                    raise
                await asyncio.sleep(self._retry_delay_seconds(exc, attempt))
        raise RuntimeError("unreachable LLM retry state")

    async def _pace_profile(self, profile: ModelProfile) -> None:
        interval = profile.min_interval_seconds
        if interval <= 0:
            return
        key = f"{profile.api_key_env}|{profile.base_url}|{profile.model}"
        lock = self._request_locks.setdefault(key, asyncio.Lock())
        async with lock:
            elapsed = time.monotonic() - self._last_request_at.get(key, 0.0)
            wait = interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at[key] = time.monotonic()

    def _retry_delay_seconds(self, exc: Exception, attempt: int) -> float:
        retry_after = getattr(getattr(exc, "response", None), "headers", {}).get("retry-after")
        if retry_after:
            try:
                return min(float(retry_after), self.config.model_retry_max_delay_seconds)
            except ValueError:
                pass
        match = re.search(
            r"(?:retry in|try again in|retryDelay['\"]?:\s*['\"]?)(?:\s*)([0-9.]+)s",
            str(exc),
            flags=re.IGNORECASE,
        )
        if match:
            return min(float(match.group(1)), self.config.model_retry_max_delay_seconds)
        base = max(1.0, min(8.0, self.config.model_retry_max_delay_seconds))
        jitter = random.uniform(0.0, 0.25 * base)
        return min(self.config.model_retry_max_delay_seconds, base * (2 ** (attempt - 1)) + jitter)

    async def aclose(self) -> None:
        for client in self._clients.values():
            await client.close()


def strip_provider_thoughts(content: str) -> str:
    """Remove provider-visible thought wrappers before strict JSON parsing."""

    cleaned = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL).strip()
    if cleaned:
        return cleaned
    return content.strip()


def normalize_model_content(content: str) -> str:
    cleaned = strip_provider_thoughts(content)
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return cleaned
