"""SymPy-based algebraic sanity check.

Iterates the equations attached to an atom; for each, attempts to parse
both sides and simplify LHS-RHS. Returns a `CheckResult` with kind
`ALGEBRAIC_SANITY`. The check is honest: it never claims to "verify" a
theorem — it only reports whether the algebra of attached equations
collapses cleanly. Inequalities are reduced when possible and otherwise
reported as inconclusive.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

import sympy
from sympy import simplify, sympify
from sympy.parsing.latex import parse_latex

from models import (
    CheckKind,
    CheckResult,
    CheckStatus,
    EquationBlock,
    Evidence,
    EvidenceSourceType,
    ParsedPaper,
    ResearchAtom,
)

logger = logging.getLogger(__name__)


def run_algebraic_sanity(
    atom: ResearchAtom,
    paper: Optional[ParsedPaper] = None,
) -> CheckResult:
    check_id = f"check_alg_{atom.atom_id}_{uuid.uuid4().hex[:6]}"

    if not atom.equations:
        return CheckResult(
            check_id=check_id,
            atom_id=atom.atom_id,
            kind=CheckKind.ALGEBRAIC_SANITY,
            status=CheckStatus.NOT_APPLICABLE,
            summary="atom has no attached equations",
            confidence=0.1,
        )

    evidence: list[Evidence] = []
    statuses: list[str] = []
    raw_details: dict[str, list[dict]] = {"equations": []}

    for eq in atom.equations:
        outcome = _check_equation(eq)
        statuses.append(outcome["status"])
        raw_details["equations"].append(outcome)
        evidence.append(
            Evidence(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                source_type=EvidenceSourceType.ALGEBRAIC_CHECK,
                text=f"{eq.equation_id} ({eq.environment or '?'}): {outcome['detail']}",
                paper_id=atom.paper_id,
                atom_id=atom.atom_id,
                equation_id=eq.equation_id,
                check_id=check_id,
                confidence=outcome["confidence"],
                metadata={"latex": eq.latex},
            )
        )

    if any(s == "FAILED" for s in statuses):
        status = CheckStatus.FAILED
        confidence = 0.85
        summary = "at least one attached equation does not simplify to an identity"
    elif any(s == "PASSED" for s in statuses):
        status = CheckStatus.PASSED
        confidence = 0.7
        summary = "attached equations simplify cleanly under SymPy"
    else:
        status = CheckStatus.INCONCLUSIVE
        confidence = 0.4
        summary = "could not parse or simplify attached equations"

    return CheckResult(
        check_id=check_id,
        atom_id=atom.atom_id,
        kind=CheckKind.ALGEBRAIC_SANITY,
        status=status,
        summary=summary,
        evidence=evidence,
        confidence=confidence,
        raw_details=raw_details,
    )


def _check_equation(eq: EquationBlock) -> dict:
    latex = eq.latex.strip()
    try:
        expr = _parse(latex)
    except Exception as exc:  # noqa: BLE001
        return {"status": "SKIPPED", "detail": f"parse exception: {exc}", "confidence": 0.2}

    if expr is None:
        return {"status": "SKIPPED", "detail": "could not parse latex", "confidence": 0.2}

    try:
        if isinstance(expr, sympy.core.relational.Relational):
            return _check_relational(expr)
        if "=" in latex and not any(op in latex for op in ("==", "<=", ">=")):
            lhs_str, rhs_str = latex.split("=", 1)
            lhs = _parse(lhs_str.strip())
            rhs = _parse(rhs_str.strip())
            if lhs is None or rhs is None:
                return {
                    "status": "SKIPPED",
                    "detail": "could not parse both sides of identity",
                    "confidence": 0.2,
                }
            return _check_identity(lhs, rhs)
        return {
            "status": "SKIPPED",
            "detail": "no relation to verify (bare expression)",
            "confidence": 0.1,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "SKIPPED", "detail": f"sympy raised: {exc}", "confidence": 0.2}


def _parse(s: str):
    text = s.strip()
    if not text:
        return None
    try:
        return parse_latex(text)
    except Exception:
        pass
    try:
        return sympify(text, evaluate=False)
    except Exception:
        return None


def _check_identity(lhs, rhs) -> dict:
    try:
        diff = simplify(lhs - rhs)
    except Exception as exc:  # noqa: BLE001
        return {"status": "SKIPPED", "detail": f"simplify raised: {exc}", "confidence": 0.2}
    if diff == 0:
        return {"status": "PASSED", "detail": "LHS - RHS simplifies to 0", "confidence": 0.85}
    return {"status": "FAILED", "detail": f"LHS - RHS = {diff}", "confidence": 0.85}


def _check_relational(rel) -> dict:
    if isinstance(rel, sympy.Eq):
        return _check_identity(rel.lhs, rel.rhs)

    free = list(rel.free_symbols)
    if not free:
        try:
            value = bool(rel)
        except Exception as exc:  # noqa: BLE001
            return {"status": "SKIPPED", "detail": f"bool(rel) raised: {exc}", "confidence": 0.2}
        return (
            {"status": "PASSED", "detail": "inequality is true", "confidence": 0.85}
            if value
            else {"status": "FAILED", "detail": "inequality is false", "confidence": 0.85}
        )
    try:
        reduced = sympy.reduce_inequalities(rel, free)
    except Exception as exc:  # noqa: BLE001
        return {"status": "SKIPPED", "detail": f"reduce raised: {exc}", "confidence": 0.2}
    if reduced == sympy.true:
        return {
            "status": "PASSED",
            "detail": "inequality holds universally",
            "confidence": 0.7,
        }
    if reduced == sympy.false:
        return {
            "status": "FAILED",
            "detail": "inequality never holds",
            "confidence": 0.85,
        }
    return {
        "status": "SKIPPED",
        "detail": f"holds conditionally: {reduced}",
        "confidence": 0.3,
    }
