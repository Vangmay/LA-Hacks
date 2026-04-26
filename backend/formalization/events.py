from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class FormalizationEventType(str, Enum):
    RUN_STARTED = "run_started"
    ATOM_QUEUED = "atom_queued"
    ATOM_CONTEXT_BUILT = "atom_context_built"
    LLM_THOUGHT = "llm_thought"
    TOOL_CALL_STARTED = "tool_call_started"
    TOOL_CALL_COMPLETE = "tool_call_complete"
    AXLE_CHECK_RESULT = "axle_check_result"
    AXLE_VERIFY_RESULT = "axle_verify_result"
    ARTIFACT_RECORDED = "artifact_recorded"
    ATOM_VERDICT = "atom_verdict"
    ATOM_ERROR = "atom_error"
    RUN_COMPLETE = "run_complete"
    RUN_ERROR = "run_error"


class FormalizationEvent(BaseModel):
    event_id: str
    run_id: str
    event_type: FormalizationEventType
    atom_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
