"""Config for the research deep-dive control plane."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from config import settings


class ModelProfile(BaseModel):
    """OpenAI-compatible model settings for one orchestration role class."""

    model_config = ConfigDict(protected_namespaces=())

    provider: str
    model: str
    api_key_env: str
    base_url: str = ""
    reasoning_effort: str = ""
    max_output_tokens: int = 2048
    timeout_seconds: float = 180.0


class DeepDiveConfig(BaseModel):
    """Runtime budgets and filesystem layout for research deep-dive runs.

    Values are copied from global settings by default so deployments can tune
    behavior from environment variables without editing orchestration code.
    """

    model_config = ConfigDict(protected_namespaces=())

    workspace_root: Path = Field(default_factory=lambda: Path(settings.deepdive_workspace_root))
    max_investigators: int = Field(default_factory=lambda: settings.deepdive_max_investigators)
    subagents_per_investigator: int = Field(
        default_factory=lambda: settings.deepdive_subagents_per_investigator
    )
    min_personas_per_investigator: int = Field(
        default_factory=lambda: settings.deepdive_min_personas_per_investigator
    )
    max_personas_per_investigator: int = Field(
        default_factory=lambda: settings.deepdive_max_personas_per_investigator
    )
    require_persona_diversity: bool = Field(
        default_factory=lambda: settings.deepdive_require_persona_diversity
    )
    subagent_max_tool_calls: int = Field(
        default_factory=lambda: settings.deepdive_subagent_max_tool_calls
    )
    investigator_max_rounds: int = Field(
        default_factory=lambda: settings.deepdive_investigator_max_rounds
    )
    max_parallel_subagents: int = Field(
        default_factory=lambda: settings.deepdive_max_parallel_subagents
    )
    stage_timeout_seconds: int = Field(
        default_factory=lambda: settings.deepdive_stage_timeout_seconds
    )
    default_search_limit: int = Field(
        default_factory=lambda: settings.deepdive_default_search_limit
    )
    http_timeout_seconds: float = Field(
        default_factory=lambda: settings.deepdive_http_timeout_seconds
    )
    model_timeout_seconds: float = Field(
        default_factory=lambda: settings.deepdive_model_timeout_seconds
    )
    tool_result_char_limit: int = Field(
        default_factory=lambda: settings.deepdive_tool_result_char_limit
    )
    subagent_max_steps: int = Field(
        default_factory=lambda: settings.deepdive_subagent_max_steps
    )
    semantic_scholar_min_interval_seconds: float = Field(
        default_factory=lambda: settings.deepdive_semantic_scholar_min_interval_seconds
    )
    semantic_scholar_max_retries: int = Field(
        default_factory=lambda: settings.deepdive_semantic_scholar_max_retries
    )
    llm_action_protocol: Literal["json_action"] = Field(
        default_factory=lambda: settings.deepdive_llm_action_protocol
    )
    thinking_profile: ModelProfile = Field(
        default_factory=lambda: ModelProfile(
            provider=settings.deepdive_thinking_provider,
            model=settings.deepdive_thinking_model or settings.openai_model,
            api_key_env=settings.deepdive_thinking_api_key_env,
            base_url=settings.deepdive_thinking_base_url or settings.openai_base_url,
            reasoning_effort=settings.deepdive_thinking_reasoning_effort,
            max_output_tokens=settings.deepdive_max_output_tokens_thinking,
            timeout_seconds=settings.deepdive_model_timeout_seconds,
        )
    )
    light_profile: ModelProfile = Field(
        default_factory=lambda: ModelProfile(
            provider=settings.deepdive_light_provider,
            model=settings.deepdive_light_model,
            api_key_env=settings.deepdive_light_api_key_env,
            base_url=settings.deepdive_light_base_url,
            reasoning_effort=settings.deepdive_light_reasoning_effort,
            max_output_tokens=settings.deepdive_max_output_tokens_light,
            timeout_seconds=settings.deepdive_model_timeout_seconds,
        )
    )

    def normalized(self) -> "DeepDiveConfig":
        min_personas = max(1, self.min_personas_per_investigator)
        max_personas = max(min_personas, self.max_personas_per_investigator)
        return self.model_copy(
            update={
                "max_investigators": max(1, self.max_investigators),
                "subagents_per_investigator": max(1, self.subagents_per_investigator),
                "min_personas_per_investigator": min_personas,
                "max_personas_per_investigator": max_personas,
                "subagent_max_tool_calls": max(1, self.subagent_max_tool_calls),
                "investigator_max_rounds": max(1, self.investigator_max_rounds),
                "max_parallel_subagents": max(1, self.max_parallel_subagents),
                "stage_timeout_seconds": max(1, self.stage_timeout_seconds),
                "default_search_limit": max(1, self.default_search_limit),
                "http_timeout_seconds": max(1.0, self.http_timeout_seconds),
                "model_timeout_seconds": max(1.0, self.model_timeout_seconds),
                "tool_result_char_limit": max(1000, self.tool_result_char_limit),
                "subagent_max_steps": max(1, self.subagent_max_steps),
                "semantic_scholar_min_interval_seconds": max(
                    0.0, self.semantic_scholar_min_interval_seconds
                ),
                "semantic_scholar_max_retries": max(1, self.semantic_scholar_max_retries),
                "thinking_profile": self.thinking_profile.model_copy(
                    update={
                        "model": self.thinking_profile.model or settings.openai_model,
                        "max_output_tokens": max(256, self.thinking_profile.max_output_tokens),
                        "timeout_seconds": max(1.0, self.thinking_profile.timeout_seconds),
                    }
                ),
                "light_profile": self.light_profile.model_copy(
                    update={
                        "max_output_tokens": max(256, self.light_profile.max_output_tokens),
                        "timeout_seconds": max(1.0, self.light_profile.timeout_seconds),
                    }
                ),
            }
        )
