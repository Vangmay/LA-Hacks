from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi.testclient import TestClient

import formalization.api as formalization_api
import main as main_module
from core.job_store import job_store
from formalization.context_builder import load_review_job, rehydrate_job
from formalization.orchestrator import FormalizationOrchestrator
from formalization.store import formalization_store
from models import (
    AtomImportance,
    PaperSource,
    ParsedPaper,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraph,
    SourceKind,
    SourceSpan,
)


class NoopOrchestrator:
    async def run(self, _run_id: str) -> None:
        return None


class CapturingAgent:
    def __init__(self) -> None:
        self.contexts: list[dict] = []

    async def run_atom(self, *, run_id: str, atom_id: str, context: dict) -> None:
        self.contexts.append(context)


def main() -> None:
    formalization_api._orchestrator = NoopOrchestrator()
    client = TestClient(main_module.app)
    job_id, atom_id = make_completed_review_job()

    response = client.post(f"/formalize/{job_id}/atom/{atom_id}", json={})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["selected_atom_ids"] == [atom_id]
    run_id = data["run_id"]

    response = client.get(f"/formalize/runs/{run_id}")
    assert response.status_code == 200, response.text
    assert response.json()["job_id"] == job_id

    response = client.get(f"/formalize/runs/{run_id}/lean")
    assert response.status_code == 404

    response = client.post("/formalize/missing-job", json={})
    assert response.status_code == 404
    asyncio.run(test_formalization_run_snapshot_keeps_atom_metadata())
    print("formalization API offline ok")


async def test_formalization_run_snapshot_keeps_atom_metadata() -> None:
    job_id, atom_id = make_completed_review_job()
    job = load_review_job(job_id)
    paper, _atoms, _graph = rehydrate_job(job)
    run = formalization_store.create_run(
        job_id=job_id,
        paper_id=paper.paper_id,
        selected_atom_ids=[atom_id],
    )

    agent = CapturingAgent()
    await FormalizationOrchestrator(agent=agent).run(run.run_id)
    snapshot = formalization_store.get_run(run.run_id).model_dump()
    atom = snapshot["atom_formalizations"][atom_id]

    assert atom["text"] == "1 + 1 = 2"
    assert atom["atom_type"] == ResearchAtomType.PROPOSITION.value
    assert atom["importance"] == AtomImportance.CORE.value
    assert atom["queue_index"] == 1
    assert atom["queue_total"] == 1
    assert atom["max_iterations"] > 0
    assert atom["max_axle_calls"] > 0
    assert atom["section_heading"] == "Arithmetic"
    assert atom["context_summary"]["atom_id"] == atom_id
    assert atom["context_summary"]["section_heading"] == "Arithmetic"
    assert atom["context_summary"]["tex_excerpt_chars"] > 0
    assert atom["context_summary"]["nearby_prose_chars"] > 0
    assert agent.contexts and agent.contexts[0]["atom_id"] == atom_id


def make_completed_review_job() -> tuple[str, str]:
    source = PaperSource(
        paper_id="paper_formal_api",
        source_kind=SourceKind.MANUAL_TEX,
        fetched_at=datetime.utcnow(),
        content_hash="abc123",
    )
    span = SourceSpan(
        paper_id=source.paper_id,
        char_start=0,
        char_end=12,
        tex_start=0,
        tex_end=12,
        raw_excerpt="1 + 1 = 2",
        match_confidence=1.0,
    )
    paper = ParsedPaper(
        paper_id=source.paper_id,
        source=source,
        title="Formal API Fixture",
        raw_text="1 + 1 = 2",
        assembled_tex="1 + 1 = 2",
    )
    atom = ResearchAtom(
        atom_id="atom_formal_api",
        paper_id=source.paper_id,
        atom_type=ResearchAtomType.PROPOSITION,
        text="1 + 1 = 2",
        source_span=span,
        extraction_confidence=1.0,
        importance=AtomImportance.CORE,
        section_heading="Arithmetic",
    )
    graph = ResearchGraph(
        paper_id=source.paper_id,
        atom_ids=[atom.atom_id],
        edges=[],
        roots=[atom.atom_id],
        topological_order=[atom.atom_id],
    )
    job_id = job_store.create_job(mode="review", filename="fixture.tex")
    job_store.update(
        job_id,
        status="complete",
        paper_id=source.paper_id,
        parsed_paper=paper.model_dump(),
        atoms=[atom.model_dump()],
        graph=graph.model_dump(),
        total_atoms=1,
        completed_atoms=1,
    )
    return job_id, atom.atom_id


if __name__ == "__main__":
    main()
