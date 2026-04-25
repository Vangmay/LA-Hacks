import logging
from typing import List

import sympy
from sympy import sympify, simplify
from sympy.parsing.latex import parse_latex

from .base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class SymbolicVerifierAgent(BaseAgent):
    agent_id = "symbolic_verifier"

    async def run(self, context: AgentContext) -> AgentResult:
        claim = context.claim
        claim_id = claim.claim_id if claim else None
        equations: List[str] = list(claim.equations) if claim else []

        if not equations:
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim_id,
                status="inconclusive",
                output={
                    "tier": "symbolic",
                    "status": "inconclusive",
                    "evidence": "no parseable equations found",
                    "confidence": 0.5,
                },
                confidence=0.5,
            )

        evidence_lines: List[str] = []
        passed = 0
        failed = 0

        for eq_str in equations:
            result = self._check_equation(eq_str)
            evidence_lines.append(f"{eq_str!r}: {result}")
            if result.startswith("PASSED"):
                passed += 1
            elif result.startswith("FAILED"):
                failed += 1
            # "SKIPPED" counts as neither

        evidence = "; ".join(evidence_lines)

        if failed > 0:
            status = "failed"
            confidence = 0.85
        elif passed > 0:
            status = "passed"
            confidence = 0.9
        else:
            status = "inconclusive"
            confidence = 0.5

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={
                "tier": "symbolic",
                "status": status,
                "evidence": evidence if evidence else "no parseable equations found",
                "confidence": confidence,
            },
            confidence=confidence,
        )

    def _check_equation(self, eq_str: str) -> str:
        """Try to verify one equation string. Returns a PASSED/FAILED/SKIPPED message."""
        try:
            # Try LaTeX parsing first, fall back to sympify
            expr = self._parse(eq_str)
            if expr is None:
                return f"SKIPPED — could not parse"

            # If the expression is a relational (Eq, Le, Ge, etc.)
            if isinstance(expr, sympy.core.relational.Relational):
                return self._check_relational(expr)

            # If the raw string contains "=" treat it as an identity LHS = RHS
            if "=" in eq_str and not any(op in eq_str for op in ["==", "<=", ">="]):
                parts = eq_str.split("=", 1)
                lhs = self._parse(parts[0].strip())
                rhs = self._parse(parts[1].strip())
                if lhs is None or rhs is None:
                    return "SKIPPED — could not parse both sides of identity"
                return self._check_identity(lhs, rhs)

            # Bare expression with no relation — nothing to verify
            return "SKIPPED — no relation to verify"

        except Exception as exc:
            logger.debug("symbolic_verifier: exception on %r: %s", eq_str, exc)
            return f"SKIPPED — exception: {exc}"

    def _parse(self, s: str):
        """Try LaTeX parse then sympify. Returns SymPy expression or None."""
        s = s.strip()
        # Try LaTeX
        try:
            return parse_latex(s)
        except Exception:
            pass
        # Try sympify
        try:
            return sympify(s, evaluate=False)
        except Exception:
            return None

    def _check_identity(self, lhs, rhs) -> str:
        try:
            diff = simplify(lhs - rhs)
            if diff == 0:
                return "PASSED — identity holds (LHS - RHS simplifies to 0)"
            else:
                return f"FAILED — identity does not hold (LHS - RHS = {diff})"
        except Exception as exc:
            return f"SKIPPED — simplify raised: {exc}"

    def _check_relational(self, rel) -> str:
        try:
            # For equalities, check LHS - RHS == 0
            if isinstance(rel, sympy.Eq):
                diff = simplify(rel.lhs - rel.rhs)
                if diff == 0:
                    return "PASSED — equality holds"
                return f"FAILED — equality does not hold (diff = {diff})"

            # For inequalities, attempt reduce_inequalities on free symbols
            free = list(rel.free_symbols)
            if not free:
                result = bool(rel)
                return "PASSED — inequality is true" if result else "FAILED — inequality is false"

            reduced = sympy.reduce_inequalities(rel, free)
            if reduced == sympy.true:
                return "PASSED — inequality holds universally"
            elif reduced == sympy.false:
                return "FAILED — inequality never holds"
            else:
                return f"SKIPPED — inequality holds conditionally: {reduced}"

        except Exception as exc:
            return f"SKIPPED — relational check raised: {exc}"
