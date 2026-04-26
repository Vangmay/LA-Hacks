import json
import logging
import uuid
from typing import Optional

from openai import AsyncOpenAI

from agents.base import AgentContext, AgentResult, BaseAgent
from config import settings
from models import (
    ClaimTestability,
    MetricCriterion,
    PoCSpec,
    ResearchAtom,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Extract all quantitative success and failure criteria from this research atom. For each metric:
- metric_name: what is being measured (e.g. 'top-1 accuracy', 'training time', 'memory usage')
- paper_reported_value: exact string from paper (e.g. '94.3% on ImageNet')
- numeric_threshold: the numeric value as a float (null if not extractable)
- tolerance: how much deviation counts as reproduction (default 0.02 = 2% relative)
- comparison: 'gte' if the metric should be >= threshold, 'lte' if <=, 'within_tolerance' if ±tolerance
- experimental_conditions: dict of required conditions stated in paper (dataset, model size, batch size, etc.)
- For each metric, also extract the exact model(s) used (name, version, architecture) and include this as a 'model' field in experimental_conditions. If the model is not specified, set 'model': null or 'model': 'unspecified'.

Return JSON: {"success_criteria": [...], "failure_criteria": [...]}
Failure criteria = negation of success criteria plus any explicit failure conditions stated.
If numeric_threshold cannot be extractable, set it to null."""


class MetricExtractorAgent(BaseAgent):
    agent_id = "metric_extractor"

    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        model: Optional[str] = None,
    ) -> None:
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = model or settings.openai_model

    async def run(self, context: AgentContext) -> AgentResult:
        atom: ResearchAtom | None = context.atom or context.extra.get("atom")
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output=self._empty_spec("unknown"),
                confidence=0.0,
                error="No atom provided in context.atom",
            )

        try:
            spec_dict = await self._extract(atom)
        except Exception as exc:
            logger.error("MetricExtractorAgent failed for %s: %s", atom.atom_id, exc)
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output=self._empty_spec(atom.atom_id),
                confidence=0.0,
                error=str(exc),
            )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output=spec_dict,
            confidence=0.8,
        )

    async def _extract(self, atom: ResearchAtom) -> dict:
        section = atom.section_heading or "?"
        user_prompt = (
            f"Atom ID: {atom.atom_id}\n"
            f"Atom type: {atom.atom_type.value}\n"
            f"Section: {section}\n"
            f"Atom text: {atom.text}"
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
        )
        raw = response.choices[0].message.content

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = await self._retry_parse(user_prompt)

        def clean_model_key(criteria_list):
            for c in criteria_list:
                if isinstance(c, dict):
                    exp_conds = c.get("experimental_conditions")
                    if exp_conds is not None and ("model" in exp_conds) and (exp_conds["model"] is None or str(exp_conds["model"]).lower() == "none"):
                        del exp_conds["model"]
            return criteria_list

        data["success_criteria"] = clean_model_key(data.get("success_criteria", []))
        data["failure_criteria"] = clean_model_key(data.get("failure_criteria", []))

        success_criteria = self._parse_criteria(data.get("success_criteria", []))
        failure_criteria = self._parse_criteria(data.get("failure_criteria", []))

        spec = PoCSpec(
            spec_id=str(uuid.uuid4()),
            claim_id=atom.atom_id,
            testability=ClaimTestability.TESTABLE,
            success_criteria=success_criteria,
            failure_criteria=failure_criteria,
            scaffold_files={},
            readme="",
        )
        return spec.model_dump()

    def _parse_criteria(self, raw_list: list) -> list[MetricCriterion]:
        criteria = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            comparison = item.get("comparison", "within_tolerance")
            if comparison not in ("gte", "lte", "eq", "within_tolerance"):
                comparison = "within_tolerance"
            exp_conds = item.get("experimental_conditions") or {}
            if "model" in exp_conds and (exp_conds["model"] is None or str(exp_conds["model"]).lower() == "none"):
                del exp_conds["model"]
            try:
                criteria.append(MetricCriterion(
                    metric_name=item.get("metric_name", "unknown"),
                    paper_reported_value=str(item.get("paper_reported_value", "")),
                    numeric_threshold=item.get("numeric_threshold"),
                    tolerance=float(item.get("tolerance", 0.02)),
                    comparison=comparison,
                    experimental_conditions=exp_conds,
                ))
            except Exception as exc:
                logger.warning("Skipping malformed criterion: %s — %s", item, exc)
        return criteria

    async def _retry_parse(self, user_prompt: str) -> dict:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT + "\nRespond with ONLY valid JSON, no markdown."},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
        )
        raw = response.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"success_criteria": [], "failure_criteria": []}

    def _empty_spec(self, claim_id: str) -> dict:
        return PoCSpec(
            spec_id=str(uuid.uuid4()),
            claim_id=claim_id,
            testability=ClaimTestability.TESTABLE,
            success_criteria=[],
            failure_criteria=[],
            scaffold_files={},
            readme="",
        ).model_dump()
