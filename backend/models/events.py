"""SSE events emitted by the review orchestrator."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class GraphNodeKind(str, Enum):
    PAPER = "paper"
    ATOM = "atom"
    CHECK = "check"
    CHALLENGE = "challenge"
    REBUTTAL = "rebuttal"
    VERDICT = "verdict"


class GraphNodeStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

    NO_OBJECTION_FOUND = "no_objection_found"
    CONTESTED = "contested"
    LIKELY_FLAWED = "likely_flawed"
    REFUTED = "refuted"
    NOT_CHECKABLE = "not_checkable"


class DAGEventType(str, Enum):
    JOB_CREATED = "job_created"

    SOURCE_FETCH_STARTED = "source_fetch_started"
    SOURCE_FETCH_COMPLETE = "source_fetch_complete"

    PARSE_STARTED = "parse_started"
    PARSE_COMPLETE = "parse_complete"

    ATOM_EXTRACTION_STARTED = "atom_extraction_started"
    ATOM_EXTRACTION_PROGRESS = "atom_extraction_progress"
    ATOM_CREATED = "atom_created"
    ATOM_EXTRACTION_COMPLETE = "atom_extraction_complete"

    GRAPH_BUILD_STARTED = "graph_build_started"
    EDGE_CREATED = "edge_created"
    GRAPH_BUILD_COMPLETE = "graph_build_complete"

    CHECK_STARTED = "check_started"
    CHECK_COMPLETE = "check_complete"

    CHALLENGE_ISSUED = "challenge_issued"
    REBUTTAL_ISSUED = "rebuttal_issued"

    VERDICT_EMITTED = "verdict_emitted"
    CASCADE_TRIGGERED = "cascade_triggered"

    REPORT_READY = "report_ready"
    JOB_COMPLETE = "job_complete"
    JOB_ERROR = "job_error"


class DAGEvent(BaseModel):
    event_id: str
    job_id: str

    event_type: DAGEventType

    node_id: Optional[str] = None
    atom_id: Optional[str] = None

    payload: dict[str, Any] = Field(default_factory=dict)

    timestamp: datetime
