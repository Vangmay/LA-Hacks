"""Typed contracts for research deep-dive orchestration."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResearchStage(str, Enum):
    BOOTSTRAP = "bootstrap"
    INVESTIGATOR_PLANNING = "investigator_planning"
    SUBAGENT_RESEARCH = "subagent_research"
    INVESTIGATOR_SYNTHESIS = "investigator_synthesis"
    CROSS_INVESTIGATOR_DEEP_DIVE = "cross_investigator_deep_dive"
    CRITIQUE = "critique"
    FINALIZATION = "finalization"


class AgentModelRole(str, Enum):
    DIRECTOR = "director"
    INVESTIGATOR = "investigator"
    SEARCH_SUBAGENT = "search_subagent"
    EXTRACTION_HELPER = "extraction_helper"
    FORMATTING_HELPER = "formatting_helper"
    DEDUPE_HELPER = "dedupe_helper"
    METADATA_CLASSIFIER = "metadata_classifier"
    CRITIQUE = "critique"
    REVISION = "revision"
    FINALIZATION = "finalization"


class AgentExitReason(str, Enum):
    COMPLETED = "completed"
    MAX_TOOL_CALLS_REACHED = "max_tool_calls_reached"
    DRY_RUN = "dry_run"
    ERROR = "error"


class ToolSpec(BaseModel):
    name: str
    category: str
    purpose: str
    endpoint: Optional[str] = None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    input_example: dict[str, Any] = Field(default_factory=dict)
    output_example: dict[str, Any] = Field(default_factory=dict)
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)
    fallback_tools: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ResearchTaste(BaseModel):
    taste_id: str
    label: str
    archetype_label: str = ""
    research_zone: str = "general"
    diversity_roles: list[str] = Field(default_factory=list)
    best_for: list[str] = Field(default_factory=list)
    worldview: str
    search_biases: list[str]
    typical_queries: list[str] = Field(default_factory=list)
    evidence_preferences: list[str]
    proposal_style: str = ""
    failure_modes_to_watch: list[str]
    must_not_do: list[str] = Field(default_factory=list)
    required_counterbalance: str


class SubagentPlan(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    subagent_id: str
    investigator_id: str
    section_id: str
    section_title: str
    taste: ResearchTaste
    workspace_path: Path
    system_prompt: str
    allowed_tools: list[str]
    max_tool_calls: int
    model_role: AgentModelRole = AgentModelRole.SEARCH_SUBAGENT


class InvestigatorPlan(BaseModel):
    investigator_id: str
    section_id: str
    section_title: str
    workspace_path: Path
    system_prompt: str
    subagents: list[SubagentPlan]


class AgentRunResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    agent_id: str
    stage: ResearchStage
    exit_reason: AgentExitReason
    tool_calls_used: int
    workspace_path: Path
    artifacts: list[Path] = Field(default_factory=list)
    summary: str = ""
    error: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    llm_steps_used: int = 0
    tool_trace_path: Optional[Path] = None


class CritiqueResult(BaseModel):
    critic_id: str
    lens: str
    workspace_path: Path
    artifact_path: Path
    summary: str


class DeepDiveRunRequest(BaseModel):
    run_id: str
    arxiv_url: str
    paper_id: Optional[str] = None
    section_titles: list[str] = Field(default_factory=list)
    research_brief: str = ""
    research_objective: Literal["literature_review", "novelty_ideation"] = "novelty_ideation"
    mode: Literal["dry_run", "live"] = "dry_run"


class DeepDiveRunResult(BaseModel):
    run_id: str
    status: Literal["success", "error"]
    workspace_path: Path
    stages_completed: list[ResearchStage]
    investigators: list[InvestigatorPlan]
    subagent_results: list[AgentRunResult]
    investigator_syntheses: list[AgentRunResult]
    critiques: list[CritiqueResult]
    final_report_path: Optional[Path] = None
    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = None
