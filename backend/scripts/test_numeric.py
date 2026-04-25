"""Offline numeric probe test with a mocked OpenAI client."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from checks.numeric_probe import run_numeric_probe  # noqa: E402
from models import AtomImportance, CheckStatus, ResearchAtom, ResearchAtomType, SourceSpan  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom(text: str) -> ResearchAtom:
    return ResearchAtom(
        atom_id="atom_num_001",
        paper_id="mock-paper",
        atom_type=ResearchAtomType.PROPOSITION,
        text=text,
        source_span=SourceSpan(
            paper_id="mock-paper",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=1.0,
        importance=AtomImportance.HIGH,
    )


class _FakeCompletions:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def create(self, **_kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(self.payload))
                )
            ]
        )


class _FakeOpenAI:
    def __init__(self, payload: dict) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions(payload))


async def main_async() -> None:
    no_counterexample = await run_numeric_probe(
        _atom("For every real x, x^2 >= 0."),
        client=_FakeOpenAI(
            {
                "is_universal": True,
                "predicate": "lambda x: x*x >= 0",
                "domain": [-10, 10],
                "explanation": "single-variable universal inequality",
            }
        ),
    )
    _assert(
        no_counterexample.status == CheckStatus.NO_COUNTEREXAMPLE_FOUND,
        f"expected no counterexample, got {no_counterexample.status}: {no_counterexample.summary}",
    )

    counterexample = await run_numeric_probe(
        _atom("For every real x, x^2 < 0."),
        client=_FakeOpenAI(
            {
                "is_universal": True,
                "predicate": "lambda x: x*x < 0",
                "domain": [-10, 10],
                "explanation": "false universal inequality",
            }
        ),
    )
    _assert(
        counterexample.status == CheckStatus.COUNTEREXAMPLE_FOUND,
        f"expected counterexample, got {counterexample.status}: {counterexample.summary}",
    )


def main() -> int:
    asyncio.run(main_async())
    print("numeric probe tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
