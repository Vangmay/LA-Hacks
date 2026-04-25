"""Offline tests for the five Reader Mode agents.

No real OpenAI calls and no real HTTP requests are made.
"""
from __future__ import annotations

import asyncio
import json
import sys
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext  # noqa: E402
from agents.exercise_generator import ExerciseGeneratorAgent  # noqa: E402
from agents.explainer import ExplainerAgent  # noqa: E402
from agents.glossary_agent import GlossaryAgent  # noqa: E402
from agents.prerequisite_mapper import PrerequisiteMapperAgent  # noqa: E402
from agents.socratic_tutor import SocraticTutorAgent  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    CitationEntry,
    ResearchAtom,
    ResearchAtomType,
    SourceSpan,
)


# ---------------------------------------------------------------------------
# helpers

def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom() -> ResearchAtom:
    text = (
        "For every symmetric positive-definite matrix A in R^{n x n}, "
        "the spectral radius rho(A) equals the largest eigenvalue of A."
    )
    return ResearchAtom(
        atom_id="atom_reader_001",
        paper_id="reader-test-paper",
        atom_type=ResearchAtomType.THEOREM,
        text=text,
        section_heading="Preliminaries",
        source_span=SourceSpan(
            paper_id="reader-test-paper",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=0.95,
        importance=AtomImportance.HIGH,
    )


def _ctx(**extra) -> AgentContext:
    return AgentContext(job_id="reader-test", atom=_atom(), extra=extra)


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


# ---------------------------------------------------------------------------
# ExplainerAgent

async def test_explainer() -> None:
    payload = {
        "explanation": "A symmetric PD matrix has only positive eigenvalues. The spectral radius picks the largest.",
        "key_insight": "The spectral radius of a symmetric PD matrix is its largest eigenvalue.",
        "worked_example": "For A = [[2,0],[0,3]], rho(A) = 3.",
    }
    result = await ExplainerAgent(client=_FakeOpenAI(payload)).run(
        _ctx(comprehension_level="undergraduate")
    )
    _assert(result.status == "success", f"explainer status: {result.status} / {result.error}")
    _assert("explanation" in result.output, "explanation key missing")
    _assert("key_insight" in result.output, "key_insight key missing")
    _assert(result.output["worked_example"] is not None, "worked_example should be present")
    _assert(result.confidence > 0.5, "confidence too low")


async def test_explainer_missing_atom() -> None:
    ctx = AgentContext(job_id="reader-test")
    result = await ExplainerAgent(client=_FakeOpenAI({})).run(ctx)
    _assert(result.status == "error", "expected error when atom is missing")


# ---------------------------------------------------------------------------
# PrerequisiteMapperAgent

async def test_prerequisite_mapper() -> None:
    payload = {
        "prerequisites": [
            {
                "concept": "Spectral radius",
                "description": "The largest absolute eigenvalue of a matrix.",
                "resource_links": ["https://en.wikipedia.org/wiki/Spectral_radius"],
            },
            {
                "concept": "Positive-definite matrix",
                "description": "A symmetric matrix with all positive eigenvalues.",
                "resource_links": ["https://en.wikipedia.org/wiki/Definiteness_of_a_matrix"],
            },
        ]
    }

    # Mock httpx.AsyncClient so HEAD requests don't hit the network.
    mock_response = SimpleNamespace(status_code=200)

    async def _fake_head(url, **_kwargs):
        return mock_response

    fake_http = unittest.mock.AsyncMock()
    fake_http.head = _fake_head
    fake_http.__aenter__ = unittest.mock.AsyncMock(return_value=fake_http)
    fake_http.__aexit__ = unittest.mock.AsyncMock(return_value=False)

    with unittest.mock.patch("agents.prerequisite_mapper.httpx.AsyncClient", return_value=fake_http):
        result = await PrerequisiteMapperAgent(client=_FakeOpenAI(payload)).run(_ctx())

    _assert(result.status == "success", f"prereq status: {result.status} / {result.error}")
    prereqs = result.output.get("prerequisites", [])
    _assert(len(prereqs) == 2, f"expected 2 prerequisites, got {len(prereqs)}")
    _assert(prereqs[0]["concept"] == "Spectral radius", "wrong first concept")
    _assert(len(prereqs[0]["resource_links"]) == 1, "resource link missing")


async def test_prerequisite_mapper_404_fallback() -> None:
    payload = {
        "prerequisites": [
            {
                "concept": "Spectral norm",
                "description": "The largest singular value of a matrix.",
                "resource_links": ["https://en.wikipedia.org/wiki/Spectral_norm_nonexistent"],
            }
        ]
    }

    mock_404 = SimpleNamespace(status_code=404)

    async def _fake_head_404(url, **_kwargs):
        return mock_404

    fake_http = unittest.mock.AsyncMock()
    fake_http.head = _fake_head_404
    fake_http.__aenter__ = unittest.mock.AsyncMock(return_value=fake_http)
    fake_http.__aexit__ = unittest.mock.AsyncMock(return_value=False)

    with unittest.mock.patch("agents.prerequisite_mapper.httpx.AsyncClient", return_value=fake_http):
        result = await PrerequisiteMapperAgent(client=_FakeOpenAI(payload)).run(_ctx())

    prereqs = result.output.get("prerequisites", [])
    _assert(len(prereqs) == 1, "expected 1 prerequisite")
    link = prereqs[0]["resource_links"][0]
    _assert("Special:Search" in link, f"404 URL was not replaced with search URL: {link}")


async def test_prerequisite_mapper_atom_references_first() -> None:
    payload = {
        "prerequisites": [
            {
                "concept": "Spectral radius",
                "description": "The largest absolute eigenvalue of a matrix.",
                "resource_links": ["https://en.wikipedia.org/wiki/Spectral_radius"],
            }
        ]
    }

    mock_response = SimpleNamespace(status_code=200)

    async def _fake_head(url, **_kwargs):
        return mock_response

    fake_http = unittest.mock.AsyncMock()
    fake_http.head = _fake_head
    fake_http.__aenter__ = unittest.mock.AsyncMock(return_value=fake_http)
    fake_http.__aexit__ = unittest.mock.AsyncMock(return_value=False)

    atom = _atom().model_copy(
        update={
            "citations": [
                CitationEntry(
                    citation_id="cite_001",
                    key="perron1907",
                    title="Zur Theorie der Matrices",
                    doi="10.1007/BF01449982",
                ),
                CitationEntry(
                    citation_id="cite_002",
                    key="matrixbook",
                    title="Matrix Analysis",
                    url="https://example.org/matrix-analysis",
                ),
            ]
        }
    )
    ctx = AgentContext(job_id="reader-test", atom=atom)

    with unittest.mock.patch("agents.prerequisite_mapper.httpx.AsyncClient", return_value=fake_http):
        result = await PrerequisiteMapperAgent(client=_FakeOpenAI(payload)).run(ctx)

    links = result.output["prerequisites"][0]["resource_links"]
    _assert(
        links[:2] == ["https://doi.org/10.1007/BF01449982", "https://example.org/matrix-analysis"],
        f"atom reference links should come before wiki links: {links}",
    )
    _assert(links[2] == "https://en.wikipedia.org/wiki/Spectral_radius", f"wiki link should follow: {links}")


# ---------------------------------------------------------------------------
# GlossaryAgent

async def test_glossary() -> None:
    payload = {
        "glossary": {
            "spectral radius": "The largest absolute eigenvalue of a matrix.",
            "positive-definite": "A symmetric matrix whose eigenvalues are all strictly positive.",
            "rho(A)": "Standard notation for the spectral radius of matrix A.",
        }
    }
    result = await GlossaryAgent(client=_FakeOpenAI(payload)).run(_ctx())
    _assert(result.status == "success", f"glossary status: {result.status} / {result.error}")
    glossary = result.output.get("glossary", {})
    _assert(len(glossary) == 3, f"expected 3 terms, got {len(glossary)}")
    _assert("spectral radius" in glossary, "spectral radius missing from glossary")


async def test_glossary_bad_response() -> None:
    # LLM returns a non-dict for 'glossary' — agent should still return success with empty dict.
    payload = {"glossary": "not a dict"}
    result = await GlossaryAgent(client=_FakeOpenAI(payload)).run(_ctx())
    _assert(result.status == "success", "expected graceful success on bad payload")
    _assert(result.output["glossary"] == {}, "expected empty glossary on bad payload")


# ---------------------------------------------------------------------------
# ExerciseGeneratorAgent

async def test_exercise_generator() -> None:
    payload = {
        "exercises": [
            {
                "prompt": "Which of the following is the spectral radius of A = diag(1, 3, 2)? (A) 1  (B) 2  (C) 3",
                "exercise_type": "counterexample_mcq",
                "answer_key": "C — the spectral radius is the largest eigenvalue, which is 3.",
            },
            {
                "prompt": "Compute the spectral radius of A = [[4, 0], [0, 1]].",
                "exercise_type": "computational",
                "answer_key": "rho(A) = 4.",
            },
        ]
    }
    result = await ExerciseGeneratorAgent(client=_FakeOpenAI(payload)).run(
        _ctx(comprehension_level="graduate")
    )
    _assert(result.status == "success", f"exercise status: {result.status} / {result.error}")
    exercises = result.output.get("exercises", [])
    _assert(len(exercises) == 2, f"expected 2 exercises, got {len(exercises)}")
    _assert("exercise_id" in exercises[0], "exercise_id not assigned")
    _assert(exercises[0]["exercise_type"] == "counterexample_mcq", "wrong exercise type")
    _assert(exercises[1]["exercise_type"] == "computational", "wrong exercise type")


async def test_exercise_generator_invalid_type_coerced() -> None:
    payload = {
        "exercises": [
            {
                "prompt": "What does rho(A) represent?",
                "exercise_type": "unknown_type",
                "answer_key": "The spectral radius.",
            }
        ]
    }
    result = await ExerciseGeneratorAgent(client=_FakeOpenAI(payload)).run(_ctx())
    exercises = result.output.get("exercises", [])
    _assert(len(exercises) == 1, "exercise should survive with coerced type")
    _assert(exercises[0]["exercise_type"] == "computational", "invalid type should be coerced to computational")


# ---------------------------------------------------------------------------
# SocraticTutorAgent

async def test_socratic_tutor() -> None:
    payload = {"response": "What do you think happens to rho(A) if we scale every eigenvalue by 2?"}
    result = await SocraticTutorAgent(client=_FakeOpenAI(payload)).run(
        _ctx(
            user_message="I don't understand why rho(A) is the largest eigenvalue specifically.",
            history=[],
        )
    )
    _assert(result.status == "success", f"tutor status: {result.status} / {result.error}")
    _assert(result.output["response"], "tutor response should not be empty")


async def test_socratic_tutor_with_history() -> None:
    payload = {"response": "Exactly — and how does that change the spectral radius?"}
    history = [
        {"role": "user", "content": "What is a positive-definite matrix?"},
        {"role": "assistant", "content": "A symmetric matrix with all positive eigenvalues. Can you think of an example?"},
    ]
    result = await SocraticTutorAgent(client=_FakeOpenAI(payload)).run(
        _ctx(
            user_message="So A = [[2,0],[0,3]] would be one?",
            history=history,
        )
    )
    _assert(result.status == "success", f"tutor with history: {result.status} / {result.error}")


async def test_socratic_tutor_missing_message() -> None:
    result = await SocraticTutorAgent(client=_FakeOpenAI({"response": "hi"})).run(
        _ctx()  # no user_message in extra
    )
    _assert(result.status == "error", "expected error when user_message is missing")


# ---------------------------------------------------------------------------
# runner

async def main_async() -> None:
    await test_explainer()
    print("  ExplainerAgent — OK")

    await test_explainer_missing_atom()
    print("  ExplainerAgent (missing atom) — OK")

    await test_prerequisite_mapper()
    print("  PrerequisiteMapperAgent — OK")

    await test_prerequisite_mapper_404_fallback()
    print("  PrerequisiteMapperAgent (404 fallback) — OK")

    await test_prerequisite_mapper_atom_references_first()
    print("  PrerequisiteMapperAgent (atom references first) — OK")

    await test_glossary()
    print("  GlossaryAgent — OK")

    await test_glossary_bad_response()
    print("  GlossaryAgent (bad response) — OK")

    await test_exercise_generator()
    print("  ExerciseGeneratorAgent — OK")

    await test_exercise_generator_invalid_type_coerced()
    print("  ExerciseGeneratorAgent (invalid type coercion) — OK")

    await test_socratic_tutor()
    print("  SocraticTutorAgent — OK")

    await test_socratic_tutor_with_history()
    print("  SocraticTutorAgent (with history) — OK")

    await test_socratic_tutor_missing_message()
    print("  SocraticTutorAgent (missing message) — OK")


def main() -> int:
    asyncio.run(main_async())
    print("reader agent tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
