"""Deterministic candidate edges for the research atom graph.

These candidates are intentionally conservative. They give the graph LLM a
bounded classification problem instead of asking it to invent edges from every
atom pair.
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field

from models import ResearchAtom, ResearchAtomType, ResearchGraphEdgeType


class EdgeCandidate(BaseModel):
    candidate_id: str
    source_id: str
    target_id: str
    proposed_type: Optional[ResearchGraphEdgeType] = None
    evidence: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    deterministic: bool = False


_DEPENDENT_TYPES = {
    ResearchAtomType.THEOREM,
    ResearchAtomType.LEMMA,
    ResearchAtomType.COROLLARY,
    ResearchAtomType.PROPOSITION,
    ResearchAtomType.CONJECTURE,
    ResearchAtomType.ASSERTION,
    ResearchAtomType.BOUND,
    ResearchAtomType.CONSTRUCTION,
    ResearchAtomType.ALGORITHM,
    ResearchAtomType.TECHNIQUE,
}
_THEOREM_LIKE = {
    ResearchAtomType.THEOREM,
    ResearchAtomType.LEMMA,
    ResearchAtomType.COROLLARY,
    ResearchAtomType.PROPOSITION,
}
_STOPWORDS = {
    "about",
    "above",
    "after",
    "again",
    "algorithm",
    "also",
    "among",
    "because",
    "before",
    "being",
    "between",
    "claim",
    "could",
    "defined",
    "definition",
    "does",
    "during",
    "each",
    "equation",
    "every",
    "from",
    "given",
    "have",
    "into",
    "lemma",
    "method",
    "model",
    "only",
    "other",
    "paper",
    "proof",
    "result",
    "same",
    "section",
    "shows",
    "such",
    "than",
    "that",
    "their",
    "theorem",
    "there",
    "these",
    "this",
    "through",
    "under",
    "using",
    "where",
    "which",
    "while",
    "with",
    "within",
    "would",
}


def build_edge_candidates(atoms: list[ResearchAtom]) -> list[EdgeCandidate]:
    candidates: list[EdgeCandidate] = []
    seen: set[tuple[str, str, ResearchGraphEdgeType, str]] = set()

    def add(
        source: ResearchAtom,
        target: ResearchAtom,
        edge_type: ResearchGraphEdgeType,
        evidence: str,
        reason: str,
        confidence: float,
        *,
        deterministic: bool = False,
    ) -> None:
        if source.atom_id == target.atom_id:
            return
        key = (source.atom_id, target.atom_id, edge_type, reason)
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            EdgeCandidate(
                candidate_id=f"edge_cand_{len(candidates) + 1:03d}",
                source_id=source.atom_id,
                target_id=target.atom_id,
                proposed_type=edge_type,
                evidence=evidence[:500],
                reason=reason,
                confidence=confidence,
                deterministic=deterministic,
            )
        )

    label_by_atom = _labels_by_atom(atoms)
    for source_idx, source in enumerate(atoms):
        source_terms = _atom_terms(source)
        source_text = _search_text(source)

        # Proof environments normally refer to the immediately preceding
        # theorem-like statement in the same section.
        if source.atom_type == ResearchAtomType.PROOF_STEP:
            target = _nearest_prior_theorem_like(source_idx, source, atoms)
            if target is not None:
                add(
                    source,
                    target,
                    ResearchGraphEdgeType.PROOF_STEP_FOR,
                    "Proof environment follows a theorem-like statement",
                    "proof containment",
                    0.9,
                    deterministic=True,
                )

        for target_idx, target in enumerate(atoms[:source_idx]):
            if not _within_section_window(source, target, max_distance=8):
                continue

            target_terms = _atom_terms(target)
            overlap = sorted(source_terms & target_terms)
            overlap_count = len(overlap)
            overlap_evidence = (
                f"shared terms: {', '.join(overlap[:8])}"
                if overlap
                else "section-order prior"
            )

            if target.atom_type == ResearchAtomType.DEFINITION and source.atom_type in _DEPENDENT_TYPES:
                phrase_hit = _definition_phrase_hit(target, source_text)
                if phrase_hit or overlap_count >= 2:
                    add(
                        source,
                        target,
                        ResearchGraphEdgeType.USES_DEFINITION,
                        phrase_hit or overlap_evidence,
                        "later atom uses an earlier defined concept",
                        0.68 if phrase_hit else 0.58,
                    )
                elif _within_section_window(source, target, max_distance=3):
                    add(
                        source,
                        target,
                        ResearchGraphEdgeType.USES_DEFINITION,
                        overlap_evidence,
                        "nearby earlier definition may be required",
                        0.35,
                    )

            if target.atom_type == ResearchAtomType.ASSUMPTION and source.atom_type in _DEPENDENT_TYPES:
                if overlap_count >= 1 or _mentions_any(source_text, {"assume", "assumption", "under"}):
                    add(
                        source,
                        target,
                        ResearchGraphEdgeType.USES_ASSUMPTION,
                        overlap_evidence,
                        "later atom may rely on an earlier explicit assumption",
                        0.58,
                    )

            if target.atom_type in _THEOREM_LIKE and source.atom_type in _THEOREM_LIKE:
                if _mentions_prior_result(source_text) or overlap_count >= 2:
                    add(
                        source,
                        target,
                        ResearchGraphEdgeType.USES_LEMMA,
                        overlap_evidence,
                        "later theorem-like atom may rely on earlier result",
                        0.52,
                    )

            if source.atom_type == ResearchAtomType.EXAMPLE and overlap_count >= 1:
                add(
                    source,
                    target,
                    ResearchGraphEdgeType.EXAMPLE_FOR,
                    overlap_evidence,
                    "example illustrates an earlier atom",
                    0.62,
                )

            if source.atom_type == ResearchAtomType.COUNTEREXAMPLE and overlap_count >= 1:
                add(
                    source,
                    target,
                    ResearchGraphEdgeType.COUNTEREXAMPLE_TO,
                    overlap_evidence,
                    "counterexample targets an earlier atom",
                    0.62,
                )

            hint = _matching_dependency_hint(source, target_terms)
            if hint:
                proposed = _hint_edge_type(target)
                add(
                    source,
                    target,
                    proposed,
                    hint,
                    "LLM extraction dependency hint matched target atom",
                    0.7,
                )

            label = label_by_atom.get(target.atom_id)
            if label and label in source_text:
                add(
                    source,
                    target,
                    _hint_edge_type(target),
                    f"source mentions target label {label}",
                    "explicit label reference",
                    0.82,
                    deterministic=True,
                )

    return candidates


def _nearest_prior_theorem_like(
    source_idx: int,
    source: ResearchAtom,
    atoms: list[ResearchAtom],
) -> Optional[ResearchAtom]:
    for target in reversed(atoms[:source_idx]):
        if source.section_id and target.section_id and source.section_id != target.section_id:
            continue
        if target.atom_type in _THEOREM_LIKE:
            return target
    return None


def _within_section_window(
    source: ResearchAtom,
    target: ResearchAtom,
    *,
    max_distance: int,
) -> bool:
    source_idx = _section_index(source.section_id)
    target_idx = _section_index(target.section_id)
    if source_idx is None or target_idx is None:
        return True
    return 0 <= source_idx - target_idx <= max_distance


def _section_index(section_id: Optional[str]) -> Optional[int]:
    if not section_id:
        return None
    match = re.search(r"(\d+)$", section_id)
    return int(match.group(1)) if match else None


def _atom_terms(atom: ResearchAtom) -> set[str]:
    terms = {term.lower().strip() for term in atom.key_terms if term.strip()}
    text = " ".join([atom.text, atom.normalized_text or "", atom.source_span.raw_excerpt or ""])
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", text.lower()):
        if token not in _STOPWORDS:
            terms.add(token)
    return terms


def _search_text(atom: ResearchAtom) -> str:
    return " ".join(
        [
            atom.text or "",
            atom.normalized_text or "",
            atom.source_span.raw_excerpt or "",
            " ".join(atom.dependency_hints),
            " ".join(atom.equation_refs),
        ]
    ).lower()


def _definition_phrase_hit(definition: ResearchAtom, source_text: str) -> str:
    for term in definition.key_terms:
        clean = term.strip().lower()
        if len(clean) >= 5 and clean in source_text:
            return f"source mentions defined key term: {term}"
    words = [
        word
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", definition.text.lower())
        if word not in _STOPWORDS
    ]
    for n in (4, 3, 2):
        for idx in range(0, max(0, len(words) - n + 1)):
            phrase = " ".join(words[idx : idx + n])
            if len(phrase) >= 10 and phrase in source_text:
                return f"source mentions defined phrase: {phrase}"
    return ""


def _mentions_any(text: str, needles: set[str]) -> bool:
    return any(re.search(rf"\b{re.escape(needle)}\b", text) for needle in needles)


def _mentions_prior_result(text: str) -> bool:
    return _mentions_any(
        text,
        {"lemma", "theorem", "proposition", "corollary", "follows", "implies", "using"},
    )


def _matching_dependency_hint(source: ResearchAtom, target_terms: set[str]) -> str:
    for hint in source.dependency_hints:
        hint_terms = {
            token
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", hint.lower())
            if token not in _STOPWORDS
        }
        if hint_terms & target_terms:
            return hint
    return ""


def _hint_edge_type(target: ResearchAtom) -> ResearchGraphEdgeType:
    if target.atom_type == ResearchAtomType.DEFINITION:
        return ResearchGraphEdgeType.USES_DEFINITION
    if target.atom_type == ResearchAtomType.ASSUMPTION:
        return ResearchGraphEdgeType.USES_ASSUMPTION
    if target.atom_type in _THEOREM_LIKE:
        return ResearchGraphEdgeType.USES_LEMMA
    return ResearchGraphEdgeType.DEPENDS_ON


def _labels_by_atom(atoms: list[ResearchAtom]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for atom in atoms:
        role = atom.role_in_paper or ""
        match = re.search(r"\(label ([^)]+)\)", role)
        if match:
            labels[atom.atom_id] = match.group(1).lower()
    return labels
