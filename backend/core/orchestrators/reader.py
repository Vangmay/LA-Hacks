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
            job_store.update(
                session_id,
                status="processing",
                reader_stage="Preparing source",
                graph_snapshot=_graph_snapshot([], stage="Preparing source"),
            )

            paper_source = _build_source(job)
            tex_text = _read_tex(job)
            job_store.update(
                session_id,
                reader_stage="Parsing TeX",
                graph_snapshot=_graph_snapshot([], stage="Parsing TeX"),
            )
            paper = parse_tex(tex_text, paper_source)

            job_store.update(
                session_id,
                reader_stage="Extracting atoms",
                paper_id=paper.paper_id,
                paper_metadata={
                    "title": paper.title,
                    "arxiv_id": job.get("arxiv_id"),
                    "sections": len(paper.sections),
                    "equations": len(paper.equations),
                },
            )

            async def on_atom_progress(partial_atoms: list[ResearchAtom], progress: dict[str, Any]) -> None:
                current_job = job_store.get(session_id) or {}
                prev_snapshot = current_job.get("graph_snapshot") or {}
                stage = progress.get("stage", "Extracting atoms")
                # Preserve previously-reported batch counts when a later phase
                # (normalization) emits without them; otherwise the progress
                # bar would reset from N/N back to 0/0.
                completed = progress.get("batches_completed")
                if completed is None:
                    completed = prev_snapshot.get("extraction_batches_completed")
                total = progress.get("batches_total")
                if total is None:
                    total = prev_snapshot.get("extraction_batches_total")
                current_batch = progress.get("current_batch")
                if current_batch is None:
                    current_batch = prev_snapshot.get("extraction_current_batch")
                visible_atoms = partial_atoms
                recent_atoms = _recent_atom_snapshots(partial_atoms)
                job_store.update(
                    session_id,
                    total_atoms=max(len(partial_atoms), current_job.get("total_atoms", 0)),
                    reader_stage=stage,
                    graph_snapshot=_graph_snapshot(
                        visible_atoms,
                        stage=stage,
                        extraction_batches_completed=completed,
                        extraction_batches_total=total,
                        extraction_current_batch=current_batch,
                        parsed_atoms=len(partial_atoms),
                        recent_atoms=recent_atoms,
                    ),
                )

            atoms = await _extract_atoms(session_id, paper, on_atom_progress)
            atoms = link_equations_to_atoms(paper, atoms)
            atoms = link_citations_to_atoms(paper, atoms)
            comprehension_states = {a.atom_id: "unvisited" for a in atoms}
            job_store.update(
                session_id,
                atoms=[a.model_dump() for a in atoms],
                annotations={},
                comprehension_states=comprehension_states,
                total_atoms=len(atoms),
                reader_stage="Building dependency graph",
                graph_snapshot=_graph_snapshot(
                    atoms,
                    comprehension_states=comprehension_states,
                    stage="Building dependency graph",
                ),
            )

            graph = await _build_graph(session_id, atoms)

            start_here = _select_start_here(atoms, graph)

            job_store.update(
                session_id,
                graph=graph.model_dump(),
                graph_snapshot=_graph_snapshot(
                    atoms,
                    graph,
                    comprehension_states,
                    start_here=start_here,
                    stage="Ready",
                ),
                start_here=start_here,
                reader_stage="Ready",
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


async def _extract_atoms(
    session_id: str,
    paper: ParsedPaper,
    progress_callback=None,
) -> list[ResearchAtom]:
    result = await AtomExtractorAgent(progress_callback=progress_callback).run(
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
    graph: ResearchGraph | None = None,
    comprehension_states: dict[str, str] | None = None,
    start_here: list[str] | None = None,
    stage: str | None = None,
    extraction_batches_completed: int | None = None,
    extraction_batches_total: int | None = None,
    extraction_current_batch: int | None = None,
    parsed_atoms: int | None = None,
    recent_atoms: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    comprehension_states = comprehension_states or {}
    start_set = set(start_here or [])
    nodes = [
        {
            "id": atom.atom_id,
            "kind": "atom",
            "atom_type": atom.atom_type.value,
            "section": atom.section_heading,
            "label": _node_label(atom),
            "text": atom.text,
            "parsed_order": idx + 1,
            "comprehension_status": comprehension_states.get(atom.atom_id, "unvisited"),
            "importance": atom.importance.value,
            "source_excerpt": atom.source_span.raw_excerpt[:500],
            "start_here": atom.atom_id in start_set,
        }
        for idx, atom in enumerate(atoms)
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
        for edge in (graph.edges if graph is not None else [])
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "start_here": start_here or [],
        "stage": stage or "Building learner graph",
        "parsed_atoms": parsed_atoms if parsed_atoms is not None else len(nodes),
        "total_atoms": len(nodes),
        "extraction_batches_completed": extraction_batches_completed,
        "extraction_batches_total": extraction_batches_total,
        "extraction_current_batch": extraction_current_batch,
        "recent_atoms": recent_atoms if recent_atoms is not None else [
            {
                "id": node["id"],
                "label": node["label"],
                "parsed_order": node["parsed_order"],
            }
            for node in nodes[-5:]
        ],
    }


def _recent_atom_snapshots(atoms: list[ResearchAtom], limit: int = 5) -> list[dict[str, Any]]:
    start = max(len(atoms) - limit + 1, 1)
    return [
        {
            "id": atom.atom_id,
            "label": atom.text or _node_label(atom),
            "parsed_order": idx,
        }
        for idx, atom in enumerate(atoms[-limit:], start=start)
    ]


def _node_label(atom: ResearchAtom) -> str:
    text = _clean_label_text(atom.text or atom.source_span.raw_excerpt or "")
    if not text:
        return atom.atom_id

    lowered = text.lower()
    for prefix in (
        "we introduce ",
        "we propose ",
        "we present ",
        "we construct ",
        "we define ",
        "we prove ",
        "we show ",
        "this paper introduces ",
        "this paper presents ",
        "the paper introduces ",
        "the paper presents ",
    ):
        if lowered.startswith(prefix):
            text = text[len(prefix):]
            break

    return _safe_concept_label(text) or atom.atom_id


def _clean_label_text(text: str) -> str:
    text = text.replace("$", " ")
    for char in "\\{}[]()":
        text = text.replace(char, " ")
    return " ".join(text.split())


def _safe_concept_label(text: str, limit: int = 96) -> str:
    cleaned = " ".join(str(text or "").split()).strip(" ,.;:")
    if len(cleaned) <= limit:
        return cleaned
    clipped = cleaned[:limit].rsplit(" ", 1)[0].strip(" ,.;:")
    dangling = {
        "a", "an", "the", "at", "to", "of", "by", "with", "for", "from", "in",
        "on", "and", "or", "but", "as", "than", "that", "which", "less", "more",
    }
    words = clipped.split()
    while words and words[-1].lower().strip(" ,.;:") in dangling:
        words.pop()
    return " ".join(words).strip(" ,.;:") or cleaned[:limit].strip(" ,.;:")


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
