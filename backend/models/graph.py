"""Typed research graph.

`source_id --edge_type--> target_id`. For `DEPENDS_ON`, source requires
target — target must be established/checked before source. This matches the
internal `core/dag.py` convention used for cycle detection.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ResearchGraphEdgeType(str, Enum):
    DEPENDS_ON = "depends_on"
    USES_DEFINITION = "uses_definition"
    USES_LEMMA = "uses_lemma"
    USES_ASSUMPTION = "uses_assumption"

    GENERALIZES = "generalizes"
    SPECIAL_CASE_OF = "special_case_of"

    MOTIVATES = "motivates"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"

    PROOF_STEP_FOR = "proof_step_for"
    EXAMPLE_FOR = "example_for"
    COUNTEREXAMPLE_TO = "counterexample_to"

    RELATED_TO = "related_to"


DEPENDENCY_EDGE_TYPES: frozenset[ResearchGraphEdgeType] = frozenset(
    {
        ResearchGraphEdgeType.DEPENDS_ON,
        ResearchGraphEdgeType.USES_DEFINITION,
        ResearchGraphEdgeType.USES_LEMMA,
        ResearchGraphEdgeType.USES_ASSUMPTION,
        ResearchGraphEdgeType.PROOF_STEP_FOR,
        ResearchGraphEdgeType.SPECIAL_CASE_OF,
    }
)


class ResearchGraphEdge(BaseModel):
    edge_id: str

    source_id: str
    target_id: str

    edge_type: ResearchGraphEdgeType

    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)

    evidence_atom_ids: list[str] = Field(default_factory=list)
    source_quote: Optional[str] = None


class ResearchGraph(BaseModel):
    paper_id: str
    atom_ids: list[str]
    edges: list[ResearchGraphEdge]

    roots: list[str] = Field(default_factory=list)
    topological_order: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
