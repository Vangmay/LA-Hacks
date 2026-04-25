"""Config for the research deep-dive control plane."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from config import settings


class DeepDiveConfig(BaseModel):
    """Runtime budgets and filesystem layout for research deep-dive runs.

    Values are copied from global settings by default so deployments can tune
    behavior from environment variables without editing orchestration code.
    """

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
            }
        )
