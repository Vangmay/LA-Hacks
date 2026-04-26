"""Messy, repairable atom candidates used before final `ResearchAtom`s."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .atoms import (
    AtomCheckability,
    AtomImportance,
    AtomReviewability,
    ResearchAtomType,
)
from .source import SourceSpan


class AtomCandidate(BaseModel):
    candidate_id: str
    paper_id: str

    atom_type: ResearchAtomType
    source_quote: str
    text: str
    normalized_text: Optional[str] = None

    section_heading: Optional[str] = None
    importance: AtomImportance = AtomImportance.MEDIUM

    reviewability: AtomReviewability = AtomReviewability.REVIEWABLE
    checkability: AtomCheckability = AtomCheckability.CONCEPTUAL

    claim_scope: Optional[str] = None
    why_this_is_an_atom: Optional[str] = None
    role_in_paper: Optional[str] = None

    assumptions: list[str] = Field(default_factory=list)
    conclusions: list[str] = Field(default_factory=list)
    key_terms: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)

    dependency_hints: list[str] = Field(default_factory=list)
    equation_refs: list[str] = Field(default_factory=list)
    citation_refs: list[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)
    source_span: Optional[SourceSpan] = None
