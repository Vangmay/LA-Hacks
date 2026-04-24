from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class DAGEventType(str, Enum):
    NODE_CREATED       = "node_created"
    TIER_COMPLETE      = "tier_complete"
    CHALLENGE_ISSUED   = "challenge_issued"
    REBUTTAL_ISSUED    = "rebuttal_issued"
    VERDICT_EMITTED    = "verdict_emitted"
    CASCADE_TRIGGERED  = "cascade_triggered"
    REVIEW_COMPLETE    = "review_complete"
    NODE_CLASSIFIED    = "node_classified"
    SCAFFOLD_GENERATED = "scaffold_generated"
    POC_READY          = "poc_ready"


class DAGEvent(BaseModel):
    event_id: str
    job_id: str
    event_type: DAGEventType
    claim_id: Optional[str] = None
    payload: dict
    timestamp: datetime
