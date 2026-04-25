"""Review job snapshot — what `job_store` holds for one run."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .atoms import ResearchAtom
from .graph import ResearchGraph
from .report import ReviewReport
from .source import ParsedPaper, PaperSource
from .verdict import AtomVerdict


class JobMode(str, Enum):
    REVIEW = "review"
    READER = "reader"
    NOVEL = "novel"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class ReviewJob(BaseModel):
    job_id: str
    mode: JobMode
    status: JobStatus

    created_at: datetime
    updated_at: datetime

    source: Optional[PaperSource] = None
    parsed_paper: Optional[ParsedPaper] = None

    atoms: list[ResearchAtom] = Field(default_factory=list)
    graph: Optional[ResearchGraph] = None
    verdicts: list[AtomVerdict] = Field(default_factory=list)

    report: Optional[ReviewReport] = None

    total_atoms: int = 0
    completed_atoms: int = 0

    error: Optional[str] = None

    metadata: dict[str, Any] = Field(default_factory=dict)
