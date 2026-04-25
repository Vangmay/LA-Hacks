import asyncio
import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from agents.attacker import AttackerAgent
from agents.base import AgentContext, AgentResult
from agents.claim_extractor import ClaimExtractorAgent
from agents.dag_builder import DAGBuilderAgent
from agents.defender import DefenderAgent
from agents.numeric_adversary import NumericAdversaryAgent
from agents.symbolic_verifier import SymbolicVerifierAgent
from agents.tex_parser import TexParserAgent
from config import settings
from core.event_bus import event_bus
from core.job_store import job_store
from models import ClaimUnit, DAGEvent, DAGEventType

logger = logging.getLogger(__name__)


class ReviewOrchestrator:
    """Run the TeX-first review pipeline through Prompt 2.4.

    Runtime path:
      arXiv source TeX -> TexParserAgent -> ClaimExtractorAgent -> DAGBuilderAgent
      -> SymbolicVerifierAgent + NumericAdversaryAgent -> AttackerAgent
      -> DefenderAgent.

    Verdict aggregation/cascade/report finalization belong to Prompt 2.5+ and are
    represented here only as an interim report so API consumers can inspect the
    completed Prompt 2.4 artifacts.
    """

    async def run(self, job_id: str, **_kwargs) -> None:
        try:
            job = job_store.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            if job.get("parser_kind") != "tex":
                raise ValueError("review pipeline only supports parser_kind='tex'")

            job_store.set_status(job_id, "processing")

            parser_output = await self._run_parser(job_id, job)
            claims = await self._run_claim_extractor(job_id, parser_output)
            dag_output = await self._run_dag_builder(job_id, claims)

            dag_snapshot = _dag_snapshot(claims, dag_output.get("edges", []))
            job_store.update(
                job_id,
                parser_output=parser_output,
                claims=claims,
                dag={
                    "edges": dag_output.get("edges", []),
                    "adjacency": dag_output.get("adjacency", {}),
                    "roots": dag_output.get("roots", []),
                    "topological_order": dag_output.get("topological_order", []),
                },
                dag_snapshot=dag_snapshot,
                total_claims=len(claims),
                completed_claims=0,
            )

            for claim in claims:
                await _publish(
                    job_id,
                    DAGEventType.NODE_CREATED,
                    claim.get("claim_id"),
                    {
                        "claim": claim,
                        "dependencies": claim.get("dependencies", []),
                    },
                )

            review_results = await self._run_prompt_2_1_to_2_4(job_id, claims)
            report = _interim_report(job, parser_output, claims, dag_output, review_results)

            job_store.update(
                job_id,
                status="complete",
                completed_claims=len(claims),
                review_results=review_results,
                report=report,
            )
            await _publish(
                job_id,
                DAGEventType.REVIEW_COMPLETE,
                None,
                {"total_claims": len(claims), "stage": "prompt_2_4_complete"},
            )
        except Exception as e:
            logger.exception("Review orchestrator failed for %s", job_id)
            job_store.update(job_id, status="error", error=str(e))

    async def _run_parser(self, job_id: str, job: dict) -> Dict[str, Any]:
        tex_path = job.get("tex_path")
        result = await TexParserAgent().run(
            AgentContext(job_id=job_id, extra={"tex_path": tex_path})
        )
        if result.status != "success":
            raise RuntimeError(f"TeX parser failed: {result.error}")
        return result.output

    async def _run_claim_extractor(
        self,
        job_id: str,
        parser_output: Dict[str, Any],
    ) -> List[dict]:
        result = await ClaimExtractorAgent().run(
            AgentContext(job_id=job_id, extra={"parser_output": parser_output})
        )
        claims = result.output.get("claims", [])
        if result.status == "error":
            raise RuntimeError(f"claim extraction failed: {result.error}")
        if not claims:
            raise RuntimeError("claim extraction produced no claims")
        return claims

    async def _run_dag_builder(self, job_id: str, claims: List[dict]) -> Dict[str, Any]:
        result = await DAGBuilderAgent().run(
            AgentContext(job_id=job_id, extra={"claims": claims})
        )
        if result.status == "error":
            raise RuntimeError(f"DAG builder failed: {result.error}")
        return result.output

    async def _run_prompt_2_1_to_2_4(
        self,
        job_id: str,
        claims: List[dict],
    ) -> Dict[str, dict]:
        symbolic = SymbolicVerifierAgent()
        numeric = NumericAdversaryAgent()
        attacker = AttackerAgent()
        defender = DefenderAgent()
        semaphore = asyncio.Semaphore(max(1, settings.max_parallel_claims))
        completed = 0
        completed_lock = asyncio.Lock()
        review_results: Dict[str, dict] = {}

        async def process_claim(claim_dict: dict) -> None:
            nonlocal completed
            claim = ClaimUnit.model_validate(claim_dict)
            async with semaphore:
                verification_results = await self._run_verifiers(
                    job_id,
                    claim,
                    [symbolic, numeric],
                )
                challenges = await self._run_attacker(
                    job_id,
                    claim,
                    attacker,
                    verification_results,
                )
                rebuttals = await self._run_defender(job_id, claim, defender, challenges)
                review_results[claim.claim_id] = {
                    "claim": claim.model_dump(),
                    "verification_results": verification_results,
                    "challenges": challenges,
                    "rebuttals": rebuttals,
                }
                async with completed_lock:
                    completed += 1
                    job_store.update(job_id, completed_claims=completed)

        results = await asyncio.gather(
            *(process_claim(claim) for claim in claims),
            return_exceptions=True,
        )
        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors:
            job_store.update(job_id, claim_errors=errors)
        return review_results

    async def _run_verifiers(
        self,
        job_id: str,
        claim: ClaimUnit,
        verifiers: List[Any],
    ) -> List[dict]:
        ctx = AgentContext(job_id=job_id, claim=claim)
        results = await asyncio.gather(
            *(verifier.run(ctx) for verifier in verifiers),
            return_exceptions=True,
        )

        outputs: List[dict] = []
        for result in results:
            if isinstance(result, Exception):
                output = {
                    "tier": "unknown",
                    "status": "inconclusive",
                    "evidence": str(result),
                    "confidence": 0.0,
                }
            else:
                output = result.output
            outputs.append(output)
            await _publish(
                job_id,
                DAGEventType.TIER_COMPLETE,
                claim.claim_id,
                output,
            )
        return outputs

    async def _run_attacker(
        self,
        job_id: str,
        claim: ClaimUnit,
        attacker: AttackerAgent,
        verification_results: List[dict],
    ) -> List[dict]:
        result = await _run_agent_no_raise(
            attacker.run(
                AgentContext(
                    job_id=job_id,
                    claim=claim,
                    extra={"verification_results": verification_results},
                )
            ),
            attacker.agent_id,
            claim.claim_id,
        )
        challenges = result.output.get("challenges", [])
        for challenge in challenges:
            await _publish(
                job_id,
                DAGEventType.CHALLENGE_ISSUED,
                claim.claim_id,
                challenge,
            )
        return challenges

    async def _run_defender(
        self,
        job_id: str,
        claim: ClaimUnit,
        defender: DefenderAgent,
        challenges: List[dict],
    ) -> List[dict]:
        result = await _run_agent_no_raise(
            defender.run(
                AgentContext(
                    job_id=job_id,
                    claim=claim,
                    extra={"challenges": challenges},
                )
            ),
            defender.agent_id,
            claim.claim_id,
        )
        rebuttals = result.output.get("rebuttals", [])
        for rebuttal in rebuttals:
            await _publish(
                job_id,
                DAGEventType.REBUTTAL_ISSUED,
                claim.claim_id,
                rebuttal,
            )
        return rebuttals


