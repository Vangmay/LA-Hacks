"""Numeric counterexample probe.

Takes a `ResearchAtom`, asks the LLM for a Python lambda predicate +
domain that captures any universal numeric quantifier in the atom, then
samples + runs `scipy.optimize.minimize` on the negated predicate. Outputs
a `CheckResult` with kind `NUMERIC_COUNTEREXAMPLE_PROBE`.

Status semantics (per v0.4 plan):
- COUNTEREXAMPLE_FOUND: a sampled or optimizer-found point falsifies.
- NO_COUNTEREXAMPLE_FOUND: 1000 samples + optimizer restarts found nothing.
- NOT_APPLICABLE: the atom has no universal numeric quantifier.
- INCONCLUSIVE: parsing failed, predicate raised everywhere, etc.

Confidence is honest: NO_COUNTEREXAMPLE_FOUND is 0.4 — not the same as
"verified".
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import uuid
from typing import Any, Callable, Optional

import numpy as np
from openai import AsyncOpenAI
from scipy.optimize import minimize

from config import settings
from core.openai_client import make_async_openai
from models import (
    CheckKind,
    CheckResult,
    CheckStatus,
    Evidence,
    EvidenceSourceType,
    ResearchAtom,
)

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
    "Given an atom, decide if it contains a universally quantified numeric "
    "assertion. If so, return a single-arg lambda that returns True when "
    "the condition holds and False otherwise, plus the domain. Use only "
    "numpy (`np`), math, and basic Python operators. Never import. "
    "For equality claims use np.isclose(LHS, RHS, atol=1e-9). For strict "
    "inequalities use </>; for non-strict <=/>=."
)
_USER_PROMPT = """Atom text:
\"\"\"
{text}
\"\"\"

Equations attached to the atom (latex):
{equations}

Return ONLY a JSON object:
{{
  "is_universal": true | false,
  "predicate": "lambda x: ...",
  "domain": [low, high],
  "explanation": "<one short sentence>"
}}

Rules:
- Predicate MUST be a single-arg lambda over `x` (a scalar float).
- The predicate must return truthy when the claim holds at x, falsy when it
  fails.
- Use `np.` for math.
- Domain bounds must be finite numbers. Pick a reasonable range when not
  stated (e.g. [-10, 10]).
- If the claim is multi-variable, asymptotic, or has no clear quantifier,
  set is_universal=false.
