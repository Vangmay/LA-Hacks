from pydantic import BaseModel
from typing import List, Literal, Optional

from .adversarial import Challenge, Rebuttal
from .verification import VerificationResult


class ClaimVerdict(BaseModel):
    claim_id: str
    verdict: Literal["SUPPORTED", "CONTESTED", "REFUTED"]
    confidence: float
    is_cascaded: bool
    cascade_source: Optional[str]
    challenges: List[Challenge]
    rebuttals: List[Rebuttal]
    verification_results: List[VerificationResult]
