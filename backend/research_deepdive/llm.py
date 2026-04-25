"""Deep-dive-only OpenAI-compatible LLM client."""
from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import httpx
from openai import AsyncOpenAI

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

        response = await asyncio.wait_for(
            self._client_for(profile).chat.completions.create(**kwargs),
            timeout=profile.timeout_seconds,
        )
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
        response = await asyncio.wait_for(
            self._client_for(profile).chat.completions.create(**kwargs),
            timeout=profile.timeout_seconds,
        )
        return strip_provider_thoughts(response.choices[0].message.content or "")

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