"""


async def run_numeric_probe(
    atom: ResearchAtom,
    *,
    client: Optional[AsyncOpenAI] = None,
) -> CheckResult:
    check_id = f"check_num_{atom.atom_id}_{uuid.uuid4().hex[:6]}"
    cli = client or make_async_openai()

    try:
        spec, parse_error = await _extract_predicate(cli, atom)
    except Exception as exc:  # noqa: BLE001
        logger.exception("numeric_probe predicate extraction failed for %s", atom.atom_id)
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.INCONCLUSIVE,
            summary=f"predicate extractor error: {exc}",
            confidence=0.2,
            raw_details={"error": str(exc)},
        )

    if parse_error:
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.INCONCLUSIVE,
            summary=parse_error,
            confidence=0.2,
            raw_details={"parse_error": parse_error},
        )

    if not spec or not spec.get("is_universal"):
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.NOT_APPLICABLE,
            summary=(spec or {}).get("explanation") or "no universal numeric quantifier",
            confidence=0.1,
            raw_details={"spec": spec or {}},
        )

    predicate_str = (spec.get("predicate") or "").strip()
    domain = spec.get("domain") or []
    safety_error = _validate_lambda(predicate_str, domain)
    if safety_error:
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.INCONCLUSIVE,
            summary=safety_error,
            confidence=0.2,
            raw_details={"predicate": predicate_str, "domain": domain},
        )

    try:
        predicate = _compile_lambda(predicate_str)
    except Exception as exc:  # noqa: BLE001
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.INCONCLUSIVE,
            summary=f"lambda compile failed: {exc}",
            confidence=0.2,
            raw_details={"predicate": predicate_str},
        )

    low, high = float(domain[0]), float(domain[1])

    try:
        verdict_label, detail = await asyncio.wait_for(
            asyncio.to_thread(_search_counterexample, predicate, low, high),
            timeout=_NUMERIC_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.INCONCLUSIVE,
            summary="numeric search timed out at 5s",
            confidence=0.3,
            raw_details={"predicate": predicate_str, "domain": [low, high]},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("numeric search raised for %s", atom.atom_id)
        return _result(
            check_id=check_id,
            atom=atom,
            status=CheckStatus.INCONCLUSIVE,
            summary=f"numeric search error: {exc}",
            confidence=0.2,
            raw_details={"predicate": predicate_str, "domain": [low, high]},
        )

    if verdict_label == "counterexample":
        status = CheckStatus.COUNTEREXAMPLE_FOUND
        confidence = 0.9
    elif verdict_label == "none":
        status = CheckStatus.NO_COUNTEREXAMPLE_FOUND
        confidence = 0.4
    else:
        status = CheckStatus.INCONCLUSIVE
        confidence = 0.3

    return _result(
        check_id=check_id,
        atom=atom,
        status=status,
        summary=detail,
        confidence=confidence,
        raw_details={
            "predicate": predicate_str,
            "domain": [low, high],
            "samples": _NUM_RANDOM_SAMPLES,
            "restarts": _NUM_OPT_RESTARTS,
        },
    )


# ---------------------------------------------------------------------------


async def _extract_predicate(
    client: AsyncOpenAI,
    atom: ResearchAtom,
) -> tuple[Optional[dict], Optional[str]]:
    eq_block = (
        "\n".join(f"- {eq.latex}" for eq in atom.equations) if atom.equations else "(none)"
    )
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _USER_PROMPT.format(text=atom.text, equations=eq_block),
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=400,
    )
    raw = response.choices[0].message.content or ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"could not parse predicate JSON: {exc}"
    if not isinstance(data, dict):
        return None, "predicate JSON was not an object"
    return data, None


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
    safe_globals: dict[str, Any] = {
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
) -> tuple[str, str]:
    probe_xs = (0.5 * (low + high), low + 1e-3, high - 1e-3)
    probe_errors: list[str] = []
    for px in probe_xs:
        try:
            predicate(float(px))
        except Exception as exc:  # noqa: BLE001
            probe_errors.append(f"{type(exc).__name__}: {exc}")
    if len(probe_errors) == len(probe_xs) and len(set(probe_errors)) == 1:
        return "inconclusive", f"predicate raises everywhere: {probe_errors[0]}"

    rng = np.random.default_rng(0)
    samples = rng.uniform(low, high, _NUM_RANDOM_SAMPLES)
    for x in samples:
        try:
            result = predicate(float(x))
        except Exception as exc:  # noqa: BLE001
            return "counterexample", f"predicate raised {type(exc).__name__} at x={float(x):.6g}: {exc}"
        if not bool(result):
            return "counterexample", f"counterexample x={float(x):.6g} returned {result!r}"

    def negated(arr: np.ndarray) -> float:
        x = float(arr[0])
        if x < low or x > high:
            return 1.0
        try:
            val = predicate(x)
        except Exception:  # noqa: BLE001
            return -1.0
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
        except Exception:  # noqa: BLE001
            continue
        if res.fun < best_val:
            best_val = float(res.fun)
            best_x = float(res.x[0])

    if best_x is not None and best_val < 0:
        try:
            actual = predicate(best_x)
        except Exception as exc:  # noqa: BLE001
            return "counterexample", f"optimizer hit raise at x={best_x:.6g}: {exc}"
        if not bool(actual):
            return "counterexample", f"optimizer counterexample x={best_x:.6g} returned {actual!r}"

    return "none", (
        f"no counterexample after {_NUM_RANDOM_SAMPLES} samples + "
        f"{_NUM_OPT_RESTARTS} optimizer restarts on [{low}, {high}]"
    )


def _result(
    *,
    check_id: str,
    atom: ResearchAtom,
    status: CheckStatus,
    summary: str,
    confidence: float,
    raw_details: dict,
) -> CheckResult:
    evidence_text = f"numeric_probe ({status.value}): {summary}"
    return CheckResult(
        check_id=check_id,
        atom_id=atom.atom_id,
        kind=CheckKind.NUMERIC_COUNTEREXAMPLE_PROBE,
        status=status,
        summary=summary,
        evidence=[
            Evidence(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                source_type=EvidenceSourceType.NUMERIC_PROBE,
                text=evidence_text,
                paper_id=atom.paper_id,
                atom_id=atom.atom_id,
                check_id=check_id,
                confidence=confidence,
            )
        ],
        confidence=confidence,
        raw_details=raw_details,
    )
