from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from config import settings
from core.job_store import job_store
from formalization.axle_client import get_axle_client
from formalization.config import formalization_settings
from formalization.event_bus import formalization_event_bus
from formalization.models import FormalizationStatus
from formalization.orchestrator import FormalizationOrchestrator
from formalization.store import formalization_store
from ingestion import parse_tex
from ingestion.arxiv import fetch_arxiv_source, parse_arxiv_url
from models import (
    AtomImportance,
    ResearchAtom,
    ResearchAtomType,
    ResearchGraph,
    SourceSpan,
)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Live formalization E2E on arXiv 1312.6114.")
    parser.add_argument("--paper-id", default="1312.6114")
    parser.add_argument("--max-iterations", type=int, default=10000)
    parser.add_argument("--max-axle-calls", type=int, default=10000)
    args = parser.parse_args()

    if not (os.getenv("OPENAI_API_KEY") or settings.openai_api_key):
        raise SystemExit("OPENAI_API_KEY is required for live formalization E2E")
    if not formalization_settings.axle_api_key:
        raise SystemExit("AXLE_API_KEY is required for live formalization E2E")

    formalization_settings.formalization_max_iterations_per_atom = args.max_iterations
    formalization_settings.formalization_max_axle_calls_per_atom = args.max_axle_calls
    formalization_settings.formalization_parallelism = 1

    job_id = await build_vae_job(args.paper_id)
    job = job_store.get(job_id)
    atom_id = job["atoms"][0]["atom_id"]

    run = formalization_store.create_run(
        job_id=job_id,
        paper_id=job["paper_id"],
        selected_atom_ids=[atom_id],
        options={"source": "test_formalize_e2e", "paper_id": args.paper_id},
    )
    formalization_event_bus.create_channel(run.run_id)
    try:
        await FormalizationOrchestrator().run(run.run_id)
    finally:
        await get_axle_client().close()

    stored = formalization_store.get_run(run.run_id)
    atom = stored.atom_formalizations.get(atom_id)
    assert stored.status in {FormalizationStatus.COMPLETE, FormalizationStatus.ERROR}
    assert atom is not None
    assert atom.label is not None, atom.model_dump()
    print(
        "formalize e2e",
        {
            "job_id": job_id,
            "run_id": run.run_id,
            "atom_id": atom_id,
            "status": stored.status.value,
            "label": atom.label.value,
            "llm_calls": atom.llm_call_count,
            "tool_calls": len(atom.tool_calls),
            "artifacts": len(atom.artifacts),
        },
    )


async def build_vae_job(arxiv_id: str) -> str:
    ref = parse_arxiv_url(arxiv_id)
    if ref is None:
        raise RuntimeError(f"unrecognized arxiv id: {arxiv_id}")
    root = Path("/tmp/papercourt_formalization_e2e") / ref.canonical
    root.mkdir(parents=True, exist_ok=True)
    source = await fetch_arxiv_source(ref, str(root))
    assembled_path = root / f"{ref.canonical}.assembled.tex"
    assembled_path.write_text(source.tex_text, encoding="utf-8")

    from core.orchestrators.review import _build_source

    job_id = job_store.create_job(
        mode="review",
        filename=f"{ref.canonical}.tex",
        arxiv_id=ref.canonical,
        arxiv_source_url=source.source_url,
        tex_path=str(assembled_path),
        source_archive_path=source.archive_path,
        source_extract_dir=source.extract_dir,
        main_tex_path=source.main_tex_path,
    )
    paper = parse_tex(source.tex_text, _build_source(job_store.get(job_id)))
    atom = build_vae_atom(paper)
    graph = ResearchGraph(
        paper_id=paper.paper_id,
        atom_ids=[atom.atom_id],
        edges=[],
        roots=[atom.atom_id],
        topological_order=[atom.atom_id],
    )
    job_store.update(
        job_id,
        status="complete",
        paper_id=paper.paper_id,
        paper_title=paper.title,
        parsed_paper=paper.model_dump(),
        atoms=[atom.model_dump()],
        graph=graph.model_dump(),
        verdicts=[],
        report=None,
        total_atoms=1,
        completed_atoms=1,
        updated_at=datetime.utcnow().isoformat(),
    )
    return job_id


def build_vae_atom(paper):
    raw_text = paper.raw_text
    needle = "variational lower bound"
    idx = raw_text.lower().find(needle)
    start = max(0, idx - 700) if idx >= 0 else 0
    end = min(len(raw_text), start + 1800)
    excerpt = raw_text[start:end]
    equations = [eq for eq in paper.equations if "mathcal{L}" in eq.latex or "D_{KL}" in eq.latex][:4]
    return ResearchAtom(
        atom_id="atom_vae_elbo_identity",
        paper_id=paper.paper_id,
        atom_type=ResearchAtomType.PROPOSITION,
        text=(
            "The variational lower bound decomposes the log likelihood into an "
            "approximate posterior KL term plus an evidence lower bound, so the "
            "bound is no greater than the marginal log likelihood."
        ),
        section_heading="Auto-Encoding Variational Bayes",
        source_span=SourceSpan(
            paper_id=paper.paper_id,
            char_start=start,
            char_end=end,
            raw_excerpt=excerpt[:1000],
            match_confidence=0.8,
        ),
        equations=equations,
        citations=[],
        extraction_confidence=0.8,
        importance=AtomImportance.CORE,
        assumptions=["The latent-variable model and approximate posterior are well-defined."],
        conclusions=["The evidence lower bound is a lower bound on the marginal log likelihood."],
        proof_sketch="The KL divergence is nonnegative, so rearranging the decomposition yields the lower bound.",
        key_terms=["ELBO", "KL divergence", "variational lower bound"],
        symbols=["L(theta, phi; x)", "D_KL"],
    )


if __name__ == "__main__":
    asyncio.run(main())
