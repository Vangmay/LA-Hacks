from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[1]


class AxleSettings(BaseSettings):
    axle_api_key: str = ""
    axle_api_url: str = "https://axle.axiommath.ai"
    axle_max_concurrency: int = 2
    axle_timeout_seconds: float = 120.0

    formalization_parallelism: int = 2
    formalization_max_iterations_per_atom: int = 10000
    formalization_max_axle_calls_per_atom: int = 10000
    formalization_lean_environment: str = "lean-4.28.0"

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        extra="ignore",
    )


formalization_settings = AxleSettings()
