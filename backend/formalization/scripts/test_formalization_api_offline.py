from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

import formalization.api as formalization_api
import main as main_module
from core.job_store import job_store
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
    print("formalization API offline ok")


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
