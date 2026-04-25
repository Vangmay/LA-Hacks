"""Typed check results.

Replaces the old `VerificationResult`. A check is a deterministic-ish probe
(SymPy algebra, SciPy numeric search, citation context). Status enum is
honest: passed/failed/inconclusive plus the asymmetric counterexample
labels. Confidence is bounded.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .evidence import Evidence


class CheckKind(str, Enum):
    ALGEBRAIC_SANITY = "algebraic_sanity"
    NUMERIC_COUNTEREXAMPLE_PROBE = "numeric_counterexample_probe"
    CITATION_CONTEXT = "citation_context"
    PRIOR_ART_CONTRADICTION = "prior_art_contradiction"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    INCONCLUSIVE = "inconclusive"
    NO_COUNTEREXAMPLE_FOUND = "no_counterexample_found"
    COUNTEREXAMPLE_FOUND = "counterexample_found"


class CheckResult(BaseModel):
    check_id: str
    atom_id: str

    kind: CheckKind
    status: CheckStatus

    summary: str
    evidence: list[Evidence] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)

    raw_details: dict[str, Any] = Field(default_factory=dict)

    error: Optional[str] = None
