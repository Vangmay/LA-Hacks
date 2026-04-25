"""Mocked backend flow test for arXiv TeX review submission and orchestration.

This test makes no network calls and no OpenAI calls.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

import api.review as review_api  # noqa: E402
import core.orchestrators.review as review_orchestrator_module  # noqa: E402
from agents.base import AgentResult  # noqa: E402
from core.event_bus import event_bus  # noqa: E402
from core.job_store import job_store  # noqa: E402
from core.orchestrators.review import ReviewOrchestrator  # noqa: E402
from models import ClaimUnit  # noqa: E402


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


class FakeClaimExtractorAgent:
    async def run(self, _context):
        claims = [
            ClaimUnit(
                claim_id="claim_001",
                text="For every $x \\in \\mathbb{R}$, $x^2 \\ge 0$.",
                claim_type="theorem",
                section="Foundations",
                equations=["x^2 \\ge 0"],
                citations=[],
                dependencies=[],
            ).model_dump(),
            ClaimUnit(
                claim_id="claim_002",
                text="The minimum value is attained at $x=0$.",
                claim_type="proposition",
                section="Consequence",
                equations=[],
                citations=[],
                dependencies=[],
            ).model_dump(),
        ]
        return AgentResult(
            agent_id="claim_extractor",
            claim_id=None,
            status="success",
            output={"claims": claims},
            confidence=0.9,
        )


class FakeDAGBuilderAgent:
    async def run(self, context):
        claims = context.extra["claims"]
        claims[1]["dependencies"] = ["claim_001"]
        return AgentResult(
            agent_id="dag_builder",
            claim_id=None,
            status="success",
            output={
                "edges": [{"from": "claim_002", "to": "claim_001"}],
                "adjacency": {"claim_001": [], "claim_002": ["claim_001"]},
                "roots": ["claim_001"],
                "topological_order": ["claim_001", "claim_002"],
            },
            confidence=0.9,
        )


class FakeSymbolicVerifierAgent:
    agent_id = "symbolic_verifier"

    async def run(self, context):
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=context.claim.claim_id,
            status="success",
            output={
                "tier": "symbolic",
                "status": "passed",
                "evidence": "mock symbolic pass",
                "confidence": 0.9,
            },
            confidence=0.9,
        )


class FakeNumericAdversaryAgent:
    agent_id = "numeric_adversary"

    async def run(self, context):
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=context.claim.claim_id,
            status="inconclusive",
            output={
                "tier": "numeric",
                "status": "inconclusive",
                "evidence": "mock numeric skip",
                "confidence": 0.3,
            },
            confidence=0.3,
        )


class FakeAttackerAgent:
    agent_id = "attacker"

    async def run(self, context):
        claim_id = context.claim.claim_id
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={
                "challenges": [
                    {
                        "challenge_id": f"ch_{claim_id}_001",
                        "claim_id": claim_id,
                        "attacker_agent": "attacker",
                        "challenge_text": "mock challenge",
                        "supporting_evidence": ["mock evidence"],
                    }
                ]
            },
            confidence=0.8,
        )


class FakeDefenderAgent:
    agent_id = "defender"

    async def run(self, context):
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=context.claim.claim_id,
            status="success",
            output={
                "rebuttals": [
                    {
                        "challenge_id": challenge["challenge_id"],
                        "rebuttal_text": "mock rebuttal",
                        "supporting_evidence": ["mock support"],
                    }
                    for challenge in context.extra["challenges"]
                ]
            },
            confidence=0.7,
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
    job = job_store.get(response["job_id"])
    _assert(job is not None, "job missing")
    _assert(job["arxiv_id"] == "1706.03762", "wrong arxiv id")
    _assert(Path(job["tex_path"]).is_file(), "assembled tex was not written")


async def test_orchestrator_mocked_prompt_2_4() -> None:
    originals = {
        "ClaimExtractorAgent": review_orchestrator_module.ClaimExtractorAgent,
        "DAGBuilderAgent": review_orchestrator_module.DAGBuilderAgent,
        "SymbolicVerifierAgent": review_orchestrator_module.SymbolicVerifierAgent,
        "NumericAdversaryAgent": review_orchestrator_module.NumericAdversaryAgent,
        "AttackerAgent": review_orchestrator_module.AttackerAgent,
        "DefenderAgent": review_orchestrator_module.DefenderAgent,
    }
    review_orchestrator_module.ClaimExtractorAgent = FakeClaimExtractorAgent
    review_orchestrator_module.DAGBuilderAgent = FakeDAGBuilderAgent
    review_orchestrator_module.SymbolicVerifierAgent = FakeSymbolicVerifierAgent
    review_orchestrator_module.NumericAdversaryAgent = FakeNumericAdversaryAgent
    review_orchestrator_module.AttackerAgent = FakeAttackerAgent
    review_orchestrator_module.DefenderAgent = FakeDefenderAgent

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
    _assert(job["parser_output"]["title"] == "Mock Source Paper", "parser output missing")
    _assert(job["total_claims"] == 2, "wrong claim count")
    _assert(job["dag"]["roots"] == ["claim_001"], "wrong roots")
    _assert(job["dag_snapshot"]["edges"] == [{"from": "claim_002", "to": "claim_001"}], "bad dag")
    _assert(len(job["review_results"]["claim_001"]["verification_results"]) == 2, "verifiers missing")
    _assert(job["review_results"]["claim_001"]["challenges"], "challenge missing")
    _assert(job["review_results"]["claim_001"]["rebuttals"], "rebuttal missing")
    event_types = [event.event_type.value for event in event_bus._history[job_id]]
    _assert("node_created" in event_types, "node event missing")
    _assert("tier_complete" in event_types, "tier event missing")
    _assert("challenge_issued" in event_types, "challenge event missing")
    _assert("rebuttal_issued" in event_types, "rebuttal event missing")
    _assert("review_complete" in event_types, "complete event missing")


async def main_async() -> None:
    await test_review_route_source_storage()
    await test_orchestrator_mocked_prompt_2_4()


def main() -> int:
    asyncio.run(main_async())
    print("mocked review TeX flow tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
