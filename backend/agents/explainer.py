"""ExplainerAgent — explain a ResearchAtom at a given comprehension level."""
from __future__ import annotations

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a mathematical expositor. Explain the given research atom at the "
    "specified comprehension level.\n"
    "- layperson: no equations, use everyday analogies, focus on what the result means\n"
    "- undergraduate: minimal jargon, one intuitive example, light formalism\n"
    "- graduate: full formalism, proof sketch, connection to standard results\n"
    "- expert: terse, assume full background, focus on what's novel or surprising\n"
    "Return JSON only with keys: explanation (full explanation at level), "
    "key_insight (one sentence core takeaway), "
    "worked_example (a concrete example if applicable, null otherwise)."
)


class ExplainerAgent(BaseAgent):
    agent_id = "explainer"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        atom = context.atom
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={},
                confidence=0.0,
                error="atom missing from context",
            )

        level = context.extra.get("comprehension_level", "undergraduate")

        user_content = (
            f"Comprehension level: {level}\n\n"
            f"Atom type: {atom.atom_type.value}\n"
            f"Section: {atom.section_heading or 'unknown'}\n\n"
            f"Atom text:\n{atom.text}"
        )

        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={},
                confidence=0.0,
                error=f"json_parse_failed: {exc}",
            )
        except Exception as exc:
            logger.exception("ExplainerAgent LLM call failed")
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={},
                confidence=0.0,
                error=str(exc),
            )

        explanation = data.get("explanation", "")
        key_insight = data.get("key_insight", "")
        worked_example = data.get("worked_example")

        if not explanation or not key_insight:
            return AgentResult(
                agent_id=self.agent_id,
                status="inconclusive",
                output=data,
                confidence=0.3,
                error="incomplete explanation response",
            )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "explanation": explanation,
                "key_insight": key_insight,
                "worked_example": worked_example,
            },
            confidence=0.9,
        )
