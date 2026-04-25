"""Deterministic cascade propagation.

If atom B is `REFUTED` or `LIKELY_FLAWED`, every atom A that depends on B
(via `DEPENDS_ON` / `USES_*` / `PROOF_STEP_FOR` / `SPECIAL_CASE_OF`) is
flagged. Refuted descendants stay refuted only if independently refuted;
otherwise they become `CONTESTED`.

This is intentionally rule-based — we do not invoke an LLM.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from models import (
    AtomVerdict,
    DEPENDENCY_EDGE_TYPES,
    ResearchGraph,
    VerdictLabel,
    VerdictReasonCode,
)


_FAILING_LABELS = {VerdictLabel.REFUTED, VerdictLabel.LIKELY_FLAWED}


def apply_cascade(
    verdicts: list[AtomVerdict],
    graph: ResearchGraph,
) -> list[AtomVerdict]:
    """Return a new list of verdicts with cascade flags + escalated labels."""
    by_atom: dict[str, AtomVerdict] = {v.atom_id: v for v in verdicts}

    # source_id -> [target_ids it depends on]
    dependents_of: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        if edge.edge_type in DEPENDENCY_EDGE_TYPES:
            dependents_of[edge.target_id].add(edge.source_id)

    failing_seeds = [v.atom_id for v in verdicts if v.label in _FAILING_LABELS]

    affected_by_seed: dict[str, set[str]] = {}
    for seed in failing_seeds:
        affected_by_seed[seed] = _walk_dependents(seed, dependents_of)

    seed_for_atom: dict[str, str] = {}
    for seed, descendants in affected_by_seed.items():
        for desc in descendants:
            if desc in by_atom and desc not in seed_for_atom:
                seed_for_atom[desc] = seed

    updated: list[AtomVerdict] = []
    for verdict in verdicts:
        seed = seed_for_atom.get(verdict.atom_id)
        if seed is None or verdict.atom_id == seed:
            updated.append(verdict)
            continue

        # Already independently refuted → leave label, just record cascade.
        if verdict.label == VerdictLabel.REFUTED:
            cascaded = verdict.model_copy(
                update={
                    "is_cascaded": True,
                    "cascade_source_atom_id": seed,
                }
            )
            updated.append(cascaded)
            continue

        new_label = (
            VerdictLabel.CONTESTED
            if verdict.label
            in (
                VerdictLabel.NO_OBJECTION_FOUND,
                VerdictLabel.NOT_CHECKABLE,
                VerdictLabel.CONTESTED,
            )
            else verdict.label
        )
        new_reasons = list(verdict.reason_codes)
        if VerdictReasonCode.CASCADED_FROM_DEPENDENCY not in new_reasons:
            new_reasons.append(VerdictReasonCode.CASCADED_FROM_DEPENDENCY)

        cascaded = verdict.model_copy(
            update={
                "label": new_label,
                "is_cascaded": True,
                "cascade_source_atom_id": seed,
                "reason_codes": new_reasons,
                "rationale": (
                    verdict.rationale
                    + f" Cascaded from dependency {seed}."
                ),
            }
        )
        updated.append(cascaded)
    return updated


def _walk_dependents(
    seed: str,
    dependents_of: dict[str, set[str]],
) -> set[str]:
    seen: set[str] = set()
    stack: list[str] = [seed]
    while stack:
        node = stack.pop()
        for dependent in dependents_of.get(node, ()):
            if dependent not in seen:
                seen.add(dependent)
                stack.append(dependent)
    return seen
