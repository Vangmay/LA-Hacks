"""Research deep-dive orchestration scaffold.

This package is intentionally isolated from the implemented v0.4 review
pipeline. It defines the future research-mode control plane: prompt loading,
tool contracts, per-agent workspaces, configurable budgets, and post-research
critique/finalization stages.
"""

from .config import DeepDiveConfig
from .models import (
    CritiqueResult,
    DeepDiveRunRequest,
    DeepDiveRunResult,
    InvestigatorPlan,
    ResearchTaste,
    SubagentPlan,
    ToolSpec,
)
from .orchestrator import DeepDiveOrchestrator
from .personas import classify_research_zone, generate_research_tastes
from .prompts import PromptBook
from .tools import build_default_tool_registry

__all__ = [
    "CritiqueResult",
    "DeepDiveConfig",
    "DeepDiveOrchestrator",
    "DeepDiveRunRequest",
    "DeepDiveRunResult",
    "InvestigatorPlan",
    "PromptBook",
    "ResearchTaste",
    "SubagentPlan",
    "ToolSpec",
    "build_default_tool_registry",
    "classify_research_zone",
    "generate_research_tastes",
]
