from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from config import settings


_BACKEND_DIR = Path(__file__).resolve().parents[1]


class AxleSettings(BaseSettings):
    axle_api_key: str = ""
    axle_api_url: str = "https://axle.axiommath.ai"
    axle_max_concurrency: int = settings.deepdive_max_parallel_subagents
    axle_timeout_seconds: float = 120.0

    formalization_parallelism: int = settings.deepdive_max_parallel_subagents
    formalization_max_iterations_per_atom: int = 10000
    formalization_max_axle_calls_per_atom: int = 10000
    formalization_lean_environment: str = "lean-4.28.0"
    formalization_model_provider: str = settings.deepdive_thinking_provider
    formalization_model: str = settings.deepdive_thinking_model or settings.openai_model
    formalization_api_key_env: str = settings.deepdive_thinking_api_key_env
    formalization_base_url: str = settings.deepdive_thinking_base_url or settings.openai_base_url
    formalization_reasoning_effort: str = settings.deepdive_thinking_reasoning_effort
    formalization_max_output_tokens: int = settings.deepdive_max_output_tokens_thinking
    formalization_model_timeout_seconds: float = settings.deepdive_model_timeout_seconds
    formalization_model_max_retries: int = max(20, settings.deepdive_model_max_retries)
    formalization_model_retry_max_delay_seconds: float = settings.deepdive_model_retry_max_delay_seconds
    formalization_model_min_interval_seconds: float = settings.deepdive_thinking_min_interval_seconds

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        extra="ignore",
    )

    def runtime_metadata(self) -> dict[str, str | int | float]:
        return {
            "model_provider": self.formalization_model_provider,
            "model_name": self.formalization_model,
            "api_key_env": self.formalization_api_key_env,
            "reasoning_effort": self.formalization_reasoning_effort,
            "max_output_tokens": self.formalization_max_output_tokens,
            "model_timeout_seconds": self.formalization_model_timeout_seconds,
            "model_max_retries": self.formalization_model_max_retries,
            "model_min_interval_seconds": self.formalization_model_min_interval_seconds,
            "parallelism": self.formalization_parallelism,
            "max_iterations_per_atom": self.formalization_max_iterations_per_atom,
            "max_axle_calls_per_atom": self.formalization_max_axle_calls_per_atom,
            "axle_max_concurrency": self.axle_max_concurrency,
            "axle_timeout_seconds": self.axle_timeout_seconds,
            "lean_environment": self.formalization_lean_environment,
        }


formalization_settings = AxleSettings()
