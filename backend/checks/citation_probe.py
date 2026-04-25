"""Citation context check.

Honest, deterministic. No LLM. The probe just looks at the atom and its
attached citation entries:

- If the atom appears to make an external claim (mentions
  "[1]"/`\\cite{...}` keys or terms like "show", "prove", "shown in") but
  has zero attached citations → flag a citation gap.
- If citations were attached but their bib text is empty (i.e. we couldn't
  resolve the key) → inconclusive, mark which keys.
- Otherwise → passed.
"""
from __future__ import annotations

import re
import uuid

from models import (
    CheckKind,
    CheckResult,
    CheckStatus,
    Evidence,
    EvidenceSourceType,
    ResearchAtom,
)


_EXTERNAL_CLAIM_RE = re.compile(
    r"\b(?:show(?:n|ed)?|prove[ds]?|introduce[ds]?|propose[ds]?|"
    r"establish(?:ed|es)?|first studied|recently|prior work|previous work|"
    r"following|extends?)\b",
    re.IGNORECASE,
)


def run_citation_probe(atom: ResearchAtom) -> CheckResult:
    check_id = f"check_cite_{atom.atom_id}_{uuid.uuid4().hex[:6]}"

    has_citations = bool(atom.citations)
    looks_external = bool(_EXTERNAL_CLAIM_RE.search(atom.text or ""))

    if not has_citations and looks_external:
        return CheckResult(
            check_id=check_id,
            atom_id=atom.atom_id,
            kind=CheckKind.CITATION_CONTEXT,
            status=CheckStatus.FAILED,
            summary="atom appears to reference prior work but has no attached citations",
            evidence=[
                Evidence(
                    evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                    source_type=EvidenceSourceType.PAPER_SPAN,
                    text=atom.source_span.raw_excerpt[:500],
                    paper_id=atom.paper_id,
                    atom_id=atom.atom_id,
                    check_id=check_id,
                    confidence=0.6,
                )
            ],
            confidence=0.6,
        )

    if not has_citations:
        return CheckResult(
            check_id=check_id,
            atom_id=atom.atom_id,
            kind=CheckKind.CITATION_CONTEXT,
            status=CheckStatus.NOT_APPLICABLE,
            summary="atom does not reference external work",
            confidence=0.1,
        )

    unresolved = [c for c in atom.citations if not (c.raw_bib_text or "").strip()]
    if unresolved and len(unresolved) == len(atom.citations):
        keys = ", ".join((c.key or c.label or "?") for c in unresolved)
        return CheckResult(
            check_id=check_id,
            atom_id=atom.atom_id,
            kind=CheckKind.CITATION_CONTEXT,
            status=CheckStatus.INCONCLUSIVE,
            summary=f"all attached citations unresolved (no bib entry): {keys}",
            evidence=[
                Evidence(
                    evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                    source_type=EvidenceSourceType.CITATION,
                    text=f"unresolved citation keys: {keys}",
                    paper_id=atom.paper_id,
                    atom_id=atom.atom_id,
                    check_id=check_id,
                    confidence=0.4,
                )
            ],
            confidence=0.4,
        )

    return CheckResult(
        check_id=check_id,
        atom_id=atom.atom_id,
        kind=CheckKind.CITATION_CONTEXT,
        status=CheckStatus.PASSED,
        summary=f"{len(atom.citations)} citation(s) attached to atom",
        confidence=0.6,
    )