async def _run_agent_no_raise(
    awaitable,
    agent_id: str,
    claim_id: str,
) -> AgentResult:
    try:
        return await awaitable
    except Exception as e:
        logger.exception("%s raised for %s", agent_id, claim_id)
        return AgentResult(
            agent_id=agent_id,
            claim_id=claim_id,
            status="error",
            output={},
            confidence=0.0,
            error=str(e),
        )


async def _publish(
    job_id: str,
    event_type: DAGEventType,
    claim_id: str | None,
    payload: dict,
) -> None:
    await event_bus.publish(
        job_id,
        DAGEvent(
            event_id=str(uuid.uuid4()),
            job_id=job_id,
            event_type=event_type,
            claim_id=claim_id,
            payload=payload,
            timestamp=datetime.utcnow(),
        ),
    )


def _dag_snapshot(claims: List[dict], edges: List[dict]) -> dict:
    return {
        "nodes": [
            {
                "id": claim.get("claim_id"),
                "claim_type": claim.get("claim_type"),
                "section": claim.get("section"),
                "text": claim.get("text"),
                "dependencies": claim.get("dependencies", []),
                "status": "pending",
            }
            for claim in claims
        ],
        "edges": edges,
    }


def _interim_report(
    job: dict,
    parser_output: Dict[str, Any],
    claims: List[dict],
    dag_output: Dict[str, Any],
    review_results: Dict[str, dict],
) -> dict:
    paper_hash = _paper_hash(job.get("tex_path"))
    return {
        "paper_title": parser_output.get("title") or job.get("arxiv_id") or "Untitled",
        "paper_hash": paper_hash,
        "reviewed_at": datetime.utcnow().isoformat(),
        "stage": "prompt_2_4_complete",
        "total_claims": len(claims),
        "supported": 0,
        "contested": 0,
        "refuted": 0,
        "cascaded_failures": 0,
        "verdicts": [],
        "review_results": review_results,
        "dag_summary": {
            "nodes": [claim.get("claim_id") for claim in claims],
            "edges": dag_output.get("edges", []),
            "roots": dag_output.get("roots", []),
            "topological_order": dag_output.get("topological_order", []),
        },
        "markdown_report": (
            "# Prompt 2.4 Interim Review\n\n"
            "Verification tiers, attacker challenges, and defender rebuttals have "
            "completed. Verdict aggregation is handled by Prompt 2.5."
        ),
    }


def _paper_hash(path: str | None) -> str:
    if not path:
        return "0" * 16
    try:
        return hashlib.md5(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return "0" * 16
