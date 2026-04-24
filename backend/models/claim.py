from pydantic import BaseModel
from typing import List, Literal


class ClaimUnit(BaseModel):
    claim_id: str
    text: str
    claim_type: Literal["theorem", "lemma", "corollary", "proposition", "assertion"]
    section: str
    equations: List[str]
    citations: List[str]
    dependencies: List[str]
