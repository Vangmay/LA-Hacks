from pydantic import BaseModel
from typing import List
from datetime import datetime

from .verdict import ClaimVerdict


class ReviewReport(BaseModel):
    paper_title: str
    paper_hash: str
    reviewed_at: datetime
    total_claims: int
    supported: int
    contested: int
    refuted: int
    cascaded_failures: int
    verdicts: List[ClaimVerdict]
    dag_summary: dict
    markdown_report: str
