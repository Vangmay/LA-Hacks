"""Offline tests for the Reader Mode orchestrator, job_store additions, and API routes.

No real OpenAI calls, no real arXiv fetches, no disk I/O beyond a tiny temp file.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest.mock
import uuid
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main as main_module  # noqa: E402
from core.job_store import job_store  # noqa: E402
from models import (  # noqa: E402
    AtomImportance,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraph,
    SourceSpan,
)

client = TestClient(main_module.app)

# ---------------------------------------------------------------------------
# fixtures

_SAMPLE_TEX = r"""
\documentclass{article}
\title{Reader Test}
\begin{document}
\section{Main}
\begin{theorem}
For every $x \in \mathbb{R}$, $x^2 \geq 0$.
\end{theorem}
\end{document}
"""

_PAPER_ID = "reader-test-paper"


def _atom(atom_id: str = "atom_001") -> ResearchAtom:
    text = "For every x in R, x^2 >= 0."
    return ResearchAtom(
        atom_id=atom_id,
        paper_id=_PAPER_ID,
        atom_type=ResearchAtomType.THEOREM,
        text=text,
        section_heading="Main",
        source_span=SourceSpan(
            paper_id=_PAPER_ID,
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=0.95,
        importance=AtomImportance.HIGH,
    )


def _graph(atom_ids: list[str] | None = None) -> ResearchGraph:
    ids = atom_ids or ["atom_001"]
    return ResearchGraph(
        paper_id=_PAPER_ID,
        atom_ids=ids,
        edges=[],
        roots=ids,
        topological_order=ids,
    )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _mk_session(status: str = "complete", extra: dict | None = None) -> str:
    """Insert a pre-built reader session directly into job_store."""
    atom = _atom()
    graph = _graph()
    session_id = job_store.create_job(
        mode="reader",
        comprehension_level="graduate",
        status=status,
        atoms=[atom.model_dump()],
        graph=graph.model_dump(),
        graph_snapshot={
            "nodes": [{"id": "atom_001", "comprehension_status": "unvisited", "start_here": True}],
            "edges": [],
        },
        annotations={},
        comprehension_states={"atom_001": "unvisited"},
        start_here=["atom_001"],
        total_atoms=1,
        paper_metadata={"title": "Reader Test", "arxiv_id": "0000.00000"},
        **(extra or {}),
    )
    return session_id


def _mk_fake_openai(payload: dict):
    class _FakeCompletions:
        async def create(self, **_kw):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
            )

    class _FakeOpenAI:
        chat = SimpleNamespace(completions=_FakeCompletions())

    return _FakeOpenAI()


# ---------------------------------------------------------------------------
# 1. JobStore reader-specific methods

def test_job_store_annotation_roundtrip() -> None:
    sid = job_store.create_job(mode="reader")
    annotation = {"atom_id": "a1", "explanation": "hello"}
    job_store.set_annotation(sid, "a1", annotation)
    got = job_store.get_annotation(sid, "a1")
    _assert(got == annotation, f"annotation roundtrip failed: {got}")
    _assert(job_store.get_annotation(sid, "missing") is None, "missing annotation should be None")
    print("  job_store annotation roundtrip — OK")


def test_job_store_comprehension_status() -> None:
    sid = job_store.create_job(mode="reader")
    job_store.set_comprehension_status(sid, "a1", "understood")
    _assert(job_store.get_comprehension_status(sid, "a1") == "understood", "wrong status")
    _assert(job_store.get_comprehension_status(sid, "missing") is None, "missing should be None")
    print("  job_store comprehension_status — OK")


def test_job_store_update_exercise() -> None:
    sid = job_store.create_job(mode="reader")
    annotation = {
        "atom_id": "a1",
        "exercises": [{"exercise_id": "ex1", "prompt": "Q?", "answer_key": "A"}],
    }
    job_store.set_annotation(sid, "a1", annotation)
    updated = job_store.update_exercise_in_annotation(sid, "a1", "ex1", graded=True, user_answer="42")
    _assert(updated, "update should return True")
    ex = job_store.get_annotation(sid, "a1")["exercises"][0]
    _assert(ex["graded"] is True, "graded not set")
    _assert(ex["user_answer"] == "42", "user_answer not set")
    not_found = job_store.update_exercise_in_annotation(sid, "a1", "nonexistent")
    _assert(not_found is False, "should return False for missing exercise_id")
    print("  job_store update_exercise — OK")


# ---------------------------------------------------------------------------
# 2. ReaderOrchestrator (mocked agents)

async def test_reader_orchestrator_happy_path() -> None:
    from core.orchestrators.reader import ReaderOrchestrator  # noqa: PLC0415

    atom = _atom()
    graph = _graph()

    fake_extraction = SimpleNamespace(
        status="success",
        output={"atoms": [atom.model_dump()]},
        confidence=0.9,
        error=None,
    )
    fake_graph = SimpleNamespace(
        status="success",
        output={"graph": graph.model_dump()},
        confidence=0.9,
        error=None,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False, encoding="utf-8") as fh:
        fh.write(_SAMPLE_TEX)
        tex_path = fh.name

    try:
        session_id = job_store.create_job(
            mode="reader",
            comprehension_level="undergraduate",
            arxiv_id="0000.00000",
            tex_path=tex_path,
        )

        with (
            unittest.mock.patch(
                "core.orchestrators.reader.AtomExtractorAgent.run",
                return_value=fake_extraction,
            ),
            unittest.mock.patch(
                "core.orchestrators.reader.GraphBuilderAgent.run",
                return_value=fake_graph,
            ),
        ):
            await ReaderOrchestrator().run(session_id)

        job = job_store.get(session_id)
        _assert(job["status"] == "complete", f"expected complete, got {job['status']}")
        _assert(len(job["atoms"]) == 1, "expected 1 atom")
        _assert("atom_001" in job["start_here"], f"atom_001 not in start_here: {job['start_here']}")
        _assert(job["comprehension_states"]["atom_001"] == "unvisited", "wrong initial state")
        _assert(job["annotations"] == {}, "annotations should start empty")
    finally:
        os.unlink(tex_path)

    print("  ReaderOrchestrator happy path — OK")


async def test_reader_orchestrator_missing_tex() -> None:
    from core.orchestrators.reader import ReaderOrchestrator  # noqa: PLC0415

    session_id = job_store.create_job(mode="reader", comprehension_level="undergraduate")
    # No tex_path set — orchestrator should set status="error".
    await ReaderOrchestrator().run(session_id)
    job = job_store.get(session_id)
    _assert(job["status"] == "error", f"expected error, got {job['status']}")
    print("  ReaderOrchestrator missing tex_path ->error — OK")


# ---------------------------------------------------------------------------
# 3. Reader API routes

def test_status_unknown_404() -> None:
    resp = client.get("/read/does-not-exist/status")
    _assert(resp.status_code == 404, f"expected 404, got {resp.status_code}")
    print("  GET /read/unknown/status ->404 — OK")


def test_status_known() -> None:
    sid = _mk_session()
    resp = client.get(f"/read/{sid}/status")
    _assert(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}")
    body = resp.json()
    _assert(body["session_id"] == sid, f"wrong session_id: {body}")
    _assert(body["status"] == "complete", f"wrong status: {body}")
    _assert(body["start_here"] == ["atom_001"], f"wrong start_here: {body}")
    print("  GET /read/{sid}/status ->200 with session_id — OK")


def test_graph_unknown_returns_empty() -> None:
    resp = client.get("/read/does-not-exist/graph")
    _assert(resp.status_code == 404, f"expected 404, got {resp.status_code}")
    print("  GET /read/unknown/graph ->404 — OK")


def test_graph_returns_snapshot_with_start_here_flag() -> None:
    sid = _mk_session()
    resp = client.get(f"/read/{sid}/graph")
    _assert(resp.status_code == 200, f"expected 200: {resp.text}")
    body = resp.json()
    nodes = body.get("nodes", [])
    _assert(len(nodes) == 1, f"expected 1 node, got {len(nodes)}")
    _assert(nodes[0]["start_here"] is True, f"start_here flag missing: {nodes[0]}")
    _assert(nodes[0]["comprehension_status"] == "unvisited", f"wrong status: {nodes[0]}")
    print("  GET /read/{sid}/graph ->snapshot with start_here flag — OK")


def test_atom_annotation_cache_miss_then_hit() -> None:
    sid = _mk_session()

    explainer_payload = {
        "explanation": "x squared is non-negative.",
        "key_insight": "Squares are always non-negative.",
        "worked_example": "(-2)^2 = 4 >= 0",
    }
    prereq_payload = {"prerequisites": []}
    glossary_payload = {"glossary": {"x": "a real number"}}
    exercise_payload = {
        "exercises": [
            {
                "exercise_id": "ex-generated",
                "prompt": "What is (-3)^2?",
                "exercise_type": "computational",
                "answer_key": "9",
            }
        ]
    }

    fake_openai = _mk_fake_openai({})

    def _fake_agent_run(payload):
        async def _run(self, ctx):
            return SimpleNamespace(
                status="success",
                output=payload,
                confidence=0.9,
                error=None,
            )
        return _run

    with (
        unittest.mock.patch("api.reader.ExplainerAgent.run", _fake_agent_run(explainer_payload)),
        unittest.mock.patch("api.reader.PrerequisiteMapperAgent.run", _fake_agent_run(prereq_payload)),
        unittest.mock.patch("api.reader.GlossaryAgent.run", _fake_agent_run(glossary_payload)),
        unittest.mock.patch("api.reader.ExerciseGeneratorAgent.run", _fake_agent_run(exercise_payload)),
    ):
        # First call — cache miss, agents run.
        resp = client.get(f"/read/{sid}/atom/atom_001")
        _assert(resp.status_code == 200, f"expected 200: {resp.text}")
        body = resp.json()
        _assert(body["explanation"] == explainer_payload["explanation"], f"wrong explanation: {body}")
        _assert(body["glossary"] == {"x": "a real number"}, f"wrong glossary: {body}")
        _assert(body["atom_id"] == "atom_001", f"wrong atom_id: {body}")
        _assert(len(body["exercises"]) == 1, f"expected generated exercise in annotation: {body}")
        _assert(
            body["exercises"][0]["exercise_id"] == "ex-generated",
            f"wrong exercise id: {body['exercises']}",
        )
        _assert(
            body["exercises"][0]["exercise_type"] == "computational",
            f"wrong exercise type: {body['exercises']}",
        )
        _assert(
            body["exercises"][0]["answer_key"] == "9",
            f"wrong exercise answer key: {body['exercises']}",
        )

        # Second call — cache hit, agents should NOT run again.
        resp2 = client.get(f"/read/{sid}/atom/atom_001")
        _assert(resp2.status_code == 200, f"second call failed: {resp2.text}")
        _assert(resp2.json() == body, "cached annotation should match first response")

    print("  GET /read/{sid}/atom/{atom_id} cache miss then hit — OK")


def test_atom_annotation_unknown_session_404() -> None:
    resp = client.get("/read/bad-session/atom/atom_001")
    _assert(resp.status_code == 404, f"expected 404, got {resp.status_code}")
    print("  GET /read/unknown-session/atom/atom_001 ->404 — OK")


def test_atom_annotation_unknown_atom_404() -> None:
    sid = _mk_session()
    resp = client.get(f"/read/{sid}/atom/nonexistent_atom")
    _assert(resp.status_code == 404, f"expected 404, got {resp.status_code}")
    print("  GET /read/{sid}/atom/nonexistent ->404 — OK")


def test_atom_annotation_session_processing_returns_202() -> None:
    sid = _mk_session(status="processing")
    resp = client.get(f"/read/{sid}/atom/atom_001")
    _assert(resp.status_code == 202, f"expected 202 while processing, got {resp.status_code}")
    print("  GET /read/{sid}/atom/{atom_id} while processing ->202 — OK")


def test_tutor_returns_response() -> None:
    sid = _mk_session()
    payload = {"response": "What do you think happens if x is negative?"}

    async def _fake_run(self, ctx):
        return SimpleNamespace(status="success", output=payload, confidence=0.9, error=None)

    with unittest.mock.patch("api.reader.SocraticTutorAgent.run", _fake_run):
        resp = client.post(
            f"/read/{sid}/atom/atom_001/tutor",
            json={"message": "Why is x^2 always non-negative?", "history": []},
        )

    _assert(resp.status_code == 200, f"expected 200: {resp.text}")
    _assert(resp.json()["response"] == payload["response"], f"wrong response: {resp.json()}")
    print("  POST /read/{sid}/atom/{atom_id}/tutor ->response — OK")


def test_tutor_unknown_session_404() -> None:
    resp = client.post(
        "/read/bad/atom/atom_001/tutor",
        json={"message": "hello", "history": []},
    )
    _assert(resp.status_code == 404, f"expected 404: {resp.status_code}")
    print("  POST /read/unknown/atom/{atom_id}/tutor ->404 — OK")


def test_grade_exercise() -> None:
    sid = _mk_session()
    annotation = {
        "atom_id": "atom_001",
        "exercises": [
            {
                "exercise_id": "ex42",
                "prompt": "What is (-3)^2?",
                "exercise_type": "computational",
                "answer_key": "9",
            }
        ],
    }
    job_store.set_annotation(sid, "atom_001", annotation)

    grade_payload = {"correct": True, "feedback": "Correct! 9 is right."}

    with unittest.mock.patch(
        "api.reader.make_async_openai",
        return_value=_mk_fake_openai(grade_payload),
    ):
        resp = client.post(
            f"/read/{sid}/atom/atom_001/grade",
            json={"exercise_id": "ex42", "answer": "9"},
        )

    _assert(resp.status_code == 200, f"expected 200: {resp.text}")
    body = resp.json()
    _assert(body["correct"] is True, f"expected correct=True: {body}")
    _assert("Correct" in body["feedback"], f"unexpected feedback: {body}")

    # Verify exercise was updated in store.
    ex = job_store.get_annotation(sid, "atom_001")["exercises"][0]
    _assert(ex["graded"] is True, "exercise not marked graded in store")
    _assert(ex["user_answer"] == "9", "user_answer not stored")
    print("  POST /read/{sid}/atom/{atom_id}/grade ->correct + store updated — OK")


def test_grade_missing_annotation_404() -> None:
    sid = _mk_session()  # no annotation set
    resp = client.post(
        f"/read/{sid}/atom/atom_001/grade",
        json={"exercise_id": "ex1", "answer": "x"},
    )
    _assert(resp.status_code == 404, f"expected 404: {resp.status_code}")
    print("  POST /read/{sid}/atom/{atom_id}/grade with no annotation ->404 — OK")


def test_patch_status_valid() -> None:
    sid = _mk_session()
    resp = client.patch(
        f"/read/{sid}/atom/atom_001/status",
        json={"status": "understood"},
    )
    _assert(resp.status_code == 200, f"expected 200: {resp.text}")
    _assert(resp.json()["status"] == "understood", f"wrong status: {resp.json()}")

    stored = job_store.get_comprehension_status(sid, "atom_001")
    _assert(stored == "understood", f"store not updated: {stored}")
    print("  PATCH /read/{sid}/atom/{atom_id}/status ->understood — OK")


def test_patch_status_invalid_400() -> None:
    sid = _mk_session()
    resp = client.patch(
        f"/read/{sid}/atom/atom_001/status",
        json={"status": "totally_wrong"},
    )
    _assert(resp.status_code == 400, f"expected 400: {resp.status_code}")
    print("  PATCH /read/{sid}/atom/{atom_id}/status with bad value ->400 — OK")


def test_study_guide_empty() -> None:
    sid = _mk_session()  # no annotations visited
    resp = client.get(f"/read/{sid}/study-guide")
    _assert(resp.status_code == 200, f"expected 200: {resp.status_code}")
    text = resp.text
    _assert("Reader Test" in text, f"title missing from guide: {text[:200]}")
    _assert("No atoms visited" in text, f"expected empty-state message: {text[:200]}")
    print("  GET /read/{sid}/study-guide (empty) — OK")


def test_study_guide_with_annotations() -> None:
    sid = _mk_session()
    annotation = {
        "atom_id": "atom_001",
        "level": "graduate",
        "explanation": "Squares are always non-negative.",
        "key_insight": "x^2 >= 0 for all real x.",
        "worked_example": "(-2)^2 = 4",
        "glossary": {"spectral radius": "largest eigenvalue in magnitude"},
        "prerequisites": [
            {
                "concept": "Real numbers",
                "description": "The continuum of numbers.",
                "resource_links": ["https://en.wikipedia.org/wiki/Real_number"],
            }
        ],
        "exercises": [
            {
                "exercise_id": "ex1",
                "prompt": "Compute (-3)^2.",
                "exercise_type": "computational",
                "answer_key": "9",
            }
        ],
        "comprehension_status": "understood",
    }
    job_store.set_annotation(sid, "atom_001", annotation)
    job_store.set_comprehension_status(sid, "atom_001", "understood")

    resp = client.get(f"/read/{sid}/study-guide")
    _assert(resp.status_code == 200, f"expected 200: {resp.status_code}")
    text = resp.text
    _assert("Reader Test" in text, "title missing")
    _assert("Understood: 1/1" in text, f"progress missing: {text[:300]}")
    _assert("spectral radius" in text, "glossary term missing")
    _assert("Real numbers" in text, "prerequisite missing")
    _assert("Compute (-3)^2" in text, "exercise missing")
    _assert("★" in text, "start_here star missing")
    print("  GET /read/{sid}/study-guide (with annotations) — OK")


def test_study_guide_processing_202() -> None:
    sid = _mk_session(status="processing")
    resp = client.get(f"/read/{sid}/study-guide")
    _assert(resp.status_code == 202, f"expected 202 while processing: {resp.status_code}")
    print("  GET /read/{sid}/study-guide while processing ->202 — OK")


# ---------------------------------------------------------------------------
# runner

async def main_async() -> None:
    # job_store
    test_job_store_annotation_roundtrip()
    test_job_store_comprehension_status()
    test_job_store_update_exercise()

    # orchestrator
    await test_reader_orchestrator_happy_path()
    await test_reader_orchestrator_missing_tex()

    # API
    test_status_unknown_404()
    test_status_known()
    test_graph_unknown_returns_empty()
    test_graph_returns_snapshot_with_start_here_flag()
    test_atom_annotation_cache_miss_then_hit()
    test_atom_annotation_unknown_session_404()
    test_atom_annotation_unknown_atom_404()
    test_atom_annotation_session_processing_returns_202()
    test_tutor_returns_response()
    test_tutor_unknown_session_404()
    test_grade_exercise()
    test_grade_missing_annotation_404()
    test_patch_status_valid()
    test_patch_status_invalid_400()
    test_study_guide_empty()
    test_study_guide_with_annotations()
    test_study_guide_processing_202()


def main() -> int:
    asyncio.run(main_async())
    print("reader API/orchestrator tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
