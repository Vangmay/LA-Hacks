"""ReaderOrchestrator — builds the atom graph for a paper and marks entry-point atoms.

Pipeline:
  arXiv e-print → tex_parser → AtomExtractorAgent → GraphBuilderAgent
  → select start_here atoms → store session state

Annotations are NOT pre-generated; they are produced lazily by the API
layer when the user clicks a node.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.atom_extractor import AtomExtractorAgent
from agents.base import AgentContext
from agents.graph_builder import GraphBuilderAgent
from config import settings
from core.citation_linker import link_citations_to_atoms
from core.equation_linker import link_equations_to_atoms
from core.job_store import job_store
from ingestion import parse_tex
from models import (
    PaperSource,
    ParsedPaper,
    ResearchAtom,
    ResearchGraph,
    SourceKind,
)

logger = logging.getLogger(__name__)

# Root atoms with fewer than this many equations are preferred as entry points.
_COMPLEXITY_EQ_WEIGHT = 50


class ReaderOrchestrator:
    async def run(self, session_id: str, **_kwargs: Any) -> None:
        job = job_store.get(session_id)
        if not job:
            logger.error("reader orchestrator could not find session %s", session_id)
            return

        try:
            job_store.set_status(session_id, "processing")

            paper_source = _build_source(job)
            tex_text = _read_tex(job)
            paper = parse_tex(tex_text, paper_source)

            job_store.update(
                session_id,
                paper_id=paper.paper_id,
                paper_metadata={
                    "title": paper.title,
                    "arxiv_id": job.get("arxiv_id"),
                    "sections": len(paper.sections),
                    "equations": len(paper.equations),
                },
            )

            atoms = await _extract_atoms(session_id, paper)
            atoms = link_equations_to_atoms(paper, atoms)
            atoms = link_citations_to_atoms(paper, atoms)

            graph = await _build_graph(session_id, atoms)

            start_here = _select_start_here(atoms, graph)

            comprehension_states = {a.atom_id: "unvisited" for a in atoms}

            job_store.update(
                session_id,
                atoms=[a.model_dump() for a in atoms],
                graph=graph.model_dump(),
                graph_snapshot=_graph_snapshot(atoms, graph, comprehension_states),
                annotations={},
                comprehension_states=comprehension_states,
                start_here=start_here,
                total_atoms=len(atoms),
                status="complete",
            )
            logger.info(
                "reader session %s complete: %d atoms, %d roots, start_here=%s",
                session_id,
                len(atoms),
                len(graph.roots),
                start_here,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("reader orchestrator failed for %s", session_id)
            job_store.update(session_id, status="error", error=str(exc))


# ---------------------------------------------------------------------------
# Stage helpers


async def _extract_atoms(session_id: str, paper: ParsedPaper) -> list[ResearchAtom]:
    result = await AtomExtractorAgent().run(
        AgentContext(job_id=session_id, parsed_paper=paper)
    )
    if result.status == "error":
        raise RuntimeError(f"atom extraction failed: {result.error}")
    raw = result.output.get("atoms") or []
    atoms = [ResearchAtom.model_validate(a) for a in raw]
    if not atoms:
        raise RuntimeError("atom extraction produced zero atoms")
    return atoms


async def _build_graph(session_id: str, atoms: list[ResearchAtom]) -> ResearchGraph:
    result = await GraphBuilderAgent().run(
        AgentContext(job_id=session_id, extra={"atoms": atoms})
    )
    raw_graph = result.output.get("graph")
    if raw_graph is None:
        atom_ids = [a.atom_id for a in atoms]
        return ResearchGraph(
            paper_id=atoms[0].paper_id if atoms else "?",
            atom_ids=atom_ids,
            edges=[],
            roots=atom_ids,
            topological_order=atom_ids,
            warnings=["graph builder produced no graph"],
        )
    return ResearchGraph.model_validate(raw_graph)


def _select_start_here(
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
    max_entries: int = 3,
) -> list[str]:
    """Pick 1–3 root atoms sorted by ascending complexity (shorter = simpler)."""
    root_ids = set(graph.roots)
    atom_by_id = {a.atom_id: a for a in atoms}
    root_atoms = [atom_by_id[aid] for aid in root_ids if aid in atom_by_id]

    if not root_atoms:
        root_atoms = list(atoms)

    def _complexity(atom: ResearchAtom) -> int:
        return len(atom.equations) * _COMPLEXITY_EQ_WEIGHT + len(atom.text)

    root_atoms.sort(key=_complexity)
    return [a.atom_id for a in root_atoms[:max_entries]]


def _graph_snapshot(
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
    comprehension_states: dict[str, str],
) -> dict[str, Any]:
    nodes = [
        {
            "id": atom.atom_id,
            "kind": "atom",
            "atom_type": atom.atom_type.value,
            "section": atom.section_heading,
            "label": _node_label(atom),
            "comprehension_status": comprehension_states.get(atom.atom_id, "unvisited"),
            "importance": atom.importance.value,
            "source_excerpt": atom.source_span.raw_excerpt[:200],
        }
        for atom in atoms
    ]
    edges = [
        {
            "id": edge.edge_id,
            "source": edge.source_id,
            "target": edge.target_id,
            "edge_type": edge.edge_type.value,
            "confidence": edge.confidence,
            "rationale": edge.rationale,
        }
        for edge in graph.edges
    ]
    return {"nodes": nodes, "edges": edges}


def _node_label(atom: ResearchAtom) -> str:
    base = atom.atom_type.value.replace("_", " ").title()
    if atom.section_heading:
        return f"{base} ({atom.section_heading[:30]})"
    return base


def _build_source(job: dict[str, Any]) -> PaperSource:
    arxiv_id = job.get("arxiv_id")
    tex_path = job.get("tex_path")
    content_hash = "0" * 16
    if tex_path:
        try:
            content_hash = hashlib.md5(Path(tex_path).read_bytes()).hexdigest()[:16]
        except OSError:
            pass
    paper_id = arxiv_id or content_hash
    return PaperSource(
        paper_id=paper_id,
        source_kind=SourceKind.ARXIV if arxiv_id else SourceKind.MANUAL_TEX,
        arxiv_id=arxiv_id,
        source_url=job.get("arxiv_source_url"),
        abs_url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None,
        source_archive_path=job.get("source_archive_path"),
        source_extract_dir=job.get("source_extract_dir"),
        main_tex_path=job.get("main_tex_path"),
        assembled_tex_path=tex_path,
        fetched_at=datetime.utcnow(),
        content_hash=content_hash,
    )


def _read_tex(job: dict[str, Any]) -> str:
    tex_path = job.get("tex_path")
    if not tex_path:
        raise RuntimeError("session has no tex_path")
    return Path(tex_path).read_text(encoding="utf-8", errors="replace")
