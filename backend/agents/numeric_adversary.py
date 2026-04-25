"""NumericAdversaryAgent — search for numeric counterexamples to a claim.

Pipeline per claim:
    1. GPT-4o extracts a Python lambda predicate + numeric domain.
    2. Sandbox-check the lambda string (reject anything that touches imports,
       dunders, exec, etc.).
    3. Sample 1000 points uniformly in the domain — any False/exception
       counts as a counterexample.
    4. scipy.optimize.minimize the negated predicate from a few starts to
       try to drive it below zero.
    5. Whole numeric pass capped at 5 seconds via asyncio.wait_for.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from openai import AsyncOpenAI
from scipy.optimize import minimize

from config import settings

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_NUMERIC_TIMEOUT_SECONDS = 5.0
_NUM_RANDOM_SAMPLES = 1000
_NUM_OPT_RESTARTS = 5

_UNSAFE_TOKENS = (
    "import",
    "__",
    "exec",
    "eval",
    "open(",
    "compile(",
    "globals(",
    "locals(",
    "getattr",
    "setattr",
    "delattr",
    "os.",
    "sys.",
    "subprocess",
    "input(",
    "exit(",
    "quit(",
    "breakpoint",
    "lambda:",
    "yield",
    "async ",
    "await ",
    ";",
    "`",
)

_LAMBDA_RE = re.compile(r"^\s*lambda\s+[A-Za-z_][A-Za-z_0-9]*\s*:\s*.+$", re.DOTALL)

_SYSTEM_PROMPT = (
    "You translate mathematical claims into testable Python predicates. "
    "Given a claim, decide if it contains a universally quantified numeric "
    "assertion of the form 'for all x in some domain, f(x) satisfies a "
    "numeric condition'. If so, return a Python lambda string that returns "
    "True when the condition holds and False otherwise, plus the domain. "
    "Use only numpy (`np`), math, and basic Python operators. Never import. "
    "CRITICAL: the lambda must take EXACTLY ONE scalar float argument `x`. "
    "If the claim is over multiple variables, or its truth depends on more "
    "than one independent quantity, set is_universal=false. "
    "For equality claims (LHS = RHS, LHS equals RHS, identities), "
    "NEVER use `==` (it fails on floating point). Always use "
    "`np.isclose(LHS, RHS, atol=1e-9)`. For strict inequalities use `<`/`>`; "
    "for non-strict use `<=`/`>=`."
)

_USER_PROMPT = """Claim text:
\"\"\"{claim_text}\"\"\"

Equations from the same paper that may be relevant:
{equations}

Return ONLY a JSON object with this exact schema:
{{
  "is_universal": true | false,
  "predicate": "lambda x: ...",        // omit or "" if is_universal is false
  "domain": [low, high],                // omit or [] if is_universal is false
  "explanation": "one short sentence"   // why this predicate captures the claim, or why it can't be tested numerically
}}

