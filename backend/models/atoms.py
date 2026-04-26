"""Research atoms — the central abstraction.

A `ResearchAtom` is any discrete unit of a paper: a definition, assumption,
theorem, lemma, construction, algorithm, limitation, technique, etc. Atoms
replace the old `ClaimUnit`. They carry full source grounding so downstream
checks and the frontend can show where each one came from.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .source import CitationEntry, EquationBlock, SourceSpan


class ResearchAtomType(str, Enum):
    DEFINITION = "definition"
    ASSUMPTION = "assumption"
    THEOREM = "theorem"
    LEMMA = "lemma"
    COROLLARY = "corollary"
    PROPOSITION = "proposition"
    CONJECTURE = "conjecture"

    PROOF_STEP = "proof_step"
    CONSTRUCTION = "construction"
    ALGORITHM = "algorithm"
    BOUND = "bound"

    EXAMPLE = "example"
    COUNTEREXAMPLE = "counterexample"

    LIMITATION = "limitation"
    OPEN_PROBLEM = "open_problem"
    RELATED_WORK_CLAIM = "related_work_claim"

    TECHNIQUE = "technique"
    ASSERTION = "assertion"


class AtomImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CORE = "core"


class AtomReviewability(str, Enum):
    REVIEWABLE = "reviewable"
    LEARNING_ONLY = "learning_only"
    BACKGROUND = "background"
    DROP = "drop"


class AtomCheckability(str, Enum):
    SYMBOLIC = "symbolic"
    NUMERIC = "numeric"
    CITATION = "citation"
    PROOF_ONLY = "proof_only"
    CONCEPTUAL = "conceptual"
    NOT_CHECKABLE = "not_checkable"


class ResearchAtom(BaseModel):
    atom_id: str
    paper_id: str

    atom_type: ResearchAtomType
    text: str

    normalized_text: Optional[str] = None

    section_id: Optional[str] = None
    section_heading: Optional[str] = None

    source_span: SourceSpan

    equations: list[EquationBlock] = Field(default_factory=list)
    citations: list[CitationEntry] = Field(default_factory=list)

    extraction_confidence: float = Field(ge=0.0, le=1.0)
    importance: AtomImportance = AtomImportance.MEDIUM
    reviewability: AtomReviewability = AtomReviewability.REVIEWABLE
    checkability: AtomCheckability = AtomCheckability.CONCEPTUAL
    claim_scope: Optional[str] = None
    why_this_is_an_atom: Optional[str] = None
    role_in_paper: Optional[str] = None

    assumptions: list[str] = Field(default_factory=list)
    conclusions: list[str] = Field(default_factory=list)
    proof_sketch: Optional[str] = None

    key_terms: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    dependency_hints: list[str] = Field(default_factory=list)
    equation_refs: list[str] = Field(default_factory=list)
    citation_refs: list[str] = Field(default_factory=list)


class AtomExtractionResult(BaseModel):
    paper_id: str
    atoms: list[ResearchAtom]
    warnings: list[str] = Field(default_factory=list)


REVIEWABLE_ATOM_TYPES: frozenset[ResearchAtomType] = frozenset(
    {
        ResearchAtomType.THEOREM,
        ResearchAtomType.LEMMA,
        ResearchAtomType.COROLLARY,
        ResearchAtomType.PROPOSITION,
        ResearchAtomType.CONJECTURE,
        ResearchAtomType.ASSUMPTION,
        ResearchAtomType.BOUND,
        ResearchAtomType.CONSTRUCTION,
        ResearchAtomType.ALGORITHM,
        ResearchAtomType.LIMITATION,
        ResearchAtomType.ASSERTION,
    }
)


def is_reviewable(atom: "ResearchAtom") -> bool:
    """Atoms that should run through checks + adversarial loop."""
    return (
        atom.reviewability == AtomReviewability.REVIEWABLE
        and atom.atom_type in REVIEWABLE_ATOM_TYPES
        and atom.importance
        in {
            AtomImportance.MEDIUM,
            AtomImportance.HIGH,
            AtomImportance.CORE,
        }
    )
