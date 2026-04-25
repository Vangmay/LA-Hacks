"""Deterministic verdict aggregator.

The decision is rule-based; the LLM is only invited to write the prose
rationale (and only when there is something interesting to say).

For each atom we fold the typed checks + challenges + rebuttals into a
single `AtomVerdict`. Reason codes capture *why* the label was chosen so
the report can render an audit trail.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai
from models import (
    AtomVerdict,
    Challenge,
    CheckResult,
    CheckStatus,
    Rebuttal,
    RebuttalType,
    ResearchAtom,
    Severity,
    VerdictLabel,
    VerdictReasonCode,
    is_reviewable,
)

logger = logging.getLogger(__name__)


_RESOLVING_REBUTTAL_TYPES = {
    RebuttalType.RESOLVES,
    RebuttalType.CLARIFIES_SCOPE,
    RebuttalType.DISPUTES,
}
_RESOLVE_CONFIDENCE_THRESHOLD = 0.6


def aggregate_verdict(
    atom: ResearchAtom,
    checks: list[CheckResult],
    challenges: list[Challenge],
    rebuttals: list[Rebuttal],
) -> AtomVerdict:
    if not is_reviewable(atom):
        return AtomVerdict(
            verdict_id=f"v_{atom.atom_id}_{uuid.uuid4().hex[:6]}",
            atom_id=atom.atom_id,
            label=VerdictLabel.NOT_CHECKABLE,
            confidence=0.2,
            reason_codes=[VerdictReasonCode.NOT_REVIEWED],
            rationale=(
                f"{atom.atom_type.value} atoms in section "
                f"{atom.section_heading or '?'} are not adversarially reviewed."
            ),
            checks=checks,
            challenges=challenges,
            rebuttals=rebuttals,
        )

    rebuttal_by_challenge: dict[str, Rebuttal] = {r.challenge_id: r for r in rebuttals}
    unresolved = _unresolved_challenges(challenges, rebuttal_by_challenge)

    label, reason_codes, confidence = _decide_label(checks, challenges, unresolved)

    rationale = _short_rationale(atom, label, reason_codes, checks, unresolved)

    return AtomVerdict(
        verdict_id=f"v_{atom.atom_id}_{uuid.uuid4().hex[:6]}",
        atom_id=atom.atom_id,
        label=label,
        confidence=confidence,
        reason_codes=reason_codes,
        rationale=rationale,
        checks=checks,
        challenges=challenges,
        rebuttals=rebuttals,
    )


def _unresolved_challenges(
    challenges: list[Challenge],
    rebuttal_by_challenge: dict[str, Rebuttal],
) -> list[Challenge]:
    unresolved: list[Challenge] = []
    for challenge in challenges:
        rebuttal = rebuttal_by_challenge.get(challenge.challenge_id)
        if rebuttal is None:
            unresolved.append(challenge)
            continue
        if (
            rebuttal.response_type in _RESOLVING_REBUTTAL_TYPES
            and rebuttal.confidence >= _RESOLVE_CONFIDENCE_THRESHOLD
        ):
            continue
        unresolved.append(challenge)
    return unresolved


def _decide_label(
    checks: list[CheckResult],
    challenges: list[Challenge],
    unresolved: list[Challenge],
) -> tuple[VerdictLabel, list[VerdictReasonCode], float]:
    reasons: list[VerdictReasonCode] = []

    if any(c.status == CheckStatus.COUNTEREXAMPLE_FOUND for c in checks):
        reasons.append(VerdictReasonCode.EXPLICIT_COUNTEREXAMPLE)
        return VerdictLabel.REFUTED, reasons, 0.92

    if any(c.status == CheckStatus.FAILED for c in checks):
        reasons.append(VerdictReasonCode.ALGEBRAIC_FAILURE)
        # Algebraic failures are strong-but-not-conclusive against the whole atom.
        return VerdictLabel.LIKELY_FLAWED, reasons, 0.75

    fatal_unresolved = [c for c in unresolved if c.severity == Severity.FATAL]
    high_unresolved = [c for c in unresolved if c.severity == Severity.HIGH]

    if fatal_unresolved:
        reasons.append(VerdictReasonCode.UNRESOLVED_FATAL_CHALLENGE)
        return VerdictLabel.LIKELY_FLAWED, reasons, 0.7

    if high_unresolved:
        reasons.append(VerdictReasonCode.UNRESOLVED_HIGH_CHALLENGE)
        return VerdictLabel.CONTESTED, reasons, 0.6

    if unresolved:
        reasons.append(VerdictReasonCode.UNRESOLVED_HIGH_CHALLENGE)
        return VerdictLabel.CONTESTED, reasons, 0.55

    actionable_checks = [
        c
        for c in checks
        if c.status
        not in (CheckStatus.NOT_APPLICABLE, CheckStatus.INCONCLUSIVE)
    ]
    if not actionable_checks and not challenges:
        reasons.append(VerdictReasonCode.CHECKS_INCONCLUSIVE)
        return VerdictLabel.NOT_CHECKABLE, reasons, 0.4

    reasons.append(VerdictReasonCode.NO_SERIOUS_CHALLENGES)
    return VerdictLabel.NO_OBJECTION_FOUND, reasons, 0.65


def _short_rationale(
    atom: ResearchAtom,
    label: VerdictLabel,
    reason_codes: list[VerdictReasonCode],
    checks: list[CheckResult],
    unresolved: list[Challenge],
) -> str:
    pieces: list[str] = [f"{label.value} for {atom.atom_type.value} atom {atom.atom_id}."]
    for code in reason_codes:
        pieces.append(_reason_phrase(code, checks, unresolved))
    return " ".join(pieces)


def _reason_phrase(
    code: VerdictReasonCode,
    checks: list[CheckResult],
    unresolved: list[Challenge],
) -> str:
    if code == VerdictReasonCode.EXPLICIT_COUNTEREXAMPLE:
        return "A numeric probe found a counterexample."
    if code == VerdictReasonCode.ALGEBRAIC_FAILURE:
        return "Algebraic sanity check failed on at least one attached equation."
    if code == VerdictReasonCode.UNRESOLVED_FATAL_CHALLENGE:
        types = sorted({c.challenge_type.value for c in unresolved if c.severity == Severity.FATAL})
        return f"Unresolved fatal challenge(s): {', '.join(types) or 'unspecified'}."
    if code == VerdictReasonCode.UNRESOLVED_HIGH_CHALLENGE:
        types = sorted({c.challenge_type.value for c in unresolved})
        return f"Unresolved challenge(s): {', '.join(types) or 'unspecified'}."
    if code == VerdictReasonCode.CHECKS_INCONCLUSIVE:
        return "Checks were not applicable or inconclusive and no challenges were generated."
    if code == VerdictReasonCode.NO_SERIOUS_CHALLENGES:
        return "Checks did not surface a concrete failure and no challenges remained unresolved."
    if code == VerdictReasonCode.CASCADED_FROM_DEPENDENCY:
        return "Cascaded from a refuted dependency."
    if code == VerdictReasonCode.NOT_REVIEWED:
        return "Atom type was not selected for adversarial review."
    return code.value


# ---------------------------------------------------------------------------
# Optional LLM rationale upgrade (called from orchestrator if desired).


async def llm_polish_rationale(
    atom: ResearchAtom,
    verdict: AtomVerdict,
    *,
    client: Optional[AsyncOpenAI] = None,
) -> str:
    """One short LLM call that turns the deterministic rationale into prose
    grounded in the atom and its evidence. The rule-derived label is fixed.
    """
    cli = client or make_async_openai()
    prompt = (
        "Write one short paragraph (<=80 words) explaining a research-paper "
        "review verdict. Do NOT change the label. Use the supplied evidence; "
        "do not invent.\n\n"
        f"Atom text: {atom.text[:1500]}\n"
        f"Verdict label: {verdict.label.value}\n"
        f"Reason codes: {', '.join(c.value for c in verdict.reason_codes)}\n"
        f"Checks: "
        + json.dumps([
            {"kind": c.kind.value, "status": c.status.value, "summary": c.summary}
            for c in verdict.checks
        ])
        + "\n"
        f"Unresolved challenges: "
        + json.dumps([
            {"type": c.challenge_type.value, "severity": c.severity.value, "text": c.challenge_text[:200]}
            for c in verdict.challenges
        ])
        + "\n\nReturn plain text only."
    )
    try:
        response = await cli.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You write short, grounded review verdict rationales."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or verdict.rationale
    except Exception as exc:  # noqa: BLE001
        logger.warning("rationale polish failed: %s", exc)
        return verdict.rationale
