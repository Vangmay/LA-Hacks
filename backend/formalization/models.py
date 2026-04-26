from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class FormalizationStatus(str, Enum):
    QUEUED = "queued"
    BUILDING_CONTEXT = "building_context"
    LLM_THINKING = "llm_thinking"
    AXLE_RUNNING = "axle_running"
    COMPLETE = "complete"
    ERROR = "error"
    SKIPPED = "skipped"


class FormalizationLabel(str, Enum):
    FULLY_VERIFIED = "fully_verified"
    CONDITIONALLY_VERIFIED = "conditionally_verified"
    FORMALIZED_ONLY = "formalized_only"
    DISPROVED = "disproved"
    FORMALIZATION_FAILED = "formalization_failed"
    NOT_A_THEOREM = "not_a_theorem"
    GAVE_UP = "gave_up"


class ToolCallRecord(BaseModel):
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: Literal["pending", "success", "error"] = "pending"
    result_summary: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class FormalizationArtifact(BaseModel):
    artifact_id: str
    kind: Literal["spec", "proof", "helper_lemma", "merged"]
    lean_code: str
    axle_check_okay: Optional[bool] = None
    axle_verify_okay: Optional[bool] = None
    iteration: int
    path: Optional[str] = None


class AtomFormalization(BaseModel):
    atom_id: str
    paper_id: str
    status: FormalizationStatus = FormalizationStatus.QUEUED
    label: Optional[FormalizationLabel] = None
    rationale: Optional[str] = None
    artifacts: list[FormalizationArtifact] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    llm_messages: list[dict[str, Any]] = Field(default_factory=list)
    llm_call_count: int = 0
    used_assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class FormalizationRun(BaseModel):
    run_id: str
    job_id: str
    paper_id: str
    selected_atom_ids: list[str]
    status: FormalizationStatus = FormalizationStatus.QUEUED
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    atom_formalizations: dict[str, AtomFormalization] = Field(default_factory=dict)
    summary: dict[str, int] = Field(default_factory=dict)
    error: Optional[str] = None
    options: dict[str, Any] = Field(default_factory=dict)


class FormalizationOptions(BaseModel):
    atom_ids: Optional[list[str]] = None
    options: dict[str, Any] = Field(default_factory=dict)
