"""Offline tests for atom candidate grounding, filtering, and dedupe."""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.atom_extractor import (  # noqa: E402
    AtomExtractorAgent,
    _dedupe_candidates,
    _finalize_atom_headers,
    _filter_grounded_candidates,
    _ground_candidates,
    _local_candidate_filter,
    _loads_json_object,
    _resolve_candidate_spans,
)
from ingestion.tex_parser import parse_tex  # noqa: E402
from models import (  # noqa: E402
    AtomCandidate,
    AtomImportance,
    AtomReviewability,
    PaperSource,
    ResearchAtom,
    ResearchAtomType,
    SourceKind,
    SourceSpan,
)


SAMPLE_TEX = r"""
\documentclass{article}
\title{Candidate Cleanup Test}
\begin{document}
\section{Main}
The variational lower bound can be optimized by stochastic gradients.
The reparameterization trick provides a differentiable estimator.
\end{document}
"""

ALGORITHM_TEX = r"""
\documentclass{article}
\title{Algorithm Caption Test}
\begin{document}
\section{Main}
\begin{theorem}
For every real number x, x squared is nonnegative.
\end{theorem}
\begin{algorithm}[t]
\caption{Minibatch version of a training algorithm. Either stochastic estimator can be used.}
\begin{algorithmic}
\STATE Sample a minibatch.
\STATE Update parameters.
\end{algorithmic}
\end{algorithm}
\end{document}
"""


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _paper():
    source = PaperSource(
        paper_id="candidate-test",
        source_kind=SourceKind.MANUAL_TEX,
        fetched_at=datetime.utcnow(),
        content_hash=hashlib.md5(SAMPLE_TEX.encode("utf-8")).hexdigest()[:16],
    )
    return parse_tex(SAMPLE_TEX, source)


def _algorithm_paper():
    source = PaperSource(
        paper_id="algorithm-caption-test",
        source_kind=SourceKind.MANUAL_TEX,
        fetched_at=datetime.utcnow(),
        content_hash=hashlib.md5(ALGORITHM_TEX.encode("utf-8")).hexdigest()[:16],
    )
    return parse_tex(ALGORITHM_TEX, source)


def _candidate(candidate_id: str, quote: str, text: str | None = None) -> AtomCandidate:
    return AtomCandidate(
        candidate_id=candidate_id,
        paper_id="candidate-test",
        atom_type=ResearchAtomType.ASSERTION,
        source_quote=quote,
        text=text or quote,
        section_heading="Main",
        importance=AtomImportance.HIGH,
        reviewability=AtomReviewability.REVIEWABLE,
        confidence=0.9,
    )


def test_exact_grounding_survives() -> None:
    paper = _paper()
    candidate = _candidate(
        "cand_001",
        "The variational lower bound can be optimized by stochastic gradients.",
    )
    grounded, warnings = _ground_candidates(paper, [candidate])
    _assert(len(grounded) == 1, f"expected one grounded candidate: {warnings}")
    _assert(
        grounded[0].source_span is not None
        and grounded[0].source_span.match_confidence == 1.0,
        f"expected exact span, got {grounded[0].source_span}",
    )


def test_low_confidence_grounding_drops() -> None:
    paper = _paper()
    candidate = _candidate("cand_bad", "This sentence does not occur in the paper.")
    resolved, _ = _resolve_candidate_spans(paper, [candidate])
    grounded, warnings = _filter_grounded_candidates(resolved)
    _assert(not grounded, "bad source quote should not enter final atoms")
    _assert(
        any("dropped_low_confidence_span: cand_bad" in warning for warning in warnings),
        f"expected low-confidence warning, got {warnings}",
    )


def test_duplicate_candidates_merge() -> None:
    paper = _paper()
    candidates = [
        _candidate(
            "cand_001",
            "The reparameterization trick provides a differentiable estimator.",
        ),
        _candidate(
            "cand_002",
            "The reparameterization trick provides a differentiable estimator.",
            "Reparameterization trick provides a differentiable estimator.",
        ),
    ]
    grounded, warnings = _ground_candidates(paper, candidates)
    deduped = _dedupe_candidates(grounded, warnings)
    _assert(len(deduped) == 1, f"expected duplicate merge, got {deduped}")
    _assert(
        any("deduped_candidate" in warning for warning in warnings),
        f"expected dedupe warning, got {warnings}",
    )


def test_json_backslash_repair() -> None:
    raw = r'{"candidates": [{"source_quote": "where \dmodel is used and \u is malformed"}]}'
    data, warning = _loads_json_object(raw)
    _assert(data is not None, f"JSON repair failed: {warning}")
    quote = data["candidates"][0]["source_quote"]
    _assert("\\dmodel" in quote and "\\u" in quote, f"bad repaired quote: {quote!r}")
    _assert(warning, "expected repair warning")


