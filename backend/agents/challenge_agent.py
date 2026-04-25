"""Challenge agent — replaces the legacy AttackerAgent.

Asks an LLM for at most 3 typed `Challenge` objects per atom, each carrying
a `challenge_type`, severity, evidence list, and a falsifiable test. The
agent gets the atom, its attached equations and citations, the surrounding
graph context, and the prior `CheckResult`s as ammunition.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai
from models import (
    Challenge,
    ChallengeType,
    CheckResult,
    Evidence,
    EvidenceSourceType,
    ResearchAtom,
    ResearchGraph,
    Severity,
)

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = (
    "You are a rigorous adversarial reviewer of a theoretical research "
    "paper. Generate AT MOST 3 challenges per atom. Each challenge must be "
    "specific, technically grounded, and falsifiable. Vague skepticism is "
    "not allowed. Use the check results and source excerpt as evidence. "
    "Output JSON only."
)

_USER_PROMPT_TMPL = """Atom under review (id {atom_id}, type {atom_type}, section {section}):
\"\"\"
{atom_text}
\"\"\"

Source excerpt:
\"\"\"
{source_excerpt}
\"\"\"

Equations attached:
{equations_block}

Citations attached:
{citations_block}

Prior checks:
{checks_block}

Graph context (atoms this one depends on):
{graph_block}

Allowed challenge types:
counterexample, missing_assumption, proof_gap, citation_gap,
notation_ambiguity, scope_overclaim, contradicts_prior_work,
algebraic_error, numeric_failure, other.

Severity: low | medium | high | fatal.

Return JSON:
{{
  "challenges": [
    {{
      "challenge_type": "...",
      "severity": "low|medium|high|fatal",
      "challenge_text": "<one paragraph>",
      "evidence": [
        {{"text": "...", "source": "atom_text|equation|citation|check|graph"}}
      ],
      "falsifiable_test": "<concrete test that would resolve the challenge>",
      "confidence": 0.0
    }}
  ]
}}

If no serious challenge applies, return {{"challenges": []}}.
Output ONLY the JSON object.
"""


class ChallengeAgent(BaseAgent):
    agent_id = "challenge_agent"

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
                output={"challenges": []},
                confidence=0.0,
                error="atom missing",
            )

        prompt = _build_prompt(atom, context.checks, context.graph)

        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            raw = response.choices[0].message.content or "{}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("challenge_agent LLM call failed for %s", atom.atom_id)
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"challenges": []},
                confidence=0.0,
                error=str(exc),
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return AgentResult(
                agent_id=self.agent_id,
                status="inconclusive",
                output={"challenges": []},
                confidence=0.3,
                error="json_parse_failed",
            )

        raw_challenges = (data or {}).get("challenges") or []
        challenges = _build_challenges(atom, raw_challenges, attacker_id=self.agent_id)

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"challenges": [c.model_dump() for c in challenges]},
            confidence=0.7 if challenges else 0.5,
        )


def _build_prompt(
    atom: ResearchAtom,
    checks: list[CheckResult],
    graph: Optional[ResearchGraph],
) -> str:
    eq_block = (
        "\n".join(f"- {eq.equation_id}: {eq.latex}" for eq in atom.equations)
        if atom.equations
        else "(none)"
    )
    cite_block = (
        "\n".join(
            f"- {c.citation_id} key={c.key or '?'} label={c.label or '?'}"
            for c in atom.citations
        )
        if atom.citations
        else "(none)"
    )
    if checks:
        check_lines = []
        for check in checks:
            line = f"- {check.kind.value} → {check.status.value}: {check.summary}"
            check_lines.append(line)
        checks_block = "\n".join(check_lines)
    else:
        checks_block = "(none)"

    graph_block = "(no upstream dependencies)"
    if graph is not None:
        deps = [
            edge.target_id
            for edge in graph.edges
            if edge.source_id == atom.atom_id
        ]
        if deps:
            graph_block = ", ".join(deps)

    return _USER_PROMPT_TMPL.format(
        atom_id=atom.atom_id,
        atom_type=atom.atom_type.value,
        section=atom.section_heading or "?",
        atom_text=atom.text,
        source_excerpt=atom.source_span.raw_excerpt[:1200],
        equations_block=eq_block,
        citations_block=cite_block,
        checks_block=checks_block,
        graph_block=graph_block,
    )


def _build_challenges(
    atom: ResearchAtom,
    raw_challenges: list[Any],
    *,
    attacker_id: str,
) -> list[Challenge]:
    out: list[Challenge] = []
    for entry in raw_challenges[:3]:
        if not isinstance(entry, dict):
            continue
        challenge_type = _coerce_challenge_type(entry.get("challenge_type"))
        severity = _coerce_severity(entry.get("severity"))
        text = (entry.get("challenge_text") or "").strip()
        if not text:
            continue

        evidence_objects = _build_evidence(atom, entry.get("evidence"))
        confidence = _coerce_confidence(entry.get("confidence"), default=0.6)
        falsifiable = (entry.get("falsifiable_test") or "").strip() or None

        out.append(
            Challenge(
                challenge_id=f"ch_{atom.atom_id}_{len(out) + 1:03d}",
                atom_id=atom.atom_id,
                attacker_agent=attacker_id,
                challenge_type=challenge_type,
                severity=severity,
                challenge_text=text,
                evidence=evidence_objects,
                falsifiable_test=falsifiable,
                confidence=confidence,
            )
        )
    return out


def _build_evidence(atom: ResearchAtom, raw_evidence: Any) -> list[Evidence]:
    if not isinstance(raw_evidence, list):
        return []
    out: list[Evidence] = []
    for entry in raw_evidence:
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
            "graph": EvidenceSourceType.AGENT_REASONING,
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


def _coerce_challenge_type(value: Any) -> ChallengeType:
    if isinstance(value, str):
        try:
            return ChallengeType(value.strip().lower())
        except ValueError:
            pass
    return ChallengeType.OTHER


def _coerce_severity(value: Any) -> Severity:
    if isinstance(value, str):
        try:
            return Severity(value.strip().lower())
        except ValueError:
            pass
    return Severity.MEDIUM


def _coerce_confidence(value: Any, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))
