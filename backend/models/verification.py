from pydantic import BaseModel
from typing import Literal


class VerificationResult(BaseModel):
    tier: Literal["symbolic", "numeric", "semantic"]
    status: Literal["passed", "failed", "inconclusive"]
    evidence: str
    confidence: float
