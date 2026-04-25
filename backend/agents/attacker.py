import asyncio
import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from config import settings
from models import Challenge
from .base import BaseAgent, AgentContext, AgentResult
from .counterexample_search import CounterexampleSearchAgent
from .citation_gap import CitationGapAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a hostile but rigorous peer reviewer. Your job is to find every possible flaw "
    "in the given mathematical claim. Use the verification results as ammunition. "
    "Generate between 1 and 3 challenges. Each challenge must be: specific (reference the "
    "exact part of the claim being attacked), technically grounded (not vague), and falsifiable. "
    'Return a JSON object: {"challenges": [{"challenge_text": str, "supporting_evidence": [str]}]}'
)


class AttackerAgent(BaseAgent):
    agent_id = "attacker"

    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        counterexample_agent: Optional[CounterexampleSearchAgent] = None,
        citation_gap_agent: Optional[CitationGapAgent] = None,
    ) -> None:
        self._client = client
        self._counterexample_agent = counterexample_agent
        self._citation_gap_agent = citation_gap_agent

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        claim = context.claim
        claim_id = claim.claim_id if claim else None
        verification_results = context.extra.get("verification_results", [])

        # Build tier summary for the prompt
        tier_summary = "; ".join(
            f"{r.get('tier', '?')} check: {r.get('status', '?').upper()} — {r.get('evidence', '')[:80]}"
            for r in verification_results
        ) or "No prior verification results."

        user_content = json.dumps({
            "claim_id": claim_id,
            "claim_type": claim.claim_type if claim else "",
            "claim_text": claim.text if claim else "",
            "equations": claim.equations if claim else [],
            "tier_results": tier_summary,
        })

        # Main attacker LLM call
        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            data = json.loads(response.choices[0].message.content or "{}")
            raw_challenges = data.get("challenges", [])
        except Exception as exc:
            logger.error("attacker: OpenAI call failed: %s", exc)
            raw_challenges = []

        challenges = []
        for i, ch in enumerate(raw_challenges, 1):
            challenges.append(Challenge(
                challenge_id=f"ch_{claim_id}_{i:03d}",
                claim_id=claim_id or "",
                attacker_agent=self.agent_id,
                challenge_text=ch.get("challenge_text", ""),
                supporting_evidence=ch.get("supporting_evidence", []),
            ).model_dump())

        # Spawn sub-agents conditionally
        sub_tasks = []
        if claim and claim.claim_type in ("theorem", "proposition") and any(
            kw in claim.text for kw in ("for all", "for every", "∀", "for each")
        ):
            counterexample_agent = self._counterexample_agent or CounterexampleSearchAgent()
            sub_tasks.append(counterexample_agent.run(context))

        if claim and claim.citations:
            citation_gap_agent = self._citation_gap_agent or CitationGapAgent()
            sub_tasks.append(citation_gap_agent.run(context))

        if sub_tasks:
            sub_results = await asyncio.gather(*sub_tasks, return_exceptions=True)
            idx = 1
            for result in sub_results:
                if isinstance(result, Exception):
                    logger.warning("attacker: sub-agent raised %s", result)
                    continue
                for ch in result.output.get("challenges", []):
                    # Re-ID to avoid collisions with main challenges
                    ch["challenge_id"] = f"ch_{claim_id}_sub_{idx:03d}"
                    idx += 1
                    challenges.append(ch)

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={"challenges": challenges},
            confidence=0.8 if challenges else 0.5,
        )
