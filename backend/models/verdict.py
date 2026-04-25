"""Atom verdict — replaces `ClaimVerdict`.

Labels are deliberately humble. `NO_OBJECTION_FOUND` instead of `SUPPORTED`
because the system cannot prove arbitrary theoretical claims; it can only
report that no concrete objection was raised.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .adversarial import Challenge, Rebuttal
from .checks import CheckResult
from .evidence import Evidence


class VerdictLabel(str, Enum):
    NO_OBJECTION_FOUND = "NO_OBJECTION_FOUND"
    CONTESTED = "CONTESTED"
    LIKELY_FLAWED = "LIKELY_FLAWED"
    REFUTED = "REFUTED"
    NOT_CHECKABLE = "NOT_CHECKABLE"


class VerdictReasonCode(str, Enum):
    EXPLICIT_COUNTEREXAMPLE = "explicit_counterexample"
    ALGEBRAIC_FAILURE = "algebraic_failure"
    UNRESOLVED_FATAL_CHALLENGE = "unresolved_fatal_challenge"
    UNRESOLVED_HIGH_CHALLENGE = "unresolved_high_challenge"
    CHECKS_INCONCLUSIVE = "checks_inconclusive"
    NO_SERIOUS_CHALLENGES = "no_serious_challenges"
    CASCADED_FROM_DEPENDENCY = "cascaded_from_dependency"
    NOT_REVIEWED = "not_reviewed"


class AtomVerdict(BaseModel):
    verdict_id: str
    atom_id: str

    label: VerdictLabel
    confidence: float = Field(ge=0.0, le=1.0)

    reason_codes: list[VerdictReasonCode] = Field(default_factory=list)
    rationale: str

    checks: list[CheckResult] = Field(default_factory=list)
    challenges: list[Challenge] = Field(default_factory=list)
    rebuttals: list[Rebuttal] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    is_cascaded: bool = False
    cascade_source_atom_id: Optional[str] = None
