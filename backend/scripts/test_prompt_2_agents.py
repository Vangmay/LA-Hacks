"""Offline Prompt 2.1-2.4 test using ClaimUnits derived from TeX parsing.

No network calls and no OpenAI calls are made.
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

from agents.attacker import AttackerAgent  # noqa: E402
from agents.base import AgentContext, AgentResult  # noqa: E402
from agents.defender import DefenderAgent  # noqa: E402
from agents.numeric_adversary import NumericAdversaryAgent  # noqa: E402
from agents.symbolic_verifier import SymbolicVerifierAgent  # noqa: E402
from agents.tex_parser import parse_tex_text  # noqa: E402
from models import ClaimUnit  # noqa: E402


SAMPLE_TEX = r"""
\documentclass{article}
\title{Prompt Two Test}
\begin{document}
\section{Main}
\begin{theorem}
For every $x$ in $[-1,1]$, $x*x >= 0$.
\end{theorem}
\begin{equation}
x + 1 = x + 1
\end{equation}
The statement follows from elementary algebra \cite{alg}.
\begin{thebibliography}{9}
\bibitem{alg} Algebra reference.
\end{thebibliography}
\end{document}
"""


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
    def __init__(self, payloads: List[str], repeat_last: bool = False) -> None:
        self._payloads = list(payloads)
        self._repeat_last = repeat_last
        self._last = payloads[-1] if payloads else "{}"

    async def create(self, **_kwargs) -> _FakeResponse:
        if self._payloads:
            payload = self._payloads.pop(0)
            self._last = payload
        elif self._repeat_last:
            payload = self._last
        else:
            raise RuntimeError("ran out of fake payloads")
        return _FakeResponse(choices=[_FakeChoice(message=_FakeMessage(content=payload))])


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeOpenAI:
    def __init__(self, payloads: List[str], repeat_last: bool = False) -> None:
        self.chat = _FakeChat(_FakeCompletions(payloads, repeat_last=repeat_last))


class _FakeChallengeAgent:
    def __init__(self, agent_id: str, text: str) -> None:
        self.agent_id = agent_id
        self._text = text

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else ""
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output={
                "challenges": [
                    {
                        "challenge_id": f"ch_{claim_id}_{self.agent_id}",
                        "claim_id": claim_id,
                        "attacker_agent": self.agent_id,
                        "challenge_text": self._text,
                        "supporting_evidence": [self.agent_id],
                    }
                ]
            },
            confidence=0.8,
        )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _claim_from_tex() -> ClaimUnit:
    parsed = parse_tex_text(SAMPLE_TEX)
    equation = parsed["equations"][0]["latex"]
    _assert(equation == "x + 1 = x + 1", f"unexpected equation: {equation!r}")
    return ClaimUnit(
        claim_id="claim_001",
        text="For every x in [-1,1], x*x >= 0.",
        claim_type="theorem",
        section="Main",
        equations=[equation],
        citations=["alg"],
        dependencies=[],
    )


async def main_async() -> None:
    claim = _claim_from_tex()

    symbolic_result = await SymbolicVerifierAgent().run(
        AgentContext(job_id="prompt-2-test", claim=claim)
    )
    _assert(symbolic_result.status == "success", "symbolic agent did not return success")
    _assert(symbolic_result.output["tier"] == "symbolic", "symbolic tier missing")
    _assert(
        symbolic_result.output["status"] in {"passed", "failed", "inconclusive"},
        "symbolic status invalid",
    )

    numeric_payload = json.dumps(
        {
            "is_universal": True,
            "predicate": "lambda x: x*x >= 0",
            "domain": [-1, 1],
            "explanation": "direct scalar predicate",
        }
    )
    numeric_result = await NumericAdversaryAgent(client=_FakeOpenAI([numeric_payload])).run(
        AgentContext(job_id="prompt-2-test", claim=claim)
    )
    _assert(numeric_result.output["tier"] == "numeric", "numeric tier missing")
    _assert(numeric_result.output["status"] == "passed", numeric_result.output["evidence"])

    attacker_payload = json.dumps(
        {
            "challenges": [
                {
                    "challenge_text": "Main mocked challenge",
                    "supporting_evidence": ["symbolic result considered"],
                }
            ]
        }
    )
    attacker = AttackerAgent(
        client=_FakeOpenAI([attacker_payload]),
        counterexample_agent=_FakeChallengeAgent(
            "counterexample_search",
            "Mocked counterexample challenge",
        ),
        citation_gap_agent=_FakeChallengeAgent(
            "citation_gap",
            "Mocked citation challenge",
        ),
    )
    attacker_result = await attacker.run(
        AgentContext(
            job_id="prompt-2-test",
            claim=claim,
            extra={"verification_results": [symbolic_result.output, numeric_result.output]},
        )
    )
    challenges = attacker_result.output["challenges"]
    _assert(attacker_result.status == "success", "attacker failed")
    _assert(len(challenges) == 3, f"expected 3 challenges, got {len(challenges)}")
    _assert(challenges[0]["challenge_id"] == "ch_claim_001_001", "main challenge id wrong")
    _assert(challenges[1]["challenge_id"] == "ch_claim_001_sub_001", "sub challenge id wrong")
    _assert(challenges[2]["challenge_id"] == "ch_claim_001_sub_002", "sub challenge id wrong")

    defender_payload = json.dumps(
        {
            "rebuttal_text": "The challenge is addressed by the stated algebraic scope.",
            "supporting_evidence": ["x*x is nonnegative on the sampled domain"],
        }
    )
    defender_result = await DefenderAgent(
        client=_FakeOpenAI([defender_payload], repeat_last=True)
    ).run(
        AgentContext(
            job_id="prompt-2-test",
            claim=claim,
            extra={"challenges": challenges},
        )
    )
    rebuttals = defender_result.output["rebuttals"]
    _assert(defender_result.status == "success", "defender failed")
    _assert(len(rebuttals) == len(challenges), "defender did not answer every challenge")
    _assert(
        {r["challenge_id"] for r in rebuttals}
        == {challenge["challenge_id"] for challenge in challenges},
        "rebuttal challenge ids do not match",
    )


def main() -> int:
    asyncio.run(main_async())
    print("offline Prompt 2.1-2.4 agent tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
