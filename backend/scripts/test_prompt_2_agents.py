"""Offline check/challenge/defense/verdict test for one ResearchAtom.

No network calls and no real OpenAI calls are made.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext  # noqa: E402
from agents.challenge_agent import ChallengeAgent  # noqa: E402
from agents.defense_agent import DefenseAgent  # noqa: E402
from agents.verdict_aggregator import aggregate_verdict  # noqa: E402
from checks.algebraic_sanity import run_algebraic_sanity  # noqa: E402
from checks.numeric_probe import run_numeric_probe  # noqa: E402
from ingestion.tex_parser import parse_tex  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    Challenge,
    CheckStatus,
    PaperSource,
    Rebuttal,
    ResearchAtom,
    ResearchAtomType,
    SourceKind,
    SourceSpan,
    VerdictLabel,
)


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


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _paper():
    source = PaperSource(
        paper_id="prompt-two-test",
        source_kind=SourceKind.MANUAL_TEX,
        fetched_at=datetime.utcnow(),
        content_hash=hashlib.md5(SAMPLE_TEX.encode("utf-8")).hexdigest()[:16],
    )
    return parse_tex(SAMPLE_TEX, source)


def _atom() -> ResearchAtom:
    text = "For every x in [-1,1], x*x >= 0."
    return ResearchAtom(
        atom_id="atom_001",
        paper_id="prompt-two-test",
        atom_type=ResearchAtomType.THEOREM,
        text=text,
        section_heading="Main",
        source_span=SourceSpan(
            paper_id="prompt-two-test",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=0.95,
        importance=AtomImportance.HIGH,
    )


async def main_async() -> None:
    paper = _paper()
    atom = _atom().model_copy(update={"equations": paper.equations, "citations": paper.bibliography})

    algebraic = run_algebraic_sanity(atom, paper)
    _assert(
        algebraic.status in {CheckStatus.PASSED, CheckStatus.INCONCLUSIVE},
        f"unexpected algebraic status: {algebraic.status}",
    )

    numeric = await run_numeric_probe(
        atom,
        client=_FakeOpenAI(
            {
                "is_universal": True,
                "predicate": "lambda x: x*x >= 0",
                "domain": [-1, 1],
                "explanation": "single-variable universal inequality",
            }
        ),
    )
    _assert(
        numeric.status == CheckStatus.NO_COUNTEREXAMPLE_FOUND,
        f"numeric probe failed: {numeric.status} {numeric.summary}",
    )

    challenge_result = await ChallengeAgent(
        client=_FakeOpenAI(
            {
                "challenges": [
                    {
                        "challenge_type": "notation_ambiguity",
                        "severity": "low",
                        "challenge_text": "`x*x` is programming notation and should be tied to multiplication.",
                        "evidence": [{"text": atom.text, "source": "atom_text"}],
                        "falsifiable_test": "Check the surrounding notation.",
                        "confidence": 0.5,
                    }
                ]
            }
        )
    ).run(AgentContext(job_id="prompt-2-test", parsed_paper=paper, atom=atom, checks=[algebraic, numeric]))
    _assert(challenge_result.status == "success", f"challenge failed: {challenge_result.error}")
    challenges = [Challenge.model_validate(c) for c in challenge_result.output["challenges"]]
    _assert(len(challenges) == 1, "expected one challenge")

    defense_result = await DefenseAgent(
        client=_FakeOpenAI(
            {
                "response_type": "resolves",
                "rebuttal_text": "The source uses the expression only as ordinary multiplication.",
                "evidence": [{"text": atom.text, "source": "atom_text"}],
                "confidence": 0.8,
            }
        )
    ).run(
        AgentContext(
            job_id="prompt-2-test",
            parsed_paper=paper,
            atom=atom,
            checks=[algebraic, numeric],
            challenges=challenges,
        )
    )
    rebuttals = [Rebuttal.model_validate(r) for r in defense_result.output["rebuttals"]]
    _assert(len(rebuttals) == 1, "defense did not answer challenge")

    verdict = aggregate_verdict(atom, [algebraic, numeric], challenges, rebuttals)
    _assert(
        verdict.label == VerdictLabel.NO_OBJECTION_FOUND,
        f"unexpected verdict: {verdict.label} {verdict.rationale}",
    )


def main() -> int:
    asyncio.run(main_async())
    print("offline check/challenge/defense/verdict test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
