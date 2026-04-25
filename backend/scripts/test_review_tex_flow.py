"""Offline flow test for arXiv TeX review submission and orchestration.

This test makes no network calls and no OpenAI calls. It patches only the
external/LLM boundaries of the v0.4 ResearchAtom pipeline.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

import api.review as review_api  # noqa: E402
import core.orchestrators.review as review_orchestrator_module  # noqa: E402
from agents.base import AgentResult  # noqa: E402
from core.event_bus import event_bus  # noqa: E402
from core.job_store import job_store  # noqa: E402
from core.orchestrators.review import ReviewOrchestrator  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    Challenge,
    ChallengeType,
    CheckKind,
    CheckResult,
    CheckStatus,
    Rebuttal,
    RebuttalType,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraph,
    ResearchGraphEdge,
    ResearchGraphEdgeType,
    Severity,
    SourceSpan,
)


SAMPLE_TEX = r"""
\documentclass{article}
\title{Mock Source Paper}
\begin{document}
\begin{abstract}A mock abstract.\end{abstract}
\section{Foundations}
\begin{theorem}For every $x \in \mathbb{R}$, $x^2 \ge 0$.\end{theorem}
\begin{equation}x^2 \ge 0\end{equation}
\section{Consequence}
\begin{proposition}The minimum value is attained at $x=0$.\end{proposition}
\end{document}
"""


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom(atom_id: str, atom_type: ResearchAtomType, text: str, section: str) -> ResearchAtom:
    return ResearchAtom(
        atom_id=atom_id,
        paper_id="1706.03762",
        atom_type=atom_type,
        text=text,
        section_id=f"sec_{section.lower()}",
        section_heading=section,
        source_span=SourceSpan(
            paper_id="1706.03762",
            section_id=f"sec_{section.lower()}",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=0.95,
        importance=AtomImportance.HIGH,
    )


class FakeAtomExtractorAgent:
    async def run(self, _context):
        atoms = [
            _atom(
                "atom_001",
                ResearchAtomType.THEOREM,
                "For every $x \\in \\mathbb{R}$, $x^2 \\ge 0$.",
                "Foundations",
            ),
            _atom(
                "atom_002",
                ResearchAtomType.PROPOSITION,
                "The minimum value is attained at $x=0$.",
                "Consequence",
            ),
        ]
        return AgentResult(
            agent_id="atom_extractor",
            status="success",
            output={"paper_id": "1706.03762", "atoms": [a.model_dump() for a in atoms], "warnings": []},
            confidence=0.95,
        )


class FakeGraphBuilderAgent:
    async def run(self, context):
        atoms = context.extra["atoms"]
        graph = ResearchGraph(
            paper_id="1706.03762",
            atom_ids=[a.atom_id for a in atoms],
            edges=[
                ResearchGraphEdge(
                    edge_id="edge_001",
                    source_id="atom_002",
                    target_id="atom_001",
                    edge_type=ResearchGraphEdgeType.DEPENDS_ON,
                    rationale="minimum statement depends on nonnegativity theorem",
                    confidence=0.9,
                )
            ],
            roots=["atom_001"],
            topological_order=["atom_001", "atom_002"],
        )
        return AgentResult(
            agent_id="graph_builder",
            status="success",
            output={"graph": graph.model_dump()},
            confidence=0.9,
        )


def fake_algebraic(atom, _paper):
    return CheckResult(
        check_id=f"check_alg_{atom.atom_id}",
        atom_id=atom.atom_id,
        kind=CheckKind.ALGEBRAIC_SANITY,
        status=CheckStatus.PASSED,
        summary="mock algebraic pass",
        confidence=0.9,
    )


def fake_citation(atom):
    return CheckResult(
        check_id=f"check_cite_{atom.atom_id}",
        atom_id=atom.atom_id,
        kind=CheckKind.CITATION_CONTEXT,
        status=CheckStatus.NOT_APPLICABLE,
        summary="no citations",
        confidence=0.8,
    )


async def fake_numeric(atom):
    return CheckResult(
        check_id=f"check_num_{atom.atom_id}",
        atom_id=atom.atom_id,
        kind=CheckKind.NUMERIC_COUNTEREXAMPLE_PROBE,
        status=CheckStatus.NO_COUNTEREXAMPLE_FOUND,
        summary="mock numeric pass",
        confidence=0.7,
    )


class FakeChallengeAgent:
    async def run(self, context):
        challenge = Challenge(
            challenge_id=f"ch_{context.atom.atom_id}_001",
            atom_id=context.atom.atom_id,
            attacker_agent="fake_challenge",
            challenge_type=ChallengeType.PROOF_GAP,
            severity=Severity.LOW,
            challenge_text="mock low severity challenge",
            confidence=0.5,
        )
        return AgentResult(
            agent_id="challenge_agent",
            status="success",
            output={"challenges": [challenge.model_dump()]},
            confidence=0.8,
        )


class FakeDefenseAgent:
    async def run(self, context):
        rebuttals = [
            Rebuttal(
                rebuttal_id=f"rb_{challenge.challenge_id}",
                challenge_id=challenge.challenge_id,
                atom_id=context.atom.atom_id,
                defender_agent="fake_defense",
                response_type=RebuttalType.RESOLVES,
                rebuttal_text="mock rebuttal resolves the challenge",
                confidence=0.8,
            ).model_dump()
            for challenge in context.challenges
        ]
        return AgentResult(
            agent_id="defense_agent",
            status="success",
            output={"rebuttals": rebuttals},
            confidence=0.8,
        )


async def test_review_route_source_storage() -> None:
    original_fetch = review_api.fetch_arxiv_source
    original_run = review_api._orchestrator.run

    async def fake_fetch(ref, dest_dir):
        root = Path(dest_dir)
        archive_path = root / "source.tar.gz"
        main_tex_path = root / "source" / "main.tex"
        archive_path.write_bytes(b"fake")
        main_tex_path.parent.mkdir(parents=True, exist_ok=True)
        main_tex_path.write_text(SAMPLE_TEX, encoding="utf-8")
        return SimpleNamespace(
            source_url=ref.source_url,
            archive_path=str(archive_path),
            extract_dir=str(main_tex_path.parent),
            main_tex_path=str(main_tex_path),
            tex_text=SAMPLE_TEX,
            tex_paths=[str(main_tex_path)],
        )

    async def fake_run(_job_id):
        return None

    review_api.fetch_arxiv_source = fake_fetch
    review_api._orchestrator.run = fake_run
    try:
        response = await review_api._submit_arxiv_review("https://arxiv.org/pdf/1706.03762")
    finally:
        review_api.fetch_arxiv_source = original_fetch
        review_api._orchestrator.run = original_run

    _assert(response["parser_kind"] == "tex", "route did not queue tex parser")
    _assert(
        response["source_url"] == "https://arxiv.org/e-print/1706.03762",
        "route did not normalize to arXiv e-print source URL",
    )
    job = job_store.get(response["job_id"])
    _assert(job is not None, "job missing")
    _assert(job["arxiv_id"] == "1706.03762", "wrong arxiv id")
    _assert(Path(job["tex_path"]).is_file(), "assembled tex was not written")


async def test_report_routes_require_completed_job() -> None:
    try:
        await review_api.get_report("missing-review-job")
    except HTTPException as exc:
        _assert(exc.status_code == 404, f"expected 404, got {exc.status_code}")
    else:
        raise AssertionError("missing report job did not raise")

    job_id = job_store.create_job(mode="review")
    try:
        await review_api.get_report(job_id)
    except HTTPException as exc:
        _assert(exc.status_code == 202, f"expected 202, got {exc.status_code}")
    else:
        raise AssertionError("incomplete report job did not raise")

    report = {"markdown_report": "# Review Report"}
    job_store.update(job_id, status="complete", report=report)
    _assert(await review_api.get_report(job_id) == report, "completed report mismatch")
    _assert(
        await review_api.get_markdown_report(job_id) == "# Review Report",
        "markdown report mismatch",
    )


async def test_orchestrator_mocked_atom_pipeline() -> None:
    originals = {
        "AtomExtractorAgent": review_orchestrator_module.AtomExtractorAgent,
        "GraphBuilderAgent": review_orchestrator_module.GraphBuilderAgent,
        "run_algebraic_sanity": review_orchestrator_module.run_algebraic_sanity,
        "run_citation_probe": review_orchestrator_module.run_citation_probe,
        "run_numeric_probe": review_orchestrator_module.run_numeric_probe,
        "ChallengeAgent": review_orchestrator_module.ChallengeAgent,
        "DefenseAgent": review_orchestrator_module.DefenseAgent,
    }
    review_orchestrator_module.AtomExtractorAgent = FakeAtomExtractorAgent
    review_orchestrator_module.GraphBuilderAgent = FakeGraphBuilderAgent
    review_orchestrator_module.run_algebraic_sanity = fake_algebraic
    review_orchestrator_module.run_citation_probe = fake_citation
    review_orchestrator_module.run_numeric_probe = fake_numeric
    review_orchestrator_module.ChallengeAgent = FakeChallengeAgent
    review_orchestrator_module.DefenseAgent = FakeDefenseAgent

    with tempfile.TemporaryDirectory() as tmp:
        tex_path = Path(tmp) / "assembled.tex"
        tex_path.write_text(SAMPLE_TEX, encoding="utf-8")
        job_id = job_store.create_job(
            mode="review",
            parser_kind="tex",
            tex_path=str(tex_path),
            arxiv_id="1706.03762",
        )
        event_bus.create_channel(job_id)
        try:
            await ReviewOrchestrator().run(job_id)
        finally:
            for name, value in originals.items():
                setattr(review_orchestrator_module, name, value)

    job = job_store.get(job_id)
    _assert(job["status"] == "complete", f"job did not complete: {job}")
    _assert(job["parsed_paper"]["title"] == "Mock Source Paper", "parsed paper missing")
    _assert(job["total_atoms"] == 2, "wrong atom count")
    _assert(job["graph"]["roots"] == ["atom_001"], "wrong graph roots")
    _assert(len(job["graph_snapshot"]["edges"]) == 1, "bad graph snapshot")
    _assert(len(job["verdicts"]) == 2, "verdicts missing")
    _assert(job["report"]["summary"]["total_atoms"] == 2, "report summary wrong")
    status = await review_api.get_status(job_id)
    _assert(status["completed_atoms"] == 2, "status completed_atoms wrong")
    atom_detail = await review_api.get_atom(job_id, "atom_001")
    _assert(atom_detail["atom"]["atom_id"] == "atom_001", "atom detail wrong")

    event_types = [event.event_type.value for event in event_bus._history[job_id]]
    for expected in (
        "atom_created",
        "check_complete",
        "challenge_issued",
        "rebuttal_issued",
        "verdict_emitted",
        "job_complete",
    ):
        _assert(expected in event_types, f"{expected} event missing")


async def main_async() -> None:
    await test_review_route_source_storage()
    await test_report_routes_require_completed_job()
    await test_orchestrator_mocked_atom_pipeline()


def main() -> int:
    asyncio.run(main_async())
    print("mocked ResearchAtom review flow tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
