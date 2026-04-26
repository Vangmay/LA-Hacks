import json
import logging
import asyncio
from typing import List

from openai import AsyncOpenAI

from config import settings
from models import ClaimUnit
from agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10

_SYSTEM_PROMPT = (
    "Classify each mathematical/algorithmic claim as 'testable' (can be verified by running "
    "an experiment and measuring a metric) or 'theoretical' (requires mathematical proof only). "
    "For testable claims, briefly state what experiment would verify it. "
    "Return a JSON object with a single key 'results' containing an array: "
    "{\"results\": [{\"claim_id\": str, \"testability\": \"testable\"|\"theoretical\", \"reason\": str}]}"
)


class ClaimFilterAgent(BaseAgent):
    agent_id = "claim_filter"

    _client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def run(self, context: AgentContext) -> AgentResult:
        claims: List[ClaimUnit] = context.extra.get("claims", [])
        if not claims:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"testable": [], "theoretical": [], "classifications": {}},
                confidence=0.0,
                error="No claims provided in context.extra['claims']",
            )

        try:
            classifications = await self._classify_all(claims)
        except Exception as exc:
            logger.error("ClaimFilterAgent failed: %s", exc)
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"testable": [], "theoretical": [], "classifications": {}},
                confidence=0.0,
                error=str(exc),
            )

        testable = [cid for cid, v in classifications.items() if v["testability"] == "testable"]
        theoretical = [cid for cid, v in classifications.items() if v["testability"] == "theoretical"]

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "testable": testable,
                "theoretical": theoretical,
                "classifications": classifications,
            },
            confidence=0.85,
        )

    async def _classify_all(self, claims: List[ClaimUnit]) -> dict:
        batches = [claims[i:i + _BATCH_SIZE] for i in range(0, len(claims), _BATCH_SIZE)]
        results = await asyncio.gather(*[self._classify_batch(b) for b in batches])
        merged = {}
        for batch_result in results:
            merged.update(batch_result)
        return merged

    async def _classify_batch(self, batch: List[ClaimUnit]) -> dict:
        user_prompt = json.dumps([
            {"claim_id": c.claim_id, "text": c.text} for c in batch
        ])

        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
        )
        raw = response.choices[0].message.content

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = await self._retry_parse(user_prompt)

        if isinstance(parsed, list):
            items = parsed
        else:
            items = parsed.get("results") or next(
                (v for v in parsed.values() if isinstance(v, list)), []
            )

        out = {}
        for item in items:
            cid = item.get("claim_id")
            testability = item.get("testability", "theoretical")
            if testability not in ("testable", "theoretical"):
                testability = "theoretical"
            out[cid] = {
                "testability": testability,
                "reason": item.get("reason", ""),
            }
        return out

    async def _retry_parse(self, user_prompt: str) -> dict:
        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT + " Respond with ONLY valid JSON, no markdown."},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
        )
        raw = response.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"results": []}
