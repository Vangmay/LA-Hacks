"""Typed adversarial models.

`Challenge` carries a type, severity, evidence list, and a falsifiable test.
`Rebuttal` carries a typed response (resolves / concedes / clarifies) so
the verdict aggregator can decide deterministically whether a challenge is
resolved.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .evidence import Evidence


class ChallengeType(str, Enum):
    COUNTEREXAMPLE = "counterexample"
    MISSING_ASSUMPTION = "missing_assumption"
    PROOF_GAP = "proof_gap"
    CITATION_GAP = "citation_gap"
    NOTATION_AMBIGUITY = "notation_ambiguity"
    SCOPE_OVERCLAIM = "scope_overclaim"
    CONTRADICTS_PRIOR_WORK = "contradicts_prior_work"
    ALGEBRAIC_ERROR = "algebraic_error"
    NUMERIC_FAILURE = "numeric_failure"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FATAL = "fatal"


class Challenge(BaseModel):
    challenge_id: str
    atom_id: str

    attacker_agent: str

    challenge_type: ChallengeType
    severity: Severity

    challenge_text: str

    evidence: list[Evidence] = Field(default_factory=list)
    falsifiable_test: Optional[str] = None

    confidence: float = Field(ge=0.0, le=1.0)


class RebuttalType(str, Enum):
    RESOLVES = "resolves"
    PARTIALLY_RESOLVES = "partially_resolves"
    CONCEDES = "concedes"
    CLARIFIES_SCOPE = "clarifies_scope"
    DISPUTES = "disputes"
    UNSUPPORTED_DEFENSE = "unsupported_defense"


class Rebuttal(BaseModel):
    rebuttal_id: str
    challenge_id: str
    atom_id: str

    defender_agent: str

    response_type: RebuttalType
    rebuttal_text: str

    evidence: list[Evidence] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)
