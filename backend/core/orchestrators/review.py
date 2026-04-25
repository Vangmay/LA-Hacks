import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from agents.attacker import AttackerAgent
from agents.base import AgentContext, AgentResult
from agents.cascade import CascadeAgent
from agents.defender import DefenderAgent
from agents.numeric_adversary import NumericAdversaryAgent
from agents.rag_retrieval import RAGRetrievalAgent
from agents.report_agent import ReportAgent
from agents.symbolic_verifier import SymbolicVerifierAgent
from agents.verdict_aggregator import VerdictAggregatorAgent
from config import settings
from core.dag import DAG
from core.event_bus import event_bus
from core.job_store import job_store
from models import ClaimUnit, ClaimVerdict, DAGEvent, DAGEventType

logger = logging.getLogger(__name__)


class ReviewOrchestrator:
    """Top-level controller for Review Mode.

    Pipeline:
      1. Emit NODE_CREATED for every claim.
      2. Per claim: gather verifier + adversary + retrieval + attacker + defender,
         then aggregate into a ClaimVerdict. Respect DAG dependencies.
      3. Run CascadeAgent over the verdicts to propagate REFUTED state.
      4. Run ReportAgent to produce the final ReviewReport.
      5. Persist into job_store and emit REVIEW_COMPLETE.
    """

    def __init__(self) -> None:
        self._symbolic = SymbolicVerifierAgent()
        self._numeric = NumericAdversaryAgent()
        self._rag = RAGRetrievalAgent()
        self._attacker = AttackerAgent()
        self._defender = DefenderAgent()
        self._aggregator = VerdictAggregatorAgent()
        self._cascade = CascadeAgent()
        self._report = ReportAgent()

    async def run(
        self,
        job_id: str,
        claims: Optional[List[ClaimUnit]] = None,
        dag: Optional[DAG] = None,
        paper_metadata: Optional[dict] = None,
        **_: dict,
    ) -> None:
        try:
            job_store.set_status(job_id, "processing")

            # Pull from job_store if not passed explicitly.
            job = job_store.get(job_id) or {}
            claims = claims if claims is not None else job.get("claims") or []
            dag = dag if dag is not None else job.get("dag") or DAG()
            paper_metadata = paper_metadata if paper_metadata is not None else (
                job.get("paper_metadata") or {}
            )

            claim_map: Dict[str, ClaimUnit] = {c.claim_id: c for c in claims}
            job_store.update(job_id, total_claims=len(claims), completed_claims=0)

            # 1. NODE_CREATED for every claim.
            for claim in claims:
                await self._emit(
                    job_id,
                    DAGEventType.NODE_CREATED,
                    claim_id=claim.claim_id,
                    payload={
                        "claim_text": claim.text,
                        "claim_type": claim.claim_type,
                        "section": claim.section,
                        "dependencies": claim.dependencies,
                    },
                )

            # 2. Per-claim swarms, dependency-aware.
            verdicts: Dict[str, ClaimVerdict] = {}
            tasks: Dict[str, asyncio.Task] = {}
            semaphore = asyncio.Semaphore(max(1, settings.max_parallel_claims))

            async def process(claim: ClaimUnit) -> Optional[ClaimVerdict]:
                # Wait for all upstream dependency tasks to settle first.
                deps = list(dag.edges.get(claim.claim_id, set()))
                dep_tasks = [tasks[d] for d in deps if d in tasks]
                if dep_tasks:
                    await asyncio.gather(*dep_tasks, return_exceptions=True)
                async with semaphore:
                    verdict = await self._run_claim_swarm(job_id, claim)
                if verdict is not None:
                    verdicts[claim.claim_id] = verdict
                    completed = (job_store.get(job_id) or {}).get("completed_claims", 0) + 1
                    job_store.update(job_id, completed_claims=completed)
                return verdict

            # Schedule in topological order so dep-task lookups always resolve.
            try:
                order = dag.topological_sort()
            except ValueError:
                logger.warning("review_orchestrator: DAG has a cycle, falling back to claim order")
                order = [c.claim_id for c in claims]

            for cid in order:
                if cid in claim_map and cid not in tasks:
                    tasks[cid] = asyncio.create_task(process(claim_map[cid]))
            # Catch any claim not present in DAG.
            for claim in claims:
                if claim.claim_id not in tasks:
                    tasks[claim.claim_id] = asyncio.create_task(process(claim))

            if tasks:
                await asyncio.gather(*tasks.values(), return_exceptions=True)

            # 3. Cascade.
            verdicts = await self._run_cascade(job_id, verdicts, dag)

            # 4. Report.
            report_result = await self._report.run(AgentContext(
                job_id=job_id,
                extra={
                    "verdicts": {cid: v.model_dump(mode="json") for cid, v in verdicts.items()},
                    "paper_metadata": paper_metadata,
                    "dag_summary": dag.to_dict(),
                },
            ))

            report_dict = report_result.output.get("report", {})
            markdown = report_result.output.get("markdown", "")

            # 5. Persist + REVIEW_COMPLETE.
            job_store.update(
                job_id,
                report=report_dict,
                markdown_report=markdown,
                verdicts={cid: v.model_dump(mode="json") for cid, v in verdicts.items()},
            )
            job_store.set_status(job_id, "complete")

            await self._emit(
                job_id,
                DAGEventType.REVIEW_COMPLETE,
                payload={
                    "total_claims": report_dict.get("total_claims", len(verdicts)),
                    "supported": report_dict.get("supported", 0),
                    "contested": report_dict.get("contested", 0),
                    "refuted": report_dict.get("refuted", 0),
                    "cascaded_failures": report_dict.get("cascaded_failures", 0),
                },
            )

        except Exception as e:
            logger.exception("Review orchestrator failed")
            job_store.update(job_id, status="error", error=str(e))

    async def _run_claim_swarm(
        self, job_id: str, claim: ClaimUnit
    ) -> Optional[ClaimVerdict]:
        ctx = AgentContext(job_id=job_id, claim=claim, extra={})

        # All five swarm agents run in parallel for the claim.
        gathered = await asyncio.gather(
            self._symbolic.run(ctx),
            self._numeric.run(ctx),
            self._rag.run(ctx),
            self._attacker.run(ctx),
            self._defender.run(ctx),
            return_exceptions=True,
        )
        sym_res, num_res, rag_res, atk_res, def_res = gathered

        verification_results: List[dict] = []
        for tier_label, res in (
            ("symbolic", sym_res),
            ("numeric", num_res),
            ("semantic", rag_res),
        ):
            tier_output = self._safe_output(res, fallback={
                "tier": tier_label,
                "status": "inconclusive",
                "evidence": _exc_msg(res),
                "confidence": 0.0,
            })
            verification_results.append(tier_output)
            await self._emit(
                job_id,
                DAGEventType.TIER_COMPLETE,
                claim_id=claim.claim_id,
                payload={
                    "tier": tier_output.get("tier", tier_label),
                    "status": tier_output.get("status", "inconclusive"),
                    "confidence": tier_output.get("confidence", 0.0),
                    "evidence": tier_output.get("evidence", ""),
                },
            )

        atk_output = self._safe_output(res=atk_res, fallback={"challenges": []})
        challenges = atk_output.get("challenges", []) or []
        for ch in challenges:
            await self._emit(
                job_id,
                DAGEventType.CHALLENGE_ISSUED,
                claim_id=claim.claim_id,
                payload=ch,
            )

        def_output = self._safe_output(res=def_res, fallback={"rebuttals": []})
        rebuttals = def_output.get("rebuttals", []) or []
        for rb in rebuttals:
            await self._emit(
                job_id,
                DAGEventType.REBUTTAL_ISSUED,
                claim_id=claim.claim_id,
                payload=rb,
            )

        # Aggregate.
        agg_ctx = AgentContext(
            job_id=job_id,
            claim=claim,
            extra={
                "verification_results": verification_results,
                "challenges": challenges,
                "rebuttals": rebuttals,
            },
        )
        agg_res = await self._aggregator.run(agg_ctx)
        verdict = self._verdict_from_aggregator(agg_res, claim, verification_results, challenges, rebuttals)

        await self._emit(
            job_id,
            DAGEventType.VERDICT_EMITTED,
            claim_id=claim.claim_id,
            payload={
                "verdict": verdict.verdict,
                "confidence": verdict.confidence,
                "is_cascaded": verdict.is_cascaded,
            },
        )
        return verdict

    def _verdict_from_aggregator(
        self,
        agg_res: AgentResult,
        claim: ClaimUnit,
        verification_results: List[dict],
        challenges: List[dict],
        rebuttals: List[dict],
    ) -> ClaimVerdict:
        out = agg_res.output if agg_res and agg_res.output else {}
        try:
            return ClaimVerdict.model_validate({
                "claim_id": claim.claim_id,
                "verdict": out.get("verdict", "CONTESTED"),
                "confidence": out.get("confidence", 0.5),
                "is_cascaded": out.get("is_cascaded", False),
                "cascade_source": out.get("cascade_source"),
                "challenges": out.get("challenges") or challenges,
                "rebuttals": out.get("rebuttals") or rebuttals,
                "verification_results": out.get("verification_results") or verification_results,
            })
        except Exception as exc:
            logger.warning(
                "review_orchestrator: failed to parse verdict for %s: %s",
                claim.claim_id, exc,
            )
            return ClaimVerdict(
                claim_id=claim.claim_id,
                verdict="CONTESTED",
                confidence=0.5,
                is_cascaded=False,
                cascade_source=None,
                challenges=[],
                rebuttals=[],
                verification_results=[],
            )

    async def _run_cascade(
        self,
        job_id: str,
        verdicts: Dict[str, ClaimVerdict],
        dag: DAG,
    ) -> Dict[str, ClaimVerdict]:
        if not verdicts:
            return verdicts

        ctx = AgentContext(
            job_id=job_id,
            extra={
                "verdicts": {cid: v.model_dump(mode="json") for cid, v in verdicts.items()},
                "dag": dag.to_dict(),
            },
        )
        result = await self._cascade.run(ctx)
        updated = (result.output or {}).get("updated_verdicts") or {}

        # Trust CascadeAgent's output if it produced anything; otherwise
        # apply a local fallback: any descendant of a REFUTED claim becomes
        # cascaded REFUTED.
        if updated:
            merged = dict(verdicts)
            for cid, v in updated.items():
                try:
                    merged[cid] = ClaimVerdict.model_validate(v)
                except Exception as exc:
                    logger.warning("cascade: failed to parse updated verdict %s: %s", cid, exc)
            new_verdicts = merged
        else:
            new_verdicts = self._local_cascade(verdicts, dag)

        for cid, v in new_verdicts.items():
            if v.is_cascaded and (cid not in verdicts or not verdicts[cid].is_cascaded):
                await self._emit(
                    job_id,
                    DAGEventType.CASCADE_TRIGGERED,
                    claim_id=cid,
                    payload={
                        "cascade_source": v.cascade_source,
                        "verdict": v.verdict,
                        "confidence": v.confidence,
                    },
                )
        return new_verdicts

    def _local_cascade(
        self,
        verdicts: Dict[str, ClaimVerdict],
        dag: DAG,
    ) -> Dict[str, ClaimVerdict]:
        merged = {cid: v.model_copy() for cid, v in verdicts.items()}
        for cid, v in verdicts.items():
            if v.verdict != "REFUTED" or v.is_cascaded:
                continue
            for desc in dag.get_descendants(cid):
                if desc not in merged:
                    continue
                d = merged[desc]
                if d.verdict == "REFUTED":
                    continue
                merged[desc] = d.model_copy(update={
                    "verdict": "REFUTED",
                    "is_cascaded": True,
                    "cascade_source": cid,
                    "confidence": min(d.confidence, v.confidence),
                })
        return merged

    async def _emit(
        self,
        job_id: str,
        event_type: DAGEventType,
        claim_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        try:
            await event_bus.publish(job_id, DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=event_type,
                claim_id=claim_id,
                payload=payload or {},
                timestamp=datetime.utcnow(),
            ))
        except Exception as exc:
            logger.warning("review_orchestrator: failed to emit %s: %s", event_type, exc)

    @staticmethod
    def _safe_output(res, fallback: dict) -> dict:
        if isinstance(res, Exception) or res is None:
            return dict(fallback)
        out = getattr(res, "output", None)
        if not isinstance(out, dict):
            return dict(fallback)
        return out


def _exc_msg(res) -> str:
    if isinstance(res, Exception):
        return f"agent raised: {res}"
    return ""
