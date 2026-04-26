"""Event contracts for live research deep-dive runs."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DeepDiveEventType(str, Enum):
    RUN_STARTED = "run.started"
    RUN_SNAPSHOT = "run.snapshot"
    RUN_FINALIZED = "run.finalized"
    RUN_ERROR = "run.error"

    STAGE_ENTERED = "stage.entered"
    STAGE_COMPLETED = "stage.completed"

    INVESTIGATOR_PLANNED = "investigator.planned"
    INVESTIGATOR_SYNTHESIZED = "investigator.synthesized"

    SUBAGENT_PLANNED = "subagent.planned"
    SUBAGENT_STARTED = "subagent.started"
    SUBAGENT_TOOL_REQUESTED = "subagent.tool.requested"
    SUBAGENT_TOOL_RESULT = "subagent.tool.result"
    SUBAGENT_TOOL_REJECTED = "subagent.tool.rejected"
    SUBAGENT_TOOL_ERROR = "subagent.tool.error"
    SUBAGENT_ARTIFACT_UPDATED = "subagent.artifact.updated"
    SUBAGENT_BUDGET = "subagent.budget"
    SUBAGENT_COMPLETED = "subagent.completed"

    CROSS_INVESTIGATOR_COMPLETED = "cross_investigator.completed"
    CRITIQUE_COMPLETED = "critique.completed"


class DeepDiveEvent(BaseModel):
    """A replayable event emitted by the research deep-dive control plane."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    type: DeepDiveEventType
    run_id: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)
