import logging
from typing import Dict, List

from agents.base import AgentContext, AgentResult, BaseAgent
from models import ExperimentResult, ReproductionStatus

logger = logging.getLogger(__name__)

_STATUS_RANK: Dict[ReproductionStatus, int] = {
    ReproductionStatus.REPRODUCED: 0,
    ReproductionStatus.PARTIAL: 1,
    ReproductionStatus.FAILED: 2,
    ReproductionStatus.PENDING: 3,
}


class ResultsAnalyzerAgent(BaseAgent):
    agent_id = "results_analyzer"

    async def run(self, context: AgentContext) -> AgentResult:
        results_json = context.extra.get("results_json", {})
        poc_specs_raw = context.extra.get("poc_specs", [])

        spec_map: dict = (
            poc_specs_raw
            if isinstance(poc_specs_raw, dict)
            else {s["claim_id"]: s for s in poc_specs_raw}
        )

        # Accept a single result dict or a list
        results_list: list = (
            [results_json] if isinstance(results_json, dict) else list(results_json)
        )

        all_results: List[ExperimentResult] = []
        claim_statuses: Dict[str, ReproductionStatus] = {}

        for entry in results_list:
            claim_id = entry.get("claim_id", "")
            metrics: dict = entry.get("metrics", {})
            spec = spec_map.get(claim_id)

            if spec is None:
                logger.warning("No PoCSpec found for claim_id=%s — skipping", claim_id)
                continue

            claim_results: List[ExperimentResult] = []
            for criterion in spec.get("success_criteria", []):
                result = self._evaluate_criterion(claim_id, metrics, criterion)
                claim_results.append(result)

            all_results.extend(claim_results)
            claim_statuses[claim_id] = (
                self._worst_status([r.status for r in claim_results])
                if claim_results
                else ReproductionStatus.PENDING
            )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "results": [r.model_dump() for r in all_results],
                "claim_statuses": {k: v.value for k, v in claim_statuses.items()},
            },
            confidence=0.9,
        )

    # ── Criterion evaluation ───────────────────────────────────────────────────

    def _evaluate_criterion(self, claim_id: str, metrics: dict, criterion: dict) -> ExperimentResult:
        metric_name: str = criterion.get("metric_name", "unknown")
        threshold = criterion.get("numeric_threshold")
        tolerance: float = float(criterion.get("tolerance", 0.02))
        comparison: str = criterion.get("comparison", "within_tolerance")

        if metric_name not in metrics:
            return ExperimentResult(
                claim_id=claim_id,
                metric_name=metric_name,
                achieved_value=0.0,
                status=ReproductionStatus.FAILED,
                delta=None,
                error_message="metric not found in results",
            )

        achieved = float(metrics[metric_name])

        if threshold is None:
            return ExperimentResult(
                claim_id=claim_id,
                metric_name=metric_name,
                achieved_value=achieved,
                status=ReproductionStatus.FAILED,
                delta=None,
                error_message="numeric_threshold not available in spec",
            )

        delta = achieved - threshold
        # Absolute tolerance band: relative to the threshold magnitude
        abs_tol = tolerance * abs(threshold) if abs(threshold) > 1e-9 else tolerance

        status = self._classify(comparison, achieved, threshold, abs_tol)
        return ExperimentResult(
            claim_id=claim_id,
            metric_name=metric_name,
            achieved_value=achieved,
            status=status,
            delta=delta,
        )

    def _classify(
        self,
        comparison: str,
        achieved: float,
        threshold: float,
        abs_tol: float,
    ) -> ReproductionStatus:
        if comparison == "gte":
            if achieved >= threshold:
                return ReproductionStatus.REPRODUCED
            if threshold - achieved <= 2 * abs_tol:
                return ReproductionStatus.PARTIAL
            return ReproductionStatus.FAILED

        if comparison == "lte":
            if achieved <= threshold:
                return ReproductionStatus.REPRODUCED
            if achieved - threshold <= 2 * abs_tol:
                return ReproductionStatus.PARTIAL
            return ReproductionStatus.FAILED

        # within_tolerance / eq
        diff = abs(achieved - threshold)
        if diff <= abs_tol:
            return ReproductionStatus.REPRODUCED
        if diff <= 2 * abs_tol:
            return ReproductionStatus.PARTIAL
        return ReproductionStatus.FAILED

    def _worst_status(self, statuses: List[ReproductionStatus]) -> ReproductionStatus:
        return max(statuses, key=lambda s: _STATUS_RANK.get(s, 0))
