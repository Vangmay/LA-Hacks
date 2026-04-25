import json
import logging

from openai import AsyncOpenAI

from config import settings
from models import Challenge
from .base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Given this claim and its cited references (listed by ref_id only since we don't have full text), "
    "identify any citation gaps: places where the claim makes an appeal to a result but either cites "
    "nothing, cites something implausibly general, or the citation seems mismatched. "
    'Return JSON: {"gaps": [{"location": str, "issue": str}]}'
)


class CitationGapAgent(BaseAgent):
    agent_id = "citation_gap"

    _client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def run(self, context: AgentContext) -> AgentResult:
        claim = context.claim
        claim_id = claim.claim_id if claim else None

        user_content = json.dumps({
            "claim": claim.text if claim else "",
            "citations": claim.citations if claim else [],
        })

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
            )
            data = json.loads(response.choices[0].message.content or "{}")
        except Exception as exc:
            logger.error("citation_gap: OpenAI call failed: %s", exc)
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim_id,
                status="inconclusive",
                output={"challenges": []},
                confidence=0.0,
                error=str(exc),
            )

        challenges = []
        for i, gap in enumerate(data.get("gaps", []), 1):
            challenges.append(Challenge(
                challenge_id=f"ch_{claim_id}_cg_{i:03d}",
                claim_id=claim_id or "",
                attacker_agent=self.agent_id,
                challenge_text=f"{gap.get('location', 'Unknown location')}: {gap.get('issue', '')}",
                supporting_evidence=[],
            ).model_dump())

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={"challenges": challenges},
            confidence=0.75 if challenges else 0.5,
        )
