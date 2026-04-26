"""Offline tests for deterministic graph edge candidate generation."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from core.edge_candidates import build_edge_candidates  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraphEdgeType,
    SourceSpan,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom(
    atom_id: str,
    atom_type: ResearchAtomType,
    text: str,
    *,
    section_id: str = "sec_001",
    key_terms: list[str] | None = None,
) -> ResearchAtom:
    return ResearchAtom(
        atom_id=atom_id,
        paper_id="edge-candidate-test",
        atom_type=atom_type,
        text=text,
        section_id=section_id,
        section_heading="Main",
        source_span=SourceSpan(
            paper_id="edge-candidate-test",
            section_id=section_id,
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=1.0,
        importance=AtomImportance.HIGH,
        key_terms=key_terms or [],
    )


def test_definition_candidate() -> None:
    atoms = [
        _atom(
            "atom_001",
            ResearchAtomType.DEFINITION,
            "The variational lower bound is the objective optimized by the model.",
            key_terms=["variational lower bound"],
        ),
        _atom(
            "atom_002",
            ResearchAtomType.THEOREM,
            "The variational lower bound can be optimized using stochastic gradients.",
            section_id="sec_002",
        ),
    ]
    candidates = build_edge_candidates(atoms)
    _assert(
        any(
            candidate.source_id == "atom_002"
            and candidate.target_id == "atom_001"
            and candidate.proposed_type == ResearchGraphEdgeType.USES_DEFINITION
            for candidate in candidates
        ),
        f"expected uses_definition candidate, got {candidates}",
    )


def test_proof_step_candidate() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.THEOREM, "For every real x, x^2 >= 0."),
        _atom(
            "atom_002",
            ResearchAtomType.PROOF_STEP,
            "Proof. The claim follows because x times x is nonnegative.",
        ),
    ]
    candidates = build_edge_candidates(atoms)
    _assert(
        any(
            candidate.source_id == "atom_002"
            and candidate.target_id == "atom_001"
            and candidate.proposed_type == ResearchGraphEdgeType.PROOF_STEP_FOR
            and candidate.deterministic
            for candidate in candidates
        ),
        f"expected deterministic proof_step_for candidate, got {candidates}",
    )


def main() -> int:
    test_definition_candidate()
    print("  definition overlap candidate - OK")
    test_proof_step_candidate()
    print("  proof step candidate - OK")
    print("edge candidate tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
