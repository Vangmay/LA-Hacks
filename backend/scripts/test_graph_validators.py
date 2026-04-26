"""Offline tests for graph edge validators and DAG finalization."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.graph_builder import _finalize_graph  # noqa: E402
from core.graph_validators import validate_and_repair_edges  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraphEdge,
    ResearchGraphEdgeType,
    SourceSpan,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom(atom_id: str, atom_type: ResearchAtomType, text: str) -> ResearchAtom:
    return ResearchAtom(
        atom_id=atom_id,
        paper_id="graph-validator-test",
        atom_type=atom_type,
        text=text,
        section_heading="Main",
        source_span=SourceSpan(
            paper_id="graph-validator-test",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=1.0,
        importance=AtomImportance.HIGH,
    )


def _edge(
    source_id: str,
    target_id: str,
    edge_type: ResearchGraphEdgeType,
    confidence: float = 0.8,
) -> ResearchGraphEdge:
    return ResearchGraphEdge(
        edge_id="edge_tmp",
        source_id=source_id,
        target_id=target_id,
        edge_type=edge_type,
        rationale="test edge",
        confidence=confidence,
    )


def test_invalid_definition_target_dropped() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.TECHNIQUE, "A technique."),
        _atom("atom_002", ResearchAtomType.THEOREM, "A theorem uses the technique."),
    ]
    warnings: list[str] = []
    edges = validate_and_repair_edges(
        [_edge("atom_002", "atom_001", ResearchGraphEdgeType.USES_DEFINITION)],
        atoms,
        warnings,
    )
    _assert(not edges, f"invalid uses_definition edge survived: {edges}")
    _assert(
        any("dropped_invalid_edge_type_target" in warning for warning in warnings),
        f"expected invalid target warning, got {warnings}",
    )


def test_example_direction_repaired() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.TECHNIQUE, "A concept."),
        _atom("atom_002", ResearchAtomType.EXAMPLE, "An example of the concept."),
    ]
    warnings: list[str] = []
    edges = validate_and_repair_edges(
        [_edge("atom_001", "atom_002", ResearchGraphEdgeType.EXAMPLE_FOR)],
        atoms,
        warnings,
    )
    _assert(len(edges) == 1, f"example edge should be repaired: {warnings}")
    _assert(edges[0].source_id == "atom_002" and edges[0].target_id == "atom_001", str(edges[0]))
    _assert(any("repaired_edge_direction" in warning for warning in warnings), str(warnings))


def test_proof_step_constraint() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.THEOREM, "The theorem."),
        _atom("atom_002", ResearchAtomType.PROOF_STEP, "The proof step."),
    ]
    warnings: list[str] = []
    edges = validate_and_repair_edges(
        [_edge("atom_002", "atom_001", ResearchGraphEdgeType.PROOF_STEP_FOR)],
        atoms,
        warnings,
    )
    _assert(len(edges) == 1, f"valid proof edge dropped: {warnings}")


def test_low_confidence_edge_dropped() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.DEFINITION, "A definition."),
        _atom("atom_002", ResearchAtomType.THEOREM, "A theorem."),
    ]
    warnings: list[str] = []
    edges = validate_and_repair_edges(
        [_edge("atom_002", "atom_001", ResearchGraphEdgeType.USES_DEFINITION, confidence=0.2)],
        atoms,
        warnings,
    )
    _assert(not edges, "low-confidence edge should be dropped")
    _assert(any("dropped_low_confidence_edge" in warning for warning in warnings), str(warnings))


def test_duplicate_rationale_dependency_dropped() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.ASSERTION, "The method regularizes the objective."),
        _atom("atom_002", ResearchAtomType.ASSERTION, "The lower bound prevents overfitting."),
    ]
    edge = _edge("atom_002", "atom_001", ResearchGraphEdgeType.DEPENDS_ON)
    edge = edge.model_copy(update={"rationale": "atom 2 is a reiteration and reinforces atom 1"})
    warnings: list[str] = []
    edges = validate_and_repair_edges([edge], atoms, warnings)
    _assert(not edges, "duplicate/restatement rationale should not be a dependency")
    _assert(any("dropped_weak_dependency_rationale" in warning for warning in warnings), str(warnings))


def test_cycle_removal_still_works() -> None:
    warnings: list[str] = []
    graph = _finalize_graph(
        paper_id="graph-validator-test",
        atom_ids=["atom_001", "atom_002", "atom_003"],
        edges=[
            _edge("atom_001", "atom_002", ResearchGraphEdgeType.DEPENDS_ON),
            _edge("atom_002", "atom_003", ResearchGraphEdgeType.DEPENDS_ON),
            _edge("atom_003", "atom_001", ResearchGraphEdgeType.DEPENDS_ON),
        ],
        warnings=warnings,
    )
    _assert(len(graph.edges) == 2, f"cycle edge should be dropped: {graph.edges}")
    _assert(any("dropped_cycle" in warning for warning in warnings), str(warnings))


def main() -> int:
    test_invalid_definition_target_dropped()
    print("  invalid definition target dropped - OK")
    test_example_direction_repaired()
    print("  example direction repaired - OK")
    test_proof_step_constraint()
    print("  proof step constraint - OK")
    test_low_confidence_edge_dropped()
    print("  low-confidence edge dropped - OK")
    test_duplicate_rationale_dependency_dropped()
    print("  duplicate dependency rationale dropped - OK")
    test_cycle_removal_still_works()
    print("  cycle removal still works - OK")
    print("graph validator tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