Rules:
- The predicate MUST be a single-arg lambda. The argument represents an arbitrary point in the domain.
- The predicate MUST return a Python truthy value when the claim holds at x and falsy when it fails. Strict inequalities count as `>` / `<`.
- Use `np.` for math (np.sin, np.exp, np.log, etc.). Do NOT import anything.
- If the claim is about discrete sequences, asymptotic behaviour, or has no clear numeric quantifier, set is_universal=false.
- Domain bounds must be finite numbers. Pick a reasonable finite range (e.g. [-10, 10] when not stated).
- Output ONLY the JSON object, no prose, no code fences.
"""


class NumericAdversaryAgent(BaseAgent):
    agent_id = "numeric_adversary"

    EMPTY_OUTPUT: Dict[str, Any] = {
        "tier": "numeric",
        "status": "inconclusive",
        "evidence": "",
        "confidence": 0.0,
    }

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        claim = context.claim
        if claim is None:
            return self._inconclusive(None, "no claim provided")

        try:
            spec, parse_error = await self._extract_predicate(claim.text, claim.equations)
        except Exception as e:
            logger.exception("Predicate extraction failed for %s", claim.claim_id)
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim.claim_id,
                status="error",
                output=_result_dict("inconclusive", f"extractor error: {e}", 0.0),
                confidence=0.0,
                error=str(e),
            )

        if parse_error:
            return self._inconclusive(claim.claim_id, parse_error)
        if not spec or not spec.get("is_universal"):
            why = (spec or {}).get("explanation") or "no universal numeric quantifier"
            return self._inconclusive(claim.claim_id, why)

        predicate_str = (spec.get("predicate") or "").strip()
        domain = spec.get("domain") or []
        safety_error = _validate_lambda(predicate_str, domain)
        if safety_error:
            return self._inconclusive(claim.claim_id, safety_error)

        try:
            predicate = _compile_lambda(predicate_str)
        except Exception as e:
            return self._inconclusive(claim.claim_id, f"lambda compile failed: {e}")

        low, high = float(domain[0]), float(domain[1])

        try:
            verdict, evidence = await asyncio.wait_for(
                asyncio.to_thread(_search_counterexample, predicate, low, high),
                timeout=_NUMERIC_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return self._inconclusive(claim.claim_id, "numeric search timed out at 5s")
        except Exception as e:
            logger.exception("Numeric search failed for %s", claim.claim_id)
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim.claim_id,
                status="error",
                output=_result_dict("inconclusive", f"numeric error: {e}", 0.0),
                confidence=0.0,
                error=str(e),
            )

        confidence = 0.95 if verdict == "failed" else 0.7 if verdict == "passed" else 0.3
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim.claim_id,
            status="success",
            output=_result_dict(verdict, evidence, confidence),
            confidence=confidence,
        )

    async def _extract_predicate(
        self,
        claim_text: str,
        equations: List[str],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        eq_block = "\n".join(f"- {e}" for e in (equations or [])) or "(none)"
        client = self._get_client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_PROMPT.format(
                    claim_text=claim_text,
                    equations=eq_block,
                )},
            ],
            response_format={"type": "json_object"},
            max_tokens=400,
        )
        raw = response.choices[0].message.content or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return None, f"could not parse predicate JSON: {e}"
        if not isinstance(data, dict):
            return None, "predicate JSON was not an object"
        return data, None

    def _inconclusive(self, claim_id: Optional[str], reason: str) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="inconclusive",
            output=_result_dict("inconclusive", reason, 0.3),
            confidence=0.3,
        )


def _result_dict(status: str, evidence: str, confidence: float) -> Dict[str, Any]:
    return {
        "tier": "numeric",
        "status": status,
        "evidence": evidence,
        "confidence": confidence,
    }


def _validate_lambda(predicate_str: str, domain: Any) -> Optional[str]:
    if not predicate_str:
        return "no predicate string"
    if not _LAMBDA_RE.match(predicate_str):
        return "predicate is not a single-arg lambda"
    lower = predicate_str.lower()
    for token in _UNSAFE_TOKENS:
        if token in lower:
            return f"predicate contains unsafe token: {token!r}"
    if not (isinstance(domain, list) and len(domain) == 2):
        return "domain must be [low, high]"
    try:
        low, high = float(domain[0]), float(domain[1])
    except (TypeError, ValueError):
        return "domain entries must be numbers"
    if not (math.isfinite(low) and math.isfinite(high)):
        return "domain bounds must be finite"
    if low >= high:
        return "domain low must be < high"
    return None


def _compile_lambda(predicate_str: str) -> Callable[[float], Any]:
    safe_globals: Dict[str, Any] = {
        "__builtins__": {
            "abs": abs,
            "min": min,
            "max": max,
            "len": len,
            "range": range,
            "float": float,
            "int": int,
            "bool": bool,
            "True": True,
            "False": False,
            "None": None,
        },
        "np": np,
        "math": math,
    }
    return eval(predicate_str, safe_globals, {})  # noqa: S307 — sandboxed above


def _search_counterexample(
    predicate: Callable[[float], Any],
    low: float,
    high: float,
) -> Tuple[str, str]:
    """Run sampling + scipy search. Returns (verdict, evidence)."""
    # Probe at midpoint, low, and high to distinguish a malformed predicate
    # (raises everywhere with the same shape error) from a genuine domain
    # raise (e.g. log(0)). If all three probes raise with the same exception
    # type and message, treat as inconclusive.
    probe_xs = (0.5 * (low + high), low + 1e-3, high - 1e-3)
    probe_errors: List[str] = []
    for px in probe_xs:
        try:
            predicate(float(px))
        except Exception as e:
            probe_errors.append(f"{type(e).__name__}: {e}")
    if len(probe_errors) == len(probe_xs) and len(set(probe_errors)) == 1:
        return "inconclusive", f"predicate raises everywhere: {probe_errors[0]}"

    rng = np.random.default_rng(0)
    samples = rng.uniform(low, high, _NUM_RANDOM_SAMPLES)
    for x in samples:
        try:
            result = predicate(float(x))
        except Exception as e:
            return "failed", f"predicate raised {type(e).__name__} at x={float(x):.6g}: {e}"
        if not bool(result):
            return "failed", f"counterexample x={float(x):.6g} returned {result!r}"

    # scipy search: try to drive predicate -> False by minimizing -float(predicate(x)).
    def negated(x_arr: np.ndarray) -> float:
        x = float(x_arr[0])
        if x < low or x > high:
            return 1.0  # outside domain — push optimizer back inside
        try:
            val = predicate(x)
        except Exception:
            return -1.0  # treat raise as failure region
        try:
            return -float(val)
        except (TypeError, ValueError):
            return -1.0 if not bool(val) else 1.0

    starts = rng.uniform(low, high, _NUM_OPT_RESTARTS)
    best_val = math.inf
    best_x: Optional[float] = None
    for x0 in starts:
        try:
            res = minimize(
                negated,
                x0=np.array([float(x0)]),
                method="Nelder-Mead",
                options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 200},
            )
        except Exception:
            continue
        if res.fun < best_val:
            best_val = float(res.fun)
            best_x = float(res.x[0])

    if best_x is not None and best_val < 0:
        try:
            actual = predicate(best_x)
        except Exception as e:
            return "failed", f"optimizer hit raise at x={best_x:.6g}: {e}"
        if not bool(actual):
            return "failed", f"optimizer counterexample x={best_x:.6g} returned {actual!r}"

    return "passed", (
        f"no counterexample after {_NUM_RANDOM_SAMPLES} samples + "
        f"{_NUM_OPT_RESTARTS} optimizer restarts on [{low}, {high}]"
    )
