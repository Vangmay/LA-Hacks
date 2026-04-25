import json
import logging

from openai import AsyncOpenAI

from config import settings
from models import Challenge
from .base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Construct an explicit mathematical counterexample to this claim if one exists. "
    "If you can construct one, describe it precisely with specific values. "
    "If the claim appears universally valid, say so. "
    'Return JSON: {"counterexample_found": bool, "description": str, "values": dict}'
)


class CounterexampleSearchAgent(BaseAgent):
    agent_id = "counterexample_search"

    _client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def run(self, context: AgentContext) -> AgentResult:
        claim = context.claim
        claim_id = claim.claim_id if claim else None

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": claim.text if claim else ""},
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
            )
            data = json.loads(response.choices[0].message.content or "{}")
        except Exception as exc:
            logger.error("counterexample_search: OpenAI call failed: %s", exc)
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim_id,
                status="inconclusive",
                output={"challenges": []},
                confidence=0.0,
                error=str(exc),
            )

        challenges = []
        if data.get("counterexample_found"):
            values = data.get("values", {})
            evidence = [f"{k} = {v}" for k, v in values.items()] if values else []
            challenges.append(Challenge(
                challenge_id=f"ch_{claim_id}_cx_001",
                claim_id=claim_id or "",
                attacker_agent=self.agent_id,
                challenge_text=data.get("description", "Counterexample found."),
                supporting_evidence=evidence,
            ).model_dump())

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={"challenges": challenges},
            confidence=0.85 if challenges else 0.5,
        )
