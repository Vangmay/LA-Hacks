"""Defense agent — replaces the legacy DefenderAgent.

For each `Challenge`, asks the LLM for a typed `Rebuttal`. The defender
must be honest: if a challenge is valid, concede or clarify scope; if
invalid, explain precisely why. The verdict aggregator looks at
`response_type` and `confidence` to decide whether the challenge is
resolved.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai
from models import (
    Challenge,
    Evidence,
    EvidenceSourceType,
    Rebuttal,
    RebuttalType,
    ResearchAtom,
)

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = (
    "You are defending the paper but must be honest. If a challenge is "
    "valid, concede or clarify the scope. If invalid, explain precisely "
    "why using the source text and check results. Do not invent paper "
    "content. Output JSON only."
)

_USER_PROMPT_TMPL = """Atom (id {atom_id}, type {atom_type}, section {section}):
\"\"\"
{atom_text}
\"\"\"

Source excerpt:
\"\"\"
{source_excerpt}
\"\"\"

Challenge ({challenge_type}, severity {severity}):
\"\"\"
{challenge_text}
\"\"\"

Allowed response types:
resolves, partially_resolves, concedes, clarifies_scope, disputes,
unsupported_defense.

Return JSON:
{{
  "response_type": "...",
  "rebuttal_text": "<one paragraph>",
  "evidence": [{{"text": "...", "source": "atom_text|equation|citation|check"}}],
  "confidence": 0.0
}}

Output ONLY the JSON object.
"""


class DefenseAgent(BaseAgent):
    agent_id = "defense_agent"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        atom = context.atom
        challenges = context.challenges
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"rebuttals": []},
                confidence=0.0,
                error="atom missing",
            )
        if not challenges:
            return AgentResult(
                agent_id=self.agent_id,
                status="success",
                output={"rebuttals": []},
                confidence=1.0,
            )

        tasks = [self._respond(atom, ch) for ch in challenges]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rebuttals: list[Rebuttal] = []
        for ch, result in zip(challenges, results):
            if isinstance(result, Exception):
                logger.warning("defense_agent: error for %s: %s", ch.challenge_id, result)
                rebuttals.append(_unsupported_rebuttal(atom, ch, str(result)))
            elif result is None:
                rebuttals.append(_unsupported_rebuttal(atom, ch, "no rebuttal"))
            else:
                rebuttals.append(result)

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"rebuttals": [r.model_dump() for r in rebuttals]},
            confidence=0.7,
        )

    async def _respond(self, atom: ResearchAtom, challenge: Challenge) -> Optional[Rebuttal]:
        prompt = _USER_PROMPT_TMPL.format(
            atom_id=atom.atom_id,
            atom_type=atom.atom_type.value,
            section=atom.section_heading or "?",
            atom_text=atom.text,
            source_excerpt=atom.source_span.raw_excerpt[:1200],
            challenge_type=challenge.challenge_type.value,
            severity=challenge.severity.value,
            challenge_text=challenge.challenge_text,
        )
        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=900,
            )
            raw = response.choices[0].message.content or "{}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("defense_agent LLM call failed for %s", challenge.challenge_id)
            return _unsupported_rebuttal(atom, challenge, f"LLM error: {exc}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return _unsupported_rebuttal(atom, challenge, "json_parse_failed")
        if not isinstance(data, dict):
            return _unsupported_rebuttal(atom, challenge, "non-dict response")

        rtype = _coerce_rebuttal_type(data.get("response_type"))
        text = (data.get("rebuttal_text") or "").strip()
        if not text:
            return _unsupported_rebuttal(atom, challenge, "empty rebuttal text")

        evidence = _build_evidence(atom, data.get("evidence"))
        confidence = _coerce_confidence(data.get("confidence"), default=0.5)

        return Rebuttal(
            rebuttal_id=f"rb_{challenge.challenge_id}_{uuid.uuid4().hex[:6]}",
            challenge_id=challenge.challenge_id,
            atom_id=atom.atom_id,
            defender_agent=self.agent_id,
            response_type=rtype,
            rebuttal_text=text,
            evidence=evidence,
            confidence=confidence,
        )


def _unsupported_rebuttal(
    atom: ResearchAtom,
    challenge: Challenge,
    reason: str,
) -> Rebuttal:
    return Rebuttal(
        rebuttal_id=f"rb_{challenge.challenge_id}_unsup",
        challenge_id=challenge.challenge_id,
        atom_id=atom.atom_id,
        defender_agent="defense_agent",
        response_type=RebuttalType.UNSUPPORTED_DEFENSE,
        rebuttal_text=f"defense unavailable: {reason}",
        evidence=[],
        confidence=0.0,
    )


def _build_evidence(atom: ResearchAtom, raw: Any) -> list[Evidence]:
    if not isinstance(raw, list):
        return []
    out: list[Evidence] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        text = (entry.get("text") or "").strip()
        if not text:
            continue
        source_label = (entry.get("source") or "").strip().lower()
        source_type = {
            "atom_text": EvidenceSourceType.PAPER_SPAN,
            "equation": EvidenceSourceType.EQUATION,
            "citation": EvidenceSourceType.CITATION,
            "check": EvidenceSourceType.AGENT_REASONING,
        }.get(source_label, EvidenceSourceType.AGENT_REASONING)
        out.append(
            Evidence(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                source_type=source_type,
                text=text[:1000],
                paper_id=atom.paper_id,
                atom_id=atom.atom_id,
                confidence=0.6,
            )
        )
    return out


def _coerce_rebuttal_type(value: Any) -> RebuttalType:
    if isinstance(value, str):
        try:
            return RebuttalType(value.strip().lower())
        except ValueError:
            pass
    return RebuttalType.UNSUPPORTED_DEFENSE


def _coerce_confidence(value: Any, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))
