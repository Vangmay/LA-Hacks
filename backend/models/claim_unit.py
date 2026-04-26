from pydantic import BaseModel
from typing import List, Optional

class ClaimUnit(BaseModel):
    claim_id: str
    text: str
    claim_type: str = "assertion"
    section: Optional[str] = None
    equations: Optional[list] = None
    citations: Optional[list] = None
    dependencies: Optional[list] = None
