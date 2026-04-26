from __future__ import annotations

from typing import Any, Optional

from core.job_store import job_store
from models import (
    DEPENDENCY_EDGE_TYPES,
    ParsedPaper,
    ResearchAtom,
    ResearchGraph,
    is_reviewable,
)


class FormalizationContextError(RuntimeError):
    pass


def load_review_job(job_id: str) -> dict[str, Any]:
    job = job_store.get(job_id)
    if not job:
        raise FormalizationContextError(f"review job {job_id} not found")
    if job.get("status") != "complete":
        raise FormalizationContextError(f"review job {job_id} is not complete")
    if not job.get("parsed_paper") or not job.get("atoms"):
        raise FormalizationContextError(f"review job {job_id} is missing parsed paper or atoms")
    return job


def rehydrate_job(job: dict[str, Any]) -> tuple[ParsedPaper, list[ResearchAtom], Optional[ResearchGraph]]:
    paper = ParsedPaper.model_validate(job["parsed_paper"])
    atoms = [ResearchAtom.model_validate(atom) for atom in job.get("atoms", [])]
    graph_data = job.get("graph")
    graph = ResearchGraph.model_validate(graph_data) if graph_data else None
    return paper, atoms, graph


def default_atom_ids(atoms: list[ResearchAtom]) -> list[str]:
    return [atom.atom_id for atom in atoms if is_reviewable(atom)]


def validate_atom_selection(atoms: list[ResearchAtom], atom_ids: Optional[list[str]]) -> list[str]:
    available = {atom.atom_id for atom in atoms}
    selected = atom_ids or default_atom_ids(atoms)
    unknown = [atom_id for atom_id in selected if atom_id not in available]
    if unknown:
        raise FormalizationContextError(f"unknown atom ids: {', '.join(unknown)}")
    return selected


def build_context(
    *,
    job: dict[str, Any],
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
    graph: Optional[ResearchGraph],
    atom_id: str,
    dependency_limit: int = 3,
    nearby_chars: int = 2200,
) -> dict[str, Any]:
    atom_by_id = {atom.atom_id: atom for atom in atoms}
    atom = atom_by_id.get(atom_id)
    if atom is None:
        raise FormalizationContextError(f"atom {atom_id} not found")

    source_span = atom.source_span
    tex_excerpt = source_span.raw_excerpt
    if paper.assembled_tex and source_span.tex_start is not None and source_span.tex_end is not None:
        tex_excerpt = paper.assembled_tex[source_span.tex_start:source_span.tex_end]

    nearby_prose = _nearby_prose(paper, atom, nearby_chars)
    dependencies = _dependencies(atom, atom_by_id, graph, dependency_limit)

    return {
        "job_id": job.get("job_id"),
        "paper_id": paper.paper_id,
        "title": paper.title,
        "atom_id": atom.atom_id,
        "atom_type": atom.atom_type.value,
        "importance": atom.importance.value,
        "section_id": atom.section_id,
        "section_heading": atom.section_heading,
        "atom_text": atom.text,
        "normalized_text": atom.normalized_text,
        "assumptions": atom.assumptions,
        "conclusions": atom.conclusions,
        "proof_sketch": atom.proof_sketch,
        "key_terms": atom.key_terms,
        "symbols": atom.symbols,
        "tex_excerpt": tex_excerpt[:5000],
        "nearby_prose": nearby_prose,
        "equations": [
            {
                "equation_id": eq.equation_id,
                "latex": eq.latex,
                "label": eq.label,
                "environment": eq.environment,
            }
            for eq in atom.equations
        ],
        "citations": [
            {
                "citation_id": citation.citation_id,
                "key": citation.key,
                "label": citation.label,
                "title": citation.title,
                "authors": citation.authors,
                "year": citation.year,
                "raw_bib_text": citation.raw_bib_text,
            }
            for citation in atom.citations
        ],
        "dependencies": dependencies,
        "formalization_hints": _formalization_hints(atom.text, atom.proof_sketch),
    }


def _nearby_prose(paper: ParsedPaper, atom: ResearchAtom, nearby_chars: int) -> str:
    span = atom.source_span
    if span.char_start is not None and span.char_end is not None:
        start = max(0, span.char_start - nearby_chars)
        end = min(len(paper.raw_text), span.char_end + nearby_chars)
        return paper.raw_text[start:end].strip()
    if atom.section_id:
        for section in paper.sections:
            if section.section_id == atom.section_id:
                return section.content[: nearby_chars * 2].strip()
    return span.raw_excerpt


def _dependencies(
    atom: ResearchAtom,
    atom_by_id: dict[str, ResearchAtom],
    graph: Optional[ResearchGraph],
    dependency_limit: int,
) -> list[dict[str, Any]]:
    if graph is None:
        return []
    deps: list[dict[str, Any]] = []
    for edge in graph.edges:
        if edge.source_id != atom.atom_id or edge.edge_type not in DEPENDENCY_EDGE_TYPES:
            continue
        target = atom_by_id.get(edge.target_id)
        if target is None:
            continue
        deps.append(
            {
                "atom_id": target.atom_id,
                "edge_type": edge.edge_type.value,
                "text": target.text[:800],
                "rationale": edge.rationale,
                "confidence": edge.confidence,
            }
        )
        if len(deps) >= dependency_limit:
            break
    return deps


def _formalization_hints(atom_text: str, proof_sketch: Optional[str]) -> list[str]:
    text = f"{atom_text}\n{proof_sketch or ''}".lower()
    hints: list[str] = []
    if any(term in text for term in ("elbo", "evidence lower bound", "variational lower bound", "kl")):
        hints.append(
            "This is a high-level probabilistic ELBO/KL statement. First formalize the algebraic core over R: "
            "`log_likelihood = kl_div + elbo` and `0 <= kl_div` imply `elbo <= log_likelihood`. "
            "Do not invent Mathlib measure-theory KL APIs unless AXLE confirms the scalar theorem first."
        )
    if "lower bound" in text:
        hints.append("For lower-bound claims, prefer explicit scalar assumptions plus an inequality theorem.")
    return hints
