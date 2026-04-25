"""GlossaryAgent — extract non-standard terms and notation from a ResearchAtom."""
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
    "Extract all non-standard mathematical terms and notation from the given "
    "research atom's text and provide one-sentence definitions for each. "
    "Include symbols and notation that may be unfamiliar to a general reader. "
    "Return a JSON object with key 'glossary' mapping term → definition string. "
    "Return ONLY the JSON object."
)


class GlossaryAgent(BaseAgent):
    agent_id = "glossary"

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
                output={"glossary": {}},
                confidence=0.0,
                error="atom missing from context",
            )

        user_content = (
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
                max_tokens=600,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"glossary": {}},
                confidence=0.0,
                error=f"json_parse_failed: {exc}",
            )
        except Exception as exc:
            logger.exception("GlossaryAgent LLM call failed")
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"glossary": {}},
                confidence=0.0,
                error=str(exc),
            )

        glossary = data.get("glossary") if isinstance(data, dict) else None
        if not isinstance(glossary, dict):
            glossary = {}

        # Sanitize: keep only string keys and string values.
        clean = {str(k): str(v) for k, v in glossary.items() if k and v}

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"glossary": clean},
            confidence=0.85,
        )
