"""Evidence pointers.

Every challenge, rebuttal, check, and verdict references `Evidence` so the
final report is an auditable trail rather than a free-form essay.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EvidenceSourceType(str, Enum):
    PAPER_SPAN = "paper_span"
    EQUATION = "equation"
    CITATION = "citation"

    ALGEBRAIC_CHECK = "algebraic_check"
    NUMERIC_PROBE = "numeric_probe"
    PRIOR_ART = "prior_art"

    AGENT_REASONING = "agent_reasoning"
    USER_NOTE = "user_note"


class Evidence(BaseModel):
    evidence_id: str
    source_type: EvidenceSourceType

    text: str

    paper_id: Optional[str] = None
    atom_id: Optional[str] = None
    equation_id: Optional[str] = None
    citation_id: Optional[str] = None
    check_id: Optional[str] = None

    url: Optional[str] = None
    external_paper_id: Optional[str] = None

    confidence: float = Field(ge=0.0, le=1.0)

    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCallTrace(BaseModel):
    trace_id: str
    agent_id: str
    tool_name: str

    input_summary: str
    output_summary: str

    started_at: datetime
    finished_at: datetime

    status: str
    error: Optional[str] = None
