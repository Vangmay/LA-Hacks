"""SocraticTutorAgent — Socratic dialogue scoped to a single ResearchAtom.

Conversation history is passed via context.extra["history"] as a list of
{role, content} dicts. The current user message is context.extra["user_message"].
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a Socratic math tutor. The student is asking about a specific atom "
    "from a research paper. Your job is to guide them to understanding through "
    "questions and targeted explanations — not to just give answers. Stay strictly "
    "scoped to this atom. If the student's objection reveals a genuine gap in the "
    "atom, acknowledge it honestly. Be concise. "
    "Return JSON only: {\"response\": str}"
)


def _build_atom_preamble(context: AgentContext) -> str:
    atom = context.atom
    if atom is None:
        return "(no atom provided)"
    return (
        f"Atom type: {atom.atom_type.value}\n"
        f"Section: {atom.section_heading or 'unknown'}\n\n"
        f"Atom text:\n{atom.text}"
    )


def _coerce_history(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            role = str(item.get("role", "user"))
            content = str(item.get("content", ""))
            if role in {"user", "assistant"} and content.strip():
                out.append({"role": role, "content": content})
    return out


class SocraticTutorAgent(BaseAgent):
    agent_id = "socratic_tutor"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        if context.atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"response": ""},
                confidence=0.0,
                error="atom missing from context",
            )

        user_message = str(context.extra.get("user_message", "")).strip()
        if not user_message:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"response": ""},
                confidence=0.0,
                error="user_message missing from context.extra",
            )

        history = _coerce_history(context.extra.get("history", []))

        # System message embeds atom context so the tutor is always scoped.
        atom_preamble = _build_atom_preamble(context)
        system_content = _SYSTEM_PROMPT + f"\n\nAtom under discussion:\n{atom_preamble}"

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=600,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"response": ""},
                confidence=0.0,
                error=f"json_parse_failed: {exc}",
            )
        except Exception as exc:
            logger.exception("SocraticTutorAgent LLM call failed")
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"response": ""},
                confidence=0.0,
                error=str(exc),
            )

        tutor_response = data.get("response", "") if isinstance(data, dict) else ""

        return AgentResult(
            agent_id=self.agent_id,
            status="success" if tutor_response else "inconclusive",
            output={"response": str(tutor_response)},
            confidence=0.9 if tutor_response else 0.3,
        )
