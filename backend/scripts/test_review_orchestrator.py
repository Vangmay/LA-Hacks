"""Smoke test for ReviewOrchestrator + ReportAgent.

Builds a small 3-claim DAG, runs the orchestrator end to end, and asserts:
  - all NODE_CREATED, TIER_COMPLETE, VERDICT_EMITTED, REVIEW_COMPLETE events fire
  - cascade fires when a parent claim is REFUTED
  - final ReviewReport is stored and has correct counts

Usage (from backend/):
    python scripts/test_review_orchestrator.py            # live OpenAI calls
    python scripts/test_review_orchestrator.py --mock     # offline, all LLM agents stubbed

Live mode requires OPENAI_API_KEY in backend/.env.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import dotenv

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

dotenv.load_dotenv(BACKEND / ".env")

from agents.base import AgentResult
from config import settings
from core.dag import DAG
from core.event_bus import event_bus
from core.job_store import job_store
from core.orchestrators.review import ReviewOrchestrator
from models import ClaimUnit, DAGEventType


CLAIMS = [
    ClaimUnit(
        claim_id="c1",
        text="Self-attention has O(n^2) time and memory complexity per layer.",
        claim_type="proposition",
        section="3.2",
        equations=["T(n) = O(n^2)"],
        citations=[],
        dependencies=[],
    ),
    ClaimUnit(
        claim_id="c2",
        text="Therefore self-attention scales worse than recurrent layers for very long sequences.",
        claim_type="theorem",
        section="3.2",
        equations=[],
        citations=[],
        dependencies=["c1"],
    ),
    ClaimUnit(
        claim_id="c3",
        text="Hence Transformer training is impractical for sequences of length > 10000 without modification.",
        claim_type="corollary",
        section="3.2",
        equations=[],
        citations=[],
        dependencies=["c2"],
    ),
]


def _build_dag() -> DAG:
    dag = DAG()
    for c in CLAIMS:
        dag.add_node(c.claim_id)
    dag.add_edge("c2", "c1")
    dag.add_edge("c3", "c2")
    return dag


async def _fake_attacker(self, ctx) -> AgentResult:
    return AgentResult(
        agent_id="attacker",
        claim_id=ctx.claim.claim_id,
        status="success",
        output={
            "challenges": [
                {
                    "challenge_id": f"ch_{ctx.claim.claim_id}_1",
                    "claim_id": ctx.claim.claim_id,
                    "attacker_agent": "attacker",
                    "challenge_text": "Hidden constant factor is large.",
                    "supporting_evidence": [],
                }
            ]
        },
        confidence=0.7,
    )


async def _fake_defender(self, ctx) -> AgentResult:
    challenges = (ctx.extra or {}).get("challenges", [])
    return AgentResult(
        agent_id="defender",
        claim_id=ctx.claim.claim_id,
        status="success",
        output={
            "rebuttals": [
                {
                    "challenge_id": ch["challenge_id"],
                    "rebuttal_text": "Bound is asymptotic and per-layer.",
                    "supporting_evidence": [],
                }
                for ch in challenges
            ]
        },
        confidence=0.7,
    )


async def _fake_aggregator(self, ctx) -> AgentResult:
    """Mark c1 REFUTED so cascade kicks in for c2 and c3."""
    cid = ctx.claim.claim_id
    if cid == "c1":
        verdict, conf = "REFUTED", 0.9
    else:
        verdict, conf = "SUPPORTED", 0.8
    return AgentResult(
        agent_id="verdict_aggregator",
        claim_id=cid,
        status="success",
        output={
            "claim_id": cid,
            "verdict": verdict,
            "confidence": conf,
            "is_cascaded": False,
            "cascade_source": None,
            "challenges": (ctx.extra or {}).get("challenges", []),
            "rebuttals": (ctx.extra or {}).get("rebuttals", []),
            "verification_results": (ctx.extra or {}).get("verification_results", []),
        },
        confidence=conf,
    )


def _make_report_mock_client() -> MagicMock:
    fake = MagicMock()
    fake.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=(
                            "# Mock Review Report\n\n"
                            "## Executive Summary\nMocked output for testing.\n"
                        )
                    )
                )
            ]
        )
    )
    return fake


async def run(use_mock: bool) -> int:
    if not use_mock and not settings.openai_api_key:
        print("OPENAI_API_KEY not set. Add it to backend/.env or run with --mock.")
        return 1

    print(
        f"=== ReviewOrchestrator ({'mocked' if use_mock else f'live, model={settings.openai_model}'}) ==="
    )
    print(f"  claims: {len(CLAIMS)}, dag edges: c2->c1, c3->c2")

    job_id = job_store.create_job(mode="review", filename="smoke.pdf")
    event_bus.create_channel(job_id)
    dag = _build_dag()

    orch = ReviewOrchestrator()

    if use_mock:
        # Patch all five swarm agents + aggregator + report's LLM call.
        orch._report._client = _make_report_mock_client()
        ctx_mgrs = [
            patch("agents.attacker.AttackerAgent.run", new=_fake_attacker),
            patch("agents.defender.DefenderAgent.run", new=_fake_defender),
            patch(
                "agents.verdict_aggregator.VerdictAggregatorAgent.run",
                new=_fake_aggregator,
            ),
        ]
        for cm in ctx_mgrs:
            cm.start()
        try:
            await orch.run(
                job_id,
                claims=CLAIMS,
                dag=dag,
                paper_metadata={"title": "Attention Is All You Need", "hash": "abc123"},
            )
        finally:
            for cm in ctx_mgrs:
                cm.stop()
    else:
        await orch.run(
            job_id,
            claims=CLAIMS,
            dag=dag,
            paper_metadata={"title": "Attention Is All You Need", "hash": "abc123"},
        )

    job = job_store.get(job_id) or {}
    events = list(event_bus._history.get(job_id, []))
    event_types = [e.event_type for e in events]
    counts = {t.value: event_types.count(t) for t in DAGEventType}

    print(f"\n  status:           {job.get('status')}")
    print(f"  completed_claims: {job.get('completed_claims')}/{job.get('total_claims')}")
    print(f"  total events:     {len(events)}")
    for k, v in counts.items():
        if v:
            print(f"    {k}: {v}")

    report = job.get("report") or {}
    print("\n  report:")
    print(f"    paper_title:       {report.get('paper_title')}")
    print(f"    total_claims:      {report.get('total_claims')}")
    print(f"    supported:         {report.get('supported')}")
    print(f"    contested:         {report.get('contested')}")
    print(f"    refuted:           {report.get('refuted')}")
    print(f"    cascaded_failures: {report.get('cascaded_failures')}")
    md = report.get("markdown_report") or ""
    print(f"\n  markdown ({len(md)} chars, first 200):")
    print("    " + md.replace("\n", "\n    ")[:200])

    failures = []

    if job.get("status") != "complete":
        failures.append(f"status != complete (got {job.get('status')})")
    if job.get("completed_claims") != len(CLAIMS):
        failures.append(
            f"completed_claims {job.get('completed_claims')} != {len(CLAIMS)}"
        )

    expect_node_created = len(CLAIMS)
    expect_tier_complete = len(CLAIMS) * 3
    expect_verdict_emitted = len(CLAIMS)
    if counts["node_created"] != expect_node_created:
        failures.append(
            f"node_created {counts['node_created']} != {expect_node_created}"
        )
    if counts["tier_complete"] != expect_tier_complete:
        failures.append(
            f"tier_complete {counts['tier_complete']} != {expect_tier_complete}"
        )
    if counts["verdict_emitted"] != expect_verdict_emitted:
        failures.append(
            f"verdict_emitted {counts['verdict_emitted']} != {expect_verdict_emitted}"
        )
    if counts["review_complete"] != 1:
        failures.append(f"review_complete {counts['review_complete']} != 1")

    if use_mock:
        # c1 is REFUTED, so c2 and c3 should cascade.
        if counts["cascade_triggered"] != 2:
            failures.append(
                f"cascade_triggered {counts['cascade_triggered']} != 2"
            )
        if report.get("refuted") != 3:
            failures.append(f"refuted {report.get('refuted')} != 3")
        if report.get("cascaded_failures") != 2:
            failures.append(
                f"cascaded_failures {report.get('cascaded_failures')} != 2"
            )

    if report.get("total_claims") != len(CLAIMS):
        failures.append(
            f"report.total_claims {report.get('total_claims')} != {len(CLAIMS)}"
        )
    if not md.strip():
        failures.append("markdown_report is empty")

    if failures:
        print("\nFAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nOK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Stub all LLM agents (no network, no API key needed).",
    )
    args = parser.parse_args()
    return asyncio.run(run(use_mock=args.mock))


if __name__ == "__main__":
    sys.exit(main())
