"""Research deep-dive orchestration scaffold.

This package is intentionally isolated from the implemented v0.4 review
pipeline. It defines the future research-mode control plane: prompt loading,
tool contracts, per-agent workspaces, configurable budgets, and post-research
critique/finalization stages.
"""

from .config import DeepDiveConfig, ModelProfile
from .llm import DeepDiveLLMProvider
from .models import (
    AgentModelRole,
    CritiqueResult,
    DeepDiveRunRequest,
    DeepDiveRunResult,
    InvestigatorPlan,
    ResearchTaste,
    SubagentPlan,
    ToolSpec,
)
from .orchestrator import DeepDiveOrchestrator, build_subagent_context_packet
from .personas import (
    classify_research_zone,
    generate_research_tastes,
    missing_diversity_roles,
    persona_library_summary,
    validate_research_taste_roster,
)
from .prompts import PromptBook
from .tools import build_default_tool_registry

__all__ = [
    "CritiqueResult",
    "DeepDiveConfig",
    "DeepDiveLLMProvider",
    "DeepDiveOrchestrator",
    "DeepDiveRunRequest",
    "DeepDiveRunResult",
    "AgentModelRole",
    "InvestigatorPlan",
    "ModelProfile",
    "PromptBook",
    "ResearchTaste",
    "SubagentPlan",
    "ToolSpec",
    "build_default_tool_registry",
    "build_subagent_context_packet",
    "classify_research_zone",
    "generate_research_tastes",
    "missing_diversity_roles",
    "persona_library_summary",
    "validate_research_taste_roster",
]
