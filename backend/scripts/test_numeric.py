"""Smoke test for NumericAdversaryAgent — no real OpenAI calls.

Usage (from backend/):
    .venv/bin/python scripts/test_numeric.py

Drives three claims through a fake OpenAI client:
    1. true universal claim (passes)            -> status="passed"
    2. false universal claim (counterexample)   -> status="failed"
    3. non-universal claim                       -> status="inconclusive"
    4. unsafe predicate (sandbox rejection)      -> status="inconclusive"
"""
from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext  # noqa: E402
from agents.numeric_adversary import NumericAdversaryAgent  # noqa: E402
from models import ClaimUnit  # noqa: E402


@dataclass
class _FakeMessage:
    content: str


@dataclass
class _FakeChoice:
    message: _FakeMessage


@dataclass
class _FakeResponse:
    choices: List[_FakeChoice]


class _FakeCompletions:
    def __init__(self, payloads: List[str]) -> None:
        self._payloads = list(payloads)

    async def create(self, **_kwargs) -> _FakeResponse:
        if not self._payloads:
            raise RuntimeError("ran out of fake payloads")
        return _FakeResponse(choices=[_FakeChoice(message=_FakeMessage(content=self._payloads.pop(0)))])


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeOpenAI:
    def __init__(self, payloads: List[str]) -> None:
        self.chat = _FakeChat(_FakeCompletions(payloads))


def _claim(claim_id: str, text: str) -> ClaimUnit:
    return ClaimUnit(
        claim_id=claim_id,
        text=text,
        claim_type="proposition",
        section="test",
        equations=[],
        citations=[],
        dependencies=[],
    )


CASES = [
    {
        "name": "true bound: x^2 + 1 > 0 on [-10, 10]",
        "claim": _claim("c1", "For all x in [-10, 10], x^2 + 1 > 0."),
        "payload": json.dumps({
            "is_universal": True,
            "predicate": "lambda x: x*x + 1 > 0",
            "domain": [-10.0, 10.0],
            "explanation": "trivially positive",
        }),
        "expect_status": "passed",
    },
    {
        "name": "false bound: sin(x) >= 0.5 on [-3.14, 3.14]",
        "claim": _claim("c2", "For every x in [-pi, pi], sin(x) >= 0.5."),
        "payload": json.dumps({
            "is_universal": True,
            "predicate": "lambda x: np.sin(x) >= 0.5",
            "domain": [-3.14159, 3.14159],
            "explanation": "claim is false near 0 and negatives",
        }),
        "expect_status": "failed",
    },
    {
        "name": "non-universal claim",
        "claim": _claim("c3", "The transformer outperforms RNNs on translation."),
        "payload": json.dumps({
            "is_universal": False,
            "explanation": "no numeric quantifier",
        }),
        "expect_status": "inconclusive",
    },
    {
        "name": "unsafe predicate (sandbox should reject)",
        "claim": _claim("c4", "For all x in [0, 1], something."),
        "payload": json.dumps({
            "is_universal": True,
            "predicate": "lambda x: __import__('os').system('echo pwn') or True",
            "domain": [0.0, 1.0],
            "explanation": "malicious",
        }),
        "expect_status": "inconclusive",
    },
]


async def _main() -> int:
    fake = _FakeOpenAI([c["payload"] for c in CASES])
    agent = NumericAdversaryAgent(client=fake)

    failures = 0
    for case in CASES:
        ctx = AgentContext(job_id="test", claim=case["claim"])
        result = await agent.run(ctx)
        inner_status = result.output.get("status")
        passed = inner_status == case["expect_status"]
        marker = "OK " if passed else "FAIL"
        print(f"[{marker}] {case['name']!r}")
        print(f"      agent_status={result.status} inner_status={inner_status} "
              f"confidence={result.confidence}")
        print(f"      evidence: {result.output.get('evidence')[:120]}")
        if not passed:
            failures += 1
            print(f"      expected inner_status={case['expect_status']!r}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
