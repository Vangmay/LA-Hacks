"""Offline challenge/defense agent test with mocked OpenAI clients."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext  # noqa: E402
from agents.challenge_agent import ChallengeAgent  # noqa: E402
from agents.defense_agent import DefenseAgent  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    Challenge,
    ChallengeType,
    Rebuttal,
    RebuttalType,
    ResearchAtom,
    ResearchAtomType,
    Severity,
    SourceSpan,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom() -> ResearchAtom:
    text = "For every real x, x^2 >= 0."
    return ResearchAtom(
        atom_id="atom_adv_001",
        paper_id="mock-paper",
        atom_type=ResearchAtomType.THEOREM,
        text=text,
        section_heading="Main",
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
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(self.payload)))]
        )


class _FakeOpenAI:
    def __init__(self, payload: dict) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions(payload))


async def main_async() -> None:
    atom = _atom()
    challenge_result = await ChallengeAgent(
        client=_FakeOpenAI(
            {
                "challenges": [
                    {
                        "challenge_type": "proof_gap",
                        "severity": "low",
                        "challenge_text": "The paper should state the real-valued domain explicitly.",
                        "evidence": [{"text": atom.text, "source": "atom_text"}],
                        "falsifiable_test": "Check whether the surrounding section defines x as real.",
                        "confidence": 0.6,
                    }
                ]
            }
        )
    ).run(AgentContext(job_id="adv-test", atom=atom))
    _assert(challenge_result.status == "success", f"challenge failed: {challenge_result.error}")
    challenges = [Challenge.model_validate(c) for c in challenge_result.output["challenges"]]
    _assert(challenges[0].challenge_type == ChallengeType.PROOF_GAP, "wrong challenge type")
    _assert(challenges[0].severity == Severity.LOW, "wrong challenge severity")

    defense_result = await DefenseAgent(
        client=_FakeOpenAI(
            {
                "response_type": "resolves",
                "rebuttal_text": "The atom itself says real x, so the challenged domain is explicit.",
                "evidence": [{"text": atom.text, "source": "atom_text"}],
                "confidence": 0.85,
            }
        )
    ).run(AgentContext(job_id="adv-test", atom=atom, challenges=challenges))
    _assert(defense_result.status == "success", f"defense failed: {defense_result.error}")
    rebuttals = [Rebuttal.model_validate(r) for r in defense_result.output["rebuttals"]]
    _assert(rebuttals[0].response_type == RebuttalType.RESOLVES, "wrong rebuttal type")
    _assert(rebuttals[0].confidence >= 0.8, "rebuttal confidence missing")


def main() -> int:
    asyncio.run(main_async())
    print("challenge/defense agent tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
