"""Review orchestrator for the v0.4 source-grounded pipeline.

source → parse → atoms → spans/equations/citations → graph → checks →
challenges → rebuttals → verdicts → cascade → report.

The orchestrator stores its progress in `job_store` as plain dicts (so the
existing API/SSE wiring keeps working), and emits typed `DAGEvent`s at
every meaningful stage.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.atom_extractor import AtomExtractorAgent
from agents.base import AgentContext
from agents.cascade import apply_cascade
from agents.challenge_agent import ChallengeAgent
from agents.defense_agent import DefenseAgent
from agents.graph_builder import GraphBuilderAgent
from agents.report_agent import build_review_report
from agents.verdict_aggregator import aggregate_verdict
from checks import run_algebraic_sanity, run_citation_probe, run_numeric_probe
from config import settings
from core.citation_linker import link_citations_to_atoms
from core.equation_linker import link_equations_to_atoms
from core.event_bus import event_bus
from core.job_store import job_store
from ingestion import parse_tex
from models import (
    AtomVerdict,
    Challenge,
    CheckKind,
    CheckResult,
    CheckStatus,
    DAGEvent,
    DAGEventType,
    PaperSource,
    ParsedPaper,
    Rebuttal,
    ResearchAtom,
    ResearchGraph,
    ReviewReport,
    SourceKind,
    is_reviewable,
)

logger = logging.getLogger(__name__)


class ReviewOrchestrator:
    async def run(self, job_id: str, **_kwargs: Any) -> None:
        job = job_store.get(job_id)
        if not job:
            logger.error("review orchestrator could not find job %s", job_id)
            return

        await _publish(job_id, DAGEventType.JOB_CREATED, payload={"job_id": job_id})
        try:
            job_store.set_status(job_id, "processing")

            paper_source = _build_source(job)
            await _publish(job_id, DAGEventType.SOURCE_FETCH_COMPLETE, payload={
                "paper_id": paper_source.paper_id,
                "source_url": paper_source.source_url,
            })

            await _publish(job_id, DAGEventType.PARSE_STARTED, payload={})
            tex_text = _read_tex(job)
            paper = parse_tex(tex_text, paper_source)
            job_store.update(
                job_id,
                paper_id=paper.paper_id,
                parsed_paper=paper.model_dump(),
                paper_title=paper.title,
            )
            await _publish(job_id, DAGEventType.PARSE_COMPLETE, payload={
                "title": paper.title,
                "sections": len(paper.sections),
                "equations": len(paper.equations),
                "bibliography": len(paper.bibliography),
                "warnings": paper.parser_warnings,
            })

            atoms = await _extract_atoms(job_id, paper)
            atoms = link_equations_to_atoms(paper, atoms)
            atoms = link_citations_to_atoms(paper, atoms)

            job_store.update(
                job_id,
                atoms=[a.model_dump() for a in atoms],
                total_atoms=len(atoms),
                completed_atoms=0,
            )
            for atom in atoms:
                await _publish(
                    job_id,
                    DAGEventType.ATOM_CREATED,
                    atom_id=atom.atom_id,
                    payload=_atom_payload(atom),
                )
            await _publish(job_id, DAGEventType.ATOM_EXTRACTION_COMPLETE, payload={
                "total_atoms": len(atoms),
            })

            graph = await _build_graph(job_id, atoms)
            job_store.update(job_id, graph=graph.model_dump())
            for edge in graph.edges:
                await _publish(
                    job_id,
                    DAGEventType.EDGE_CREATED,
                    payload=edge.model_dump(),
                )
            await _publish(job_id, DAGEventType.GRAPH_BUILD_COMPLETE, payload={
                "edges": len(graph.edges),
                "roots": graph.roots,
            })
            job_store.update(job_id, graph_snapshot=_graph_snapshot(atoms, graph))

            verdicts = await _review_atoms(job_id, paper, atoms, graph)

            verdicts = apply_cascade(verdicts, graph)
            for verdict in verdicts:
                if verdict.is_cascaded:
                    await _publish(
                        job_id,
                        DAGEventType.CASCADE_TRIGGERED,
                        atom_id=verdict.atom_id,
                        payload={
                            "label": verdict.label.value,
                            "cascade_source": verdict.cascade_source_atom_id,
                        },
                    )

            for verdict in verdicts:
                await _publish(
                    job_id,
                    DAGEventType.VERDICT_EMITTED,
                    atom_id=verdict.atom_id,
                    payload={
                        "label": verdict.label.value,
                        "confidence": verdict.confidence,
                        "reason_codes": [c.value for c in verdict.reason_codes],
                    },
                )

            report = build_review_report(
                job_id=job_id,
                paper=paper,
                atoms=atoms,
                graph=graph,
                verdicts=verdicts,
                arxiv_id=job.get("arxiv_id"),
                tex_path=job.get("tex_path"),
            )
            job_store.update(
                job_id,
                verdicts=[v.model_dump() for v in verdicts],
                report=report.model_dump(),
                graph_snapshot=_graph_snapshot(atoms, graph, verdicts=verdicts),
                completed_atoms=len(atoms),
                status="complete",
            )
            await _publish(
                job_id,
                DAGEventType.REPORT_READY,
                payload={"report_id": report.report_id},
            )
            await _publish(job_id, DAGEventType.JOB_COMPLETE, payload={
                "total_atoms": len(atoms),
                "summary": report.summary.model_dump(),
            })
        except Exception as exc:  # noqa: BLE001
            logger.exception("review orchestrator failed for %s", job_id)
            job_store.update(job_id, status="error", error=str(exc))
            await _publish(job_id, DAGEventType.JOB_ERROR, payload={"error": str(exc)})


# ---------------------------------------------------------------------------
# Stage helpers


async def _extract_atoms(job_id: str, paper: ParsedPaper) -> list[ResearchAtom]:
    await _publish(job_id, DAGEventType.ATOM_EXTRACTION_STARTED, payload={})
    agent = AtomExtractorAgent()
    result = await agent.run(AgentContext(job_id=job_id, parsed_paper=paper))
    if result.status == "error":
        raise RuntimeError(f"atom extraction failed: {result.error}")
    raw_atoms = result.output.get("atoms") or []
    atoms = [ResearchAtom.model_validate(a) for a in raw_atoms]
    if not atoms:
        raise RuntimeError("atom extraction produced zero atoms")
    return atoms


async def _build_graph(job_id: str, atoms: list[ResearchAtom]) -> ResearchGraph:
    await _publish(job_id, DAGEventType.GRAPH_BUILD_STARTED, payload={})
    agent = GraphBuilderAgent()
    result = await agent.run(
        AgentContext(job_id=job_id, extra={"atoms": atoms}),
    )
    raw_graph = result.output.get("graph")
    if raw_graph is None:
        # Empty graph fallback — keep atoms but with no edges.
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


async def _review_atoms(
    job_id: str,
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
) -> list[AtomVerdict]:
    challenge_agent = ChallengeAgent()
    defense_agent = DefenseAgent()
    semaphore = asyncio.Semaphore(max(1, settings.max_parallel_claims))
    completed_lock = asyncio.Lock()
    completed = 0

    async def review_one(atom: ResearchAtom) -> AtomVerdict:
        nonlocal completed
        async with semaphore:
            checks: list[CheckResult] = []
            challenges: list[Challenge] = []
            rebuttals: list[Rebuttal] = []

            if is_reviewable(atom):
                await _publish(
                    job_id,
                    DAGEventType.CHECK_STARTED,
                    atom_id=atom.atom_id,
                    payload={"kinds": ["algebraic_sanity", "numeric_counterexample_probe", "citation_context"]},
                )
                alg = run_algebraic_sanity(atom, paper)
                cite = run_citation_probe(atom)
                num: CheckResult
                try:
                    num = await run_numeric_probe(atom)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("numeric_probe raised for %s", atom.atom_id)
                    num = CheckResult(
                        check_id=f"check_num_{atom.atom_id}_err",
                        atom_id=atom.atom_id,
                        kind=CheckKind.NUMERIC_COUNTEREXAMPLE_PROBE,
                        status=CheckStatus.INCONCLUSIVE,
                        summary=f"numeric probe error: {exc}",
                        confidence=0.0,
                    )
                checks = [alg, num, cite]
                for check in checks:
                    await _publish(
                        job_id,
                        DAGEventType.CHECK_COMPLETE,
                        atom_id=atom.atom_id,
                        payload={
                            "kind": check.kind.value,
                            "status": check.status.value,
                            "summary": check.summary,
                            "confidence": check.confidence,
                        },
                    )

                ctx = AgentContext(
                    job_id=job_id,
                    parsed_paper=paper,
                    atom=atom,
                    graph=graph,
                    checks=checks,
                )
                ch_result = await challenge_agent.run(ctx)
                challenges = [
                    Challenge.model_validate(c)
                    for c in ch_result.output.get("challenges") or []
                ]
                for challenge in challenges:
                    await _publish(
                        job_id,
                        DAGEventType.CHALLENGE_ISSUED,
                        atom_id=atom.atom_id,
                        payload=challenge.model_dump(),
                    )

                if challenges:
                    df_ctx = AgentContext(
                        job_id=job_id,
                        parsed_paper=paper,
                        atom=atom,
                        graph=graph,
                        checks=checks,
                        challenges=challenges,
                    )
                    df_result = await defense_agent.run(df_ctx)
                    rebuttals = [
                        Rebuttal.model_validate(r)
                        for r in df_result.output.get("rebuttals") or []
                    ]
                    for rebuttal in rebuttals:
                        await _publish(
                            job_id,
                            DAGEventType.REBUTTAL_ISSUED,
                            atom_id=atom.atom_id,
                            payload=rebuttal.model_dump(),
                        )

            verdict = aggregate_verdict(atom, checks, challenges, rebuttals)

            async with completed_lock:
                completed += 1
                job_store.update(job_id, completed_atoms=completed)
            return verdict

    tasks = [review_one(atom) for atom in atoms]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    verdicts: list[AtomVerdict] = []
    for atom, result in zip(atoms, results):
        if isinstance(result, Exception):
            logger.warning("verdict gather error for %s: %s", atom.atom_id, result)
            verdicts.append(
                aggregate_verdict(atom, [], [], [])
            )
        else:
            verdicts.append(result)
    return verdicts


# ---------------------------------------------------------------------------
# helpers


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
        raise RuntimeError("job has no tex_path")
    return Path(tex_path).read_text(encoding="utf-8", errors="replace")


def _atom_payload(atom: ResearchAtom) -> dict[str, Any]:
    return {
        "atom_id": atom.atom_id,
        "atom_type": atom.atom_type.value,
        "section_heading": atom.section_heading,
        "importance": atom.importance.value,
        "text": atom.text[:500],
        "source_excerpt": atom.source_span.raw_excerpt[:500],
        "equations": [eq.equation_id for eq in atom.equations],
        "citations": [c.citation_id for c in atom.citations],
    }


def _graph_snapshot(
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
    *,
    verdicts: Optional[list[AtomVerdict]] = None,
) -> dict[str, Any]:
    verdict_label = {v.atom_id: v.label.value for v in (verdicts or [])}
    nodes = [
        {
            "id": atom.atom_id,
            "kind": "atom",
            "atom_type": atom.atom_type.value,
            "section": atom.section_heading,
            "label": _node_label(atom),
            "status": verdict_label.get(atom.atom_id, "pending"),
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


async def _publish(
    job_id: str,
    event_type: DAGEventType,
    *,
    atom_id: Optional[str] = None,
    node_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    # A single failed emit must not kill the orchestration: SSE telemetry is
    # observability, not load-bearing state. Log and continue.
    try:
        await event_bus.publish(
            job_id,
            DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=event_type,
                atom_id=atom_id,
                node_id=node_id,
                payload=payload or {},
                timestamp=datetime.utcnow(),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("review orchestrator: failed to emit %s: %s", event_type, exc)