def test_dangling_header_repaired_or_dropped() -> None:
    atom = ResearchAtom(
        atom_id="atom_001",
        paper_id="candidate-test",
        atom_type=ResearchAtomType.ASSERTION,
        text="The full VB estimator is differentiable with respect to the variational parameters bphi because",
        source_span=SourceSpan(
            paper_id="candidate-test",
            raw_excerpt="The proposed estimator can be straightforwardly differentiated and optimized using standard stochastic gradient methods.",
            match_confidence=1.0,
        ),
        extraction_confidence=0.8,
        importance=AtomImportance.HIGH,
    )
    cleaned, warnings = _finalize_atom_headers([atom])
    _assert(len(cleaned) == 1, f"expected repair from source excerpt: {warnings}")
    _assert(not cleaned[0].text.lower().endswith("because"), cleaned[0].text)
    _assert(
        "differentiated and optimized" in cleaned[0].text,
        f"unexpected repaired header: {cleaned[0].text}",
    )
    _assert(any("final_header_repaired" in warning for warning in warnings), str(warnings))


def test_dangling_header_with_formula_excerpt_dropped() -> None:
    atom = ResearchAtom(
        atom_id="atom_001",
        paper_id="candidate-test",
        atom_type=ResearchAtomType.THEOREM,
        text="When both the prior p theta z and posterior approximation q phi z given x are",
        source_span=SourceSpan(
            paper_id="candidate-test",
            raw_excerpt=r"$D_{KL}((\qPhi(\bz) || \pT(\bz)) = \frac{1}{2} \sum_j (1 + \log \sigma_j^2 - \mu_j^2 - \sigma_j^2)$",
            match_confidence=1.0,
        ),
        extraction_confidence=0.8,
        importance=AtomImportance.HIGH,
    )
    cleaned, warnings = _finalize_atom_headers([atom])
    _assert(not cleaned, f"formula-only excerpt should not repair dangling English: {cleaned}")
    _assert(any("final_header_dropped" in warning for warning in warnings), str(warnings))


def test_long_clean_english_header_is_not_cropped() -> None:
    text = (
        "The variational autoencoder uses a neural network recognition model "
        "to approximate the posterior distribution while optimizing a stochastic "
        "variational lower bound with gradient-based learning"
    )
    atom = ResearchAtom(
        atom_id="atom_001",
        paper_id="candidate-test",
        atom_type=ResearchAtomType.ASSERTION,
        text=text,
        source_span=SourceSpan(
            paper_id="candidate-test",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=0.8,
        importance=AtomImportance.HIGH,
    )
    cleaned, warnings = _finalize_atom_headers([atom])
    _assert(len(cleaned) == 1, f"long clean English should survive: {warnings}")
    _assert(cleaned[0].text == text, "header text was unexpectedly cropped")


def test_raw_latex_display_text_dropped() -> None:
    atom = ResearchAtom(
        atom_id="atom_001",
        paper_id="candidate-test",
        atom_type=ResearchAtomType.ASSERTION,
        text=r"The posterior is $q_\phi(z|x)$ and the prior is \mathcal{N}(0,I)",
        source_span=SourceSpan(
            paper_id="candidate-test",
            raw_excerpt=r"$q_\phi(z|x)$ and $\mathcal{N}(0,I)$",
            match_confidence=1.0,
        ),
        extraction_confidence=0.8,
        importance=AtomImportance.HIGH,
    )
    cleaned, warnings = _finalize_atom_headers([atom])
    _assert(not cleaned, f"raw-LaTeX display text should not survive: {cleaned}")
    _assert(any("final_header_dropped" in warning for warning in warnings), str(warnings))


def test_algorithm_caption_candidate_locally_dropped() -> None:
    paper = _algorithm_paper()
    extractor = AtomExtractorAgent()
    candidates = extractor._extract_environment_candidates(paper)
    _assert(
        any(candidate.atom_type == ResearchAtomType.THEOREM for candidate in candidates),
        f"expected theorem env candidate, got {candidates}",
    )
    _assert(
        any(
            candidate.atom_type == ResearchAtomType.ALGORITHM
            and "caption" in candidate.text.lower()
            for candidate in candidates
        ),
        f"expected raw algorithm caption candidate, got {candidates}",
    )

    warnings: list[str] = []
    kept = _local_candidate_filter(candidates, warnings)
    _assert(
        any(candidate.atom_type == ResearchAtomType.THEOREM for candidate in kept),
        f"theorem candidate should remain: {warnings}",
    )
    _assert(
        not any(
            candidate.atom_type == ResearchAtomType.ALGORITHM
            and "caption" in candidate.text.lower()
            for candidate in kept
        ),
        f"raw algorithm caption candidate leaked through local filter: {kept}",
    )


def main() -> int:
    test_exact_grounding_survives()
    print("  exact candidate grounding survives - OK")
    test_low_confidence_grounding_drops()
    print("  low-confidence candidate grounding drops - OK")
    test_duplicate_candidates_merge()
    print("  duplicate candidates merge - OK")
    test_json_backslash_repair()
    print("  model JSON backslash repair - OK")
    test_dangling_header_repaired_or_dropped()
    print("  dangling header repaired or dropped - OK")
    test_dangling_header_with_formula_excerpt_dropped()
    print("  dangling formula-header dropped - OK")
    test_long_clean_english_header_is_not_cropped()
    print("  long clean English header is not cropped - OK")
    test_raw_latex_display_text_dropped()
    print("  raw LaTeX display text dropped - OK")
    test_algorithm_caption_candidate_locally_dropped()
    print("  raw algorithm caption candidate locally dropped - OK")
    print("atom candidate cleanup tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
