from pydantic import BaseModel
from typing import List


class Challenge(BaseModel):
    challenge_id: str
    claim_id: str
    attacker_agent: str
    challenge_text: str
    supporting_evidence: List[str]


class Rebuttal(BaseModel):
    challenge_id: str
    rebuttal_text: str
    supporting_evidence: List[str]
