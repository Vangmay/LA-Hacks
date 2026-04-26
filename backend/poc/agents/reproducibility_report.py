import json
import logging
from typing import Dict, List

from agents.base import AgentContext, AgentResult, BaseAgent
from config import settings
from core.openai_client import build_messages, extract_json, json_response_format, make_async_openai
from models import (
    ExperimentResult,
    GapAnalysisEntry,
    ReproducibilityReport,
    ReproductionStatus,
)

logger = logging.getLogger(__name__)

_STATUS_RANK: Dict[ReproductionStatus, int] = {
    ReproductionStatus.REPRODUCED: 0,
    ReproductionStatus.PARTIAL: 1,
    ReproductionStatus.FAILED: 2,
    ReproductionStatus.PENDING: 3,
}


class ReproducibilityReportAgent(BaseAgent):
    agent_id = "reproducibility_report"

    _client = make_async_openai()

    async def run(self, context: AgentContext) -> AgentResult:
        experiment_results_raw: list = context.extra.get("experiment_results", [])
        poc_specs_raw = context.extra.get("poc_specs", [])
        paper_metadata: dict = context.extra.get("paper_metadata", {})
        session_id: str = context.extra.get("session_id", "unknown")

        spec_map: dict = (
            poc_specs_raw
            if isinstance(poc_specs_raw, dict)
            else {s["claim_id"]: s for s in poc_specs_raw}
        )

        try:
            results = [ExperimentResult.model_validate(r) for r in experiment_results_raw]
        except Exception as exc:
            logger.error("Failed to parse experiment results: %s", exc)
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"report": {}},
                confidence=0.0,
                error=str(exc),
            )

        # Compute per-claim worst status
        results_by_claim: Dict[str, List[ExperimentResult]] = {}
        for r in results:
            results_by_claim.setdefault(r.claim_id, []).append(r)

        claim_statuses: Dict[str, ReproductionStatus] = {
            cid: max(rs, key=lambda r: _STATUS_RANK.get(r.status, 0)).status
            for cid, rs in results_by_claim.items()
        }

        # Summary stats
        total = len(spec_map)
        reproduced = sum(1 for s in claim_statuses.values() if s == ReproductionStatus.REPRODUCED)
        partial = sum(1 for s in claim_statuses.values() if s == ReproductionStatus.PARTIAL)
        failed = sum(1 for s in claim_statuses.values() if s == ReproductionStatus.FAILED)
        rate = reproduced / total if total > 0 else 0.0

        # Gap analysis for non-REPRODUCED claims
        gap_analyses: List[GapAnalysisEntry] = []
        for claim_id, status in claim_statuses.items():
            if status != ReproductionStatus.REPRODUCED:
                spec = spec_map.get(claim_id, {})
                claim_results = results_by_claim.get(claim_id, [])
                gaps = await self._gap_analysis(claim_id, spec, claim_results)
                gap_analyses.extend(gaps)

        # What to try next
        what_to_try_next = await self._what_to_try_next(gap_analyses, claim_statuses)

        # Markdown report
        markdown = await self._gen_markdown(
            session_id, paper_metadata, total, reproduced, partial, failed,
            rate, results, claim_statuses, gap_analyses, what_to_try_next, spec_map,
        )

        report = ReproducibilityReport(
            session_id=session_id,
            paper_title=paper_metadata.get("title", "Unknown Paper"),
            total_testable_claims=total,
            reproduced=reproduced,
            partial=partial,
            failed=failed,
            reproduction_rate=rate,
            results=results,
            gap_analyses=gap_analyses,
            what_to_try_next=what_to_try_next,
            markdown_report=markdown,
        )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"report": report.model_dump()},
            confidence=0.85,
        )

    # ── LLM calls ─────────────────────────────────────────────────────────────

    async def _gap_analysis(
        self,
        claim_id: str,
        spec: dict,
        claim_results: List[ExperimentResult],
    ) -> List[GapAnalysisEntry]:
        criteria_summary = []
        for r in claim_results:
            criterion = next(
                (c for c in spec.get("success_criteria", []) if c["metric_name"] == r.metric_name),
                {},
            )
            criteria_summary.append({
                "metric": r.metric_name,
                "paper_value": criterion.get("paper_reported_value", "unknown"),
                "threshold": criterion.get("numeric_threshold"),
                "achieved": r.achieved_value,
                "delta": r.delta,
                "status": r.status.value,
                "conditions": criterion.get("experimental_conditions", {}),
            })

        system = (
            "A researcher attempted to reproduce this paper's claim but got a different result. "
            "Analyze the likely causes. "
            'Return JSON: {"explanations": [{"explanation": str, "likelihood": "high"|"medium"|"low", '
            '"suggested_fix": str}]} ordered by likelihood descending.'
        )
        user = (
            f"Claim ID: {claim_id}\n"
            f"Claim text: {spec.get('claim_text', spec.get('claim_id', claim_id))}\n\n"
            f"Results summary:\n{json.dumps(criteria_summary, indent=2)}"
        )

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=build_messages(system, user),
                **json_response_format(),
                max_tokens=8000,
            )
            raw = extract_json(response.choices[0].message.content or "{}")
            data = json.loads(raw)
        except Exception as exc:
            logger.warning("Gap analysis LLM call failed for %s: %s", claim_id, exc)
            return []

        entries = []
        for item in data.get("explanations", []):
            likelihood = item.get("likelihood", "low")
            if likelihood not in ("high", "medium", "low"):
                likelihood = "low"
            entries.append(GapAnalysisEntry(
                claim_id=claim_id,
                explanation=item.get("explanation", ""),
                likelihood=likelihood,
                suggested_fix=item.get("suggested_fix", ""),
            ))
        return entries

    async def _what_to_try_next(
        self,
        gap_analyses: List[GapAnalysisEntry],
        claim_statuses: Dict[str, ReproductionStatus],
    ) -> List[str]:
        if not gap_analyses:
            return []

        failed_claims = [
            cid for cid, s in claim_statuses.items()
            if s in (ReproductionStatus.FAILED, ReproductionStatus.PARTIAL)
        ]
        gap_summary = [
            {"claim_id": g.claim_id, "explanation": g.explanation, "fix": g.suggested_fix}
            for g in gap_analyses
            if g.likelihood in ("high", "medium")
        ]

        system = (
            "Given the failed/partial claims and their gap analyses, "
            "suggest the top 3-5 concrete next steps to improve reproduction rate. "
            'Return JSON: {"steps": ["step 1", "step 2", ...]}'
        )
        user = (
            f"Failed/partial claims: {failed_claims}\n\n"
            f"Gap analyses:\n{json.dumps(gap_summary, indent=2)}"
        )

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=build_messages(system, user),
                **json_response_format(),
                max_tokens=8000,
            )
            raw = extract_json(response.choices[0].message.content or "{}")
            data = json.loads(raw)
            return data.get("steps", [])
        except Exception as exc:
            logger.warning("What-to-try-next LLM call failed: %s", exc)
            return []

    async def _gen_markdown(
        self,
        session_id: str,
        paper_metadata: dict,
        total: int,
        reproduced: int,
        partial: int,
        failed: int,
        rate: float,
        results: List[ExperimentResult],
        claim_statuses: Dict[str, ReproductionStatus],
        gap_analyses: List[GapAnalysisEntry],
        what_to_try_next: List[str],
        spec_map: dict,
    ) -> str:
        rows = []
        for claim_id, status in claim_statuses.items():
            spec = spec_map.get(claim_id, {})
            claim_results = [r for r in results if r.claim_id == claim_id]
            for r in claim_results:
                criterion = next(
                    (c for c in spec.get("success_criteria", []) if c["metric_name"] == r.metric_name),
                    {},
                )
                paper_val = criterion.get("paper_reported_value", "N/A")
                delta_str = f"{r.delta:+.4f}" if r.delta is not None else "N/A"
                rows.append(
                    f"| {claim_id} | {r.metric_name} | {paper_val} | {r.achieved_value:.4f} "
                    f"| {delta_str} | {r.status.value} |"
                )

        table_str = "\n".join(rows) if rows else "| — | — | — | — | — | — |"
        gaps_str = "\n".join(
            f"- **{g.claim_id}** ({g.likelihood}): {g.explanation}  \n  _Fix: {g.suggested_fix}_"
            for g in gap_analyses
        )
        next_str = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(what_to_try_next))

        system = (
            "Generate a concise reproducibility report in Markdown. "
            "Use the data provided. Structure: executive summary, results table, gap analysis, what to try next."
        )
        user = (
            f"Session: {session_id}\n"
            f"Paper: {paper_metadata.get('title', 'Unknown')}\n"
            f"Reproduction rate: {rate:.1%} ({reproduced}/{total} reproduced, {partial} partial, {failed} failed)\n\n"
            f"Results table:\n| claim_id | metric | paper_value | your_value | delta | status |\n"
            f"|---|---|---|---|---|---|\n{table_str}\n\n"
            f"Gap analyses:\n{gaps_str or 'None'}\n\n"
            f"What to try next:\n{next_str or 'N/A'}"
        )

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=build_messages(system, user),
                max_tokens=1500,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("Markdown generation LLM call failed: %s", exc)
            return f"# Reproducibility Report\n\nReproduction rate: {rate:.1%}\n"
