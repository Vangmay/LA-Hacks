"""Final review report bundle."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .atoms import ResearchAtom
from .graph import ResearchGraph
from .verdict import AtomVerdict


class ReviewSummary(BaseModel):
    total_atoms: int
    total_reviewed_atoms: int

    no_objection_found: int = 0
    contested: int = 0
    likely_flawed: int = 0
    refuted: int = 0
    not_checkable: int = 0

    high_risk_atom_ids: list[str] = Field(default_factory=list)
    cascaded_atom_ids: list[str] = Field(default_factory=list)


class ReviewReport(BaseModel):
    report_id: str
    job_id: str
    paper_id: str

    paper_title: str
    arxiv_id: Optional[str] = None
    paper_hash: str

    reviewed_at: datetime

    summary: ReviewSummary

    atoms: list[ResearchAtom]
    graph: ResearchGraph
    verdicts: list[AtomVerdict]

    markdown_report: str

    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
