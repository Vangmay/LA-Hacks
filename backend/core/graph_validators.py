"""Validation and conservative repair for research graph edges."""
from __future__ import annotations

from models import (
    DEPENDENCY_EDGE_TYPES,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraphEdge,
    ResearchGraphEdgeType,
)


MIN_EDGE_CONFIDENCE = 0.45

_THEOREM_LIKE = {
    ResearchAtomType.THEOREM,
    ResearchAtomType.LEMMA,
    ResearchAtomType.PROPOSITION,
    ResearchAtomType.COROLLARY,
}


def validate_and_repair_edges(
    edges: list[ResearchGraphEdge],
    atoms: list[ResearchAtom],
    warnings: list[str],
    *,
    min_confidence: float = MIN_EDGE_CONFIDENCE,
) -> list[ResearchGraphEdge]:
    atom_by_id = {atom.atom_id: atom for atom in atoms}
    validated: list[ResearchGraphEdge] = []
    seen: set[tuple[str, str, ResearchGraphEdgeType]] = set()

    for edge in edges:
        source = atom_by_id.get(edge.source_id)
        target = atom_by_id.get(edge.target_id)
        if source is None or target is None:
            warnings.append(
                f"dropped_unknown_atom: {edge.source_id!r} -> {edge.target_id!r}"
            )
            continue

        if edge.confidence < min_confidence:
            warnings.append(
                f"dropped_low_confidence_edge: {edge.source_id} -> {edge.target_id} "
                f"{edge.edge_type.value} confidence={edge.confidence:.2f}"
            )
            continue
        if _rationale_is_not_dependency(edge):
            warnings.append(
                f"dropped_weak_dependency_rationale: {edge.source_id} -> "
                f"{edge.target_id} {edge.edge_type.value}"
            )
            continue

        repaired = _repair_direction(edge, source, target, atom_by_id, warnings)
        if repaired is None:
            continue

        source = atom_by_id[repaired.source_id]
        target = atom_by_id[repaired.target_id]
        if not _valid_edge_type(repaired.edge_type, source, target):
            warnings.append(
                f"dropped_invalid_edge_type_target: {repaired.source_id} -> "
                f"{repaired.target_id} {repaired.edge_type.value} "
                f"source={source.atom_type.value} target={target.atom_type.value}"
            )
            continue

        key = (repaired.source_id, repaired.target_id, repaired.edge_type)
        if key in seen:
            continue
        seen.add(key)
        validated.append(repaired)

    return _renumber_edges(validated)


def _repair_direction(
    edge: ResearchGraphEdge,
    source: ResearchAtom,
    target: ResearchAtom,
    atom_by_id: dict[str, ResearchAtom],
    warnings: list[str],
) -> ResearchGraphEdge | None:
    if edge.edge_type == ResearchGraphEdgeType.EXAMPLE_FOR:
        if source.atom_type == ResearchAtomType.EXAMPLE:
            return edge
        if target.atom_type == ResearchAtomType.EXAMPLE and source.atom_type != ResearchAtomType.EXAMPLE:
            warnings.append(
                f"repaired_edge_direction: {edge.source_id} -> {edge.target_id} example_for"
            )
            return edge.model_copy(
                update={
                    "source_id": edge.target_id,
                    "target_id": edge.source_id,
                    "rationale": edge.rationale or "example edge direction repaired",
                }
            )
        warnings.append(
            f"dropped_invalid_direction: {edge.source_id} -> {edge.target_id} example_for"
        )
        return None

    if edge.edge_type == ResearchGraphEdgeType.COUNTEREXAMPLE_TO:
        if source.atom_type == ResearchAtomType.COUNTEREXAMPLE:
            return edge
        if (
            target.atom_type == ResearchAtomType.COUNTEREXAMPLE
            and source.atom_type != ResearchAtomType.COUNTEREXAMPLE
        ):
            warnings.append(
                f"repaired_edge_direction: {edge.source_id} -> {edge.target_id} counterexample_to"
            )
            return edge.model_copy(
                update={
                    "source_id": edge.target_id,
                    "target_id": edge.source_id,
                    "rationale": edge.rationale or "counterexample edge direction repaired",
                }
            )
        warnings.append(
            f"dropped_invalid_direction: {edge.source_id} -> {edge.target_id} counterexample_to"
        )
        return None

    if edge.edge_type == ResearchGraphEdgeType.PROOF_STEP_FOR:
        if source.atom_type == ResearchAtomType.PROOF_STEP:
            return edge
        warnings.append(
            f"dropped_invalid_direction: {edge.source_id} -> {edge.target_id} proof_step_for"
        )
        return None

    return edge


def _valid_edge_type(
    edge_type: ResearchGraphEdgeType,
    source: ResearchAtom,
    target: ResearchAtom,
) -> bool:
    if edge_type == ResearchGraphEdgeType.USES_DEFINITION:
        return target.atom_type == ResearchAtomType.DEFINITION
    if edge_type == ResearchGraphEdgeType.USES_ASSUMPTION:
        return target.atom_type == ResearchAtomType.ASSUMPTION
    if edge_type == ResearchGraphEdgeType.USES_LEMMA:
        return target.atom_type in _THEOREM_LIKE
    if edge_type == ResearchGraphEdgeType.PROOF_STEP_FOR:
        return source.atom_type == ResearchAtomType.PROOF_STEP and target.atom_type in _THEOREM_LIKE
    if edge_type == ResearchGraphEdgeType.EXAMPLE_FOR:
        return source.atom_type == ResearchAtomType.EXAMPLE
    if edge_type == ResearchGraphEdgeType.COUNTEREXAMPLE_TO:
        return source.atom_type == ResearchAtomType.COUNTEREXAMPLE
    return True


def _rationale_is_not_dependency(edge: ResearchGraphEdge) -> bool:
    if edge.edge_type not in DEPENDENCY_EDGE_TYPES:
        return False
    rationale = (edge.rationale or "").lower()
    weak_markers = {
        "duplicate",
        "duplicates",
        "restate",
        "restates",
        "restatement",
        "reiteration",
        "reiterates",
        "reinforce",
        "reinforces",
        "support",
        "supports",
        "supported",
        "similar",
        "topical",
        "related",
        "same claim",
    }
    return any(marker in rationale for marker in weak_markers)


def _renumber_edges(edges: list[ResearchGraphEdge]) -> list[ResearchGraphEdge]:
    return [
        edge.model_copy(update={"edge_id": f"edge_{idx:03d}"})
        for idx, edge in enumerate(edges, start=1)
    ]
