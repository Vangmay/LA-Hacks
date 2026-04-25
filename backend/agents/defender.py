import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from pydantic import ValidationError

from config import settings
from models import Rebuttal

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are the author of the paper defending this claim against a peer "
    "reviewer's challenge. Give the strongest possible rebuttal. If the "
    "challenge reveals a genuine flaw, acknowledge the scope limitation but "
    "argue why the core result still holds. If the challenge is wrong, "
    "explain exactly why. Be precise and technical. Return JSON: "
    "{rebuttal_text: str, supporting_evidence: [str]}"
)

_USER_PROMPT_TMPL = """CLAIM:
\"\"\"
{claim_text}
\"\"\"

PEER REVIEWER CHALLENGE:
\"\"\"
{challenge_text}
\"\"\"

Return ONLY a JSON object with this exact shape:
{{"rebuttal_text": "<your rebuttal as a single string>", "supporting_evidence": ["<evidence string>", ...]}}

No prose, no markdown, no code fences."""


class DefenderAgent(BaseAgent):
    agent_id = "defender"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else None
        claim_text = context.claim.text if context.claim else ""
        challenges = (context.extra or {}).get("challenges") or []

        if not challenges:
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim_id,
                status="success",
                output={"rebuttals": []},
                confidence=1.0,
            )

        tasks = [self._rebut_one(claim_text, ch) for ch in challenges]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rebuttals: List[Dict[str, Any]] = []
        for challenge, res in zip(challenges, results):
            challenge_id = (challenge or {}).get("challenge_id") or ""
            if isinstance(res, Exception):
                logger.warning(
                    "Defender task raised for challenge %s: %s", challenge_id, res
                )
                rebuttals.append(
                    Rebuttal(
                        challenge_id=challenge_id,
                        rebuttal_text=f"(defense unavailable: {res})",
                        supporting_evidence=[],
                    ).model_dump()
                )
            else:
                rebuttals.append(res.model_dump())

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={"rebuttals": rebuttals},
            confidence=0.7,
        )

    async def _rebut_one(
        self, claim_text: str, challenge: Dict[str, Any]
    ) -> Rebuttal:
        challenge_id = (challenge or {}).get("challenge_id") or ""
        challenge_text = (challenge or {}).get("challenge_text") or ""

        try:
            raw = await self._call_llm(claim_text, challenge_text)
        except Exception as e:
            logger.exception("LLM call failed in DefenderAgent")
            return Rebuttal(
                challenge_id=challenge_id,
                rebuttal_text=f"(defense unavailable due to LLM error: {e})",
                supporting_evidence=[],
            )

        rebuttal_text, evidence = _parse_rebuttal(raw)
        try:
            return Rebuttal(
                challenge_id=challenge_id,
                rebuttal_text=rebuttal_text,
                supporting_evidence=evidence,
            )
        except ValidationError as e:
            logger.warning(
                "Rebuttal validation failed for %s: %s", challenge_id, e
            )
            text_value = (rebuttal_text or raw or "(no rebuttal)").strip()
            return Rebuttal(
                challenge_id=challenge_id,
                rebuttal_text=text_value or "(no rebuttal)",
                supporting_evidence=[],
            )

    async def _call_llm(self, claim_text: str, challenge_text: str) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _USER_PROMPT_TMPL.format(
                        claim_text=claim_text,
                        challenge_text=challenge_text,
                    ),
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
        )
        return response.choices[0].message.content or ""


def _parse_rebuttal(raw: str) -> Tuple[str, List[str]]:
    if not raw or not raw.strip():
        return "(no response from defender)", []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip(), []

    if not isinstance(data, dict):
        return raw.strip(), []

    text_val = data.get("rebuttal_text")
    if isinstance(text_val, str) and text_val.strip():
        rebuttal_text = text_val.strip()
    else:
        rebuttal_text = raw.strip()

    evidence_raw = data.get("supporting_evidence")
    if isinstance(evidence_raw, list):
        evidence = [
            str(item).strip()
            for item in evidence_raw
            if isinstance(item, (str, int, float)) and str(item).strip()
        ]
    else:
        evidence = []

    return rebuttal_text, evidence
