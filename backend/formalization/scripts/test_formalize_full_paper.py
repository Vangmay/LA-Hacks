"""Full-paper formalization e2e.

Runs the real review pipeline (parse → atoms → graph) on an arXiv paper,
then formalizes every reviewable atom with AXLE through the orchestrator,
streaming live events to the console and saving a per-atom report at the end.

Usage:
    PYTHONPATH=backend python backend/formalization/scripts/test_formalize_full_paper.py \\
        --paper-id 1312.6114 --max-iterations 12 --max-axle-calls 10
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

load_dotenv(BACKEND / ".env", override=False)

from agents.atom_extractor import AtomExtractorAgent  # noqa: E402
from agents.base import AgentContext  # noqa: E402
from agents.graph_builder import GraphBuilderAgent  # noqa: E402
from config import settings  # noqa: E402
from core.citation_linker import link_citations_to_atoms  # noqa: E402
from core.equation_linker import link_equations_to_atoms  # noqa: E402
from core.job_store import job_store  # noqa: E402
from formalization.axle_client import get_axle_client  # noqa: E402
from formalization.config import formalization_settings  # noqa: E402
from formalization.event_bus import formalization_event_bus  # noqa: E402
from formalization.events import FormalizationEventType  # noqa: E402
from formalization.models import FormalizationStatus  # noqa: E402
from formalization.orchestrator import FormalizationOrchestrator  # noqa: E402
from formalization.store import formalization_store  # noqa: E402
from ingestion import parse_tex  # noqa: E402
from ingestion.arxiv import fetch_arxiv_source, parse_arxiv_url  # noqa: E402
from models import AtomImportance, ResearchAtom, ResearchAtomType, ResearchGraph  # noqa: E402


# A broader filter than `is_reviewable`: include definitions (formalizable as
# Lean `def`s) so the run isn't dominated by `not_a_theorem` outcomes.
FORMALIZATION_TYPES = {
    ResearchAtomType.THEOREM,
    ResearchAtomType.LEMMA,
    ResearchAtomType.COROLLARY,
    ResearchAtomType.PROPOSITION,
    ResearchAtomType.CONJECTURE,
    ResearchAtomType.BOUND,
    ResearchAtomType.ASSERTION,
    ResearchAtomType.ASSUMPTION,
    ResearchAtomType.DEFINITION,
    ResearchAtomType.CONSTRUCTION,
    ResearchAtomType.ALGORITHM,
}
FORMALIZATION_IMPORTANCE = {
    AtomImportance.MEDIUM,
    AtomImportance.HIGH,
    AtomImportance.CORE,
}


def select_formalization_atoms(atoms: list[ResearchAtom]) -> list[str]:
    return [
        atom.atom_id
        for atom in atoms
        if atom.atom_type in FORMALIZATION_TYPES
        and atom.importance in FORMALIZATION_IMPORTANCE
    ]


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-id", default="1312.6114")
    parser.add_argument("--max-iterations", type=int, default=12)
    parser.add_argument("--max-axle-calls", type=int, default=10)
    parser.add_argument("--parallelism", type=int, default=2)
    parser.add_argument("--limit", type=int, default=None, help="Only formalize the first N reviewable atoms.")
    args = parser.parse_args()

    if not (os.getenv("OPENAI_API_KEY") or settings.openai_api_key):
        raise SystemExit("OPENAI_API_KEY is required")
    if not formalization_settings.axle_api_key:
        raise SystemExit("AXLE_API_KEY is required")

    formalization_settings.formalization_max_iterations_per_atom = args.max_iterations
    formalization_settings.formalization_max_axle_calls_per_atom = args.max_axle_calls
    formalization_settings.formalization_parallelism = args.parallelism

    started = datetime.utcnow()
    print(f"\n[{_ts()}] === fetch + parse arXiv {args.paper_id} ===")
    job_id = await build_job(args.paper_id)
    job = job_store.get(job_id)
    paper_title = job.get("paper_title")
    atoms = [ResearchAtom.model_validate(a) for a in job["atoms"]]
    print(f"[{_ts()}] paper: {paper_title!r}  total_atoms={len(atoms)}")

    selected_ids = select_formalization_atoms(atoms)
    selected_atoms = [a for a in atoms if a.atom_id in selected_ids]
    if args.limit is not None:
        selected_ids = selected_ids[: args.limit]
        selected_atoms = selected_atoms[: args.limit]
    print(f"[{_ts()}] formalizing {len(selected_ids)} atoms (filter: theorem-like + def + assumption + algo)")
    for atom in selected_atoms:
        text = " ".join(atom.text.split())
        print(f"  - {atom.atom_id} [{atom.atom_type.value}/{atom.importance.value}] {text[:140]}")

    if not selected_ids:
        raise SystemExit("no formalization-eligible atoms — nothing to formalize")

    run = formalization_store.create_run(
        job_id=job_id,
        paper_id=job["paper_id"],
        selected_atom_ids=selected_ids,
        options={"source": "test_formalize_full_paper", "paper_id": args.paper_id},
    )
    formalization_event_bus.create_channel(run.run_id)

    stop_event = asyncio.Event()
    consumer_task = asyncio.create_task(_consume_events(run.run_id, stop_event))

    try:
        print(f"\n[{_ts()}] === formalize: run_id={run.run_id} ===")
        await FormalizationOrchestrator().run(run.run_id)
    finally:
        stop_event.set()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.wait_for(consumer_task, timeout=2.0)
        await get_axle_client().close()

    stored = formalization_store.get_run(run.run_id)
    elapsed = (datetime.utcnow() - started).total_seconds()
    _print_summary(stored, elapsed)
    out_path = _save_report(stored, atoms, paper_title, args)
    print(f"\n[{_ts()}] saved report: {out_path}")


async def build_job(arxiv_id: str) -> str:
    ref = parse_arxiv_url(arxiv_id)
    if ref is None:
        raise RuntimeError(f"unrecognized arxiv id: {arxiv_id}")

    root = Path("/tmp/papercourt_full_e2e") / ref.canonical
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
    print(
        f"[{_ts()}] parsed: sections={len(paper.sections)} equations={len(paper.equations)} "
        f"bib={len(paper.bibliography)}"
    )

    print(f"[{_ts()}] extracting atoms (LLM)...")
    extractor_result = await AtomExtractorAgent().run(
        AgentContext(job_id=job_id, parsed_paper=paper)
    )
    if extractor_result.status == "error":
        raise RuntimeError(f"atom extraction failed: {extractor_result.error}")
    atoms = [ResearchAtom.model_validate(a) for a in extractor_result.output.get("atoms", [])]
    if not atoms:
        raise RuntimeError("atom extraction produced zero atoms")
    atoms = link_equations_to_atoms(paper, atoms)
    atoms = link_citations_to_atoms(paper, atoms)

    print(f"[{_ts()}] building graph (LLM)...")
    graph_result = await GraphBuilderAgent().run(
        AgentContext(job_id=job_id, extra={"atoms": atoms})
    )
    graph_data = graph_result.output.get("graph")
    if graph_data is None:
        graph = ResearchGraph(
            paper_id=paper.paper_id,
            atom_ids=[a.atom_id for a in atoms],
            edges=[],
            roots=[a.atom_id for a in atoms],
            topological_order=[a.atom_id for a in atoms],
        )
    else:
        graph = ResearchGraph.model_validate(graph_data)

    job_store.update(
        job_id,
        status="complete",
        paper_id=paper.paper_id,
        paper_title=paper.title,
        parsed_paper=paper.model_dump(),
        atoms=[a.model_dump() for a in atoms],
        graph=graph.model_dump(),
        verdicts=[],
        report=None,
        total_atoms=len(atoms),
        completed_atoms=len(atoms),
        updated_at=datetime.utcnow().isoformat(),
    )
    return job_id


async def _consume_events(run_id: str, stop_event: asyncio.Event) -> None:
    """Print one terse line per relevant event so progress is visible."""
    async for event in formalization_event_bus.subscribe(run_id):
        if stop_event.is_set():
            return
        line = _format_event(event)
        if line:
            print(line, flush=True)
        if event.event_type in {
            FormalizationEventType.RUN_COMPLETE,
            FormalizationEventType.RUN_ERROR,
        }:
            return


def _format_event(event: Any) -> Optional[str]:
    et = event.event_type
    atom = event.atom_id or "-"
    payload = event.payload or {}
    ts = event.timestamp.strftime("%H:%M:%S")
    if et == FormalizationEventType.RUN_STARTED:
        return f"[{ts}] RUN_STARTED  selected={len(payload.get('selected_atom_ids', []))}"
    if et == FormalizationEventType.ATOM_QUEUED:
        return (
            f"[{ts}] QUEUED       {atom} type={payload.get('atom_type')} "
            f"importance={payload.get('importance')}"
        )
    if et == FormalizationEventType.ATOM_CONTEXT_BUILT:
        return (
            f"[{ts}] CTX_BUILT    {atom} eq={payload.get('equations')} "
            f"cite={payload.get('citations')} dep={payload.get('dependencies')}"
        )
    if et == FormalizationEventType.TOOL_CALL_STARTED:
        return f"[{ts}] TOOL_START   {atom} {payload.get('tool_name')}"
    if et == FormalizationEventType.TOOL_CALL_COMPLETE:
        summary = payload.get("result_summary") or {}
        okay = summary.get("okay")
        errs = summary.get("lean_errors")
        first = ""
        if isinstance(summary.get("first_errors"), list) and summary["first_errors"]:
            first = " | " + str(summary["first_errors"][0])[:160]
        status = payload.get("status")
        return (
            f"[{ts}] TOOL_DONE    {atom} {payload.get('tool_name')} "
            f"status={status} okay={okay} errs={errs}{first}"
        )
    if et == FormalizationEventType.ARTIFACT_RECORDED:
        return (
            f"[{ts}] ARTIFACT     {atom} kind={payload.get('kind')} "
            f"iter={payload.get('iteration')} chars={payload.get('lean_code_chars')}"
        )
    if et == FormalizationEventType.ATOM_VERDICT:
        return (
            f"[{ts}] VERDICT      {atom} label={payload.get('label')} "
            f"conf={payload.get('confidence')}"
        )
    if et == FormalizationEventType.ATOM_ERROR:
        return f"[{ts}] ATOM_ERROR   {atom} {payload.get('error', '')[:200]}"
    if et == FormalizationEventType.RUN_COMPLETE:
        return f"[{ts}] RUN_COMPLETE summary={payload.get('summary')}"
    if et == FormalizationEventType.RUN_ERROR:
        return f"[{ts}] RUN_ERROR    {payload.get('error', '')[:200]}"
    return None


def _print_summary(run: Any, elapsed_seconds: float) -> None:
    print(f"\n=== summary ({elapsed_seconds:.1f}s) ===")
    print(f"run status: {run.status.value}  total atoms: {len(run.atom_formalizations)}")
    print(f"label counts: {run.summary}")
    print("\nper-atom:")
    for atom_id, atom in run.atom_formalizations.items():
        label = atom.label.value if atom.label else "?"
        artifacts = len(atom.artifacts)
        last_artifact = atom.artifacts[-1] if atom.artifacts else None
        check_okay = last_artifact.axle_check_okay if last_artifact else None
        verify_okay = last_artifact.axle_verify_okay if last_artifact else None
        rationale = (atom.rationale or "")[:160]
        print(
            f"  {atom_id:48s} {label:24s} llm={atom.llm_call_count} tools={len(atom.tool_calls)} "
            f"artifacts={artifacts} check_ok={check_okay} verify_ok={verify_okay}"
        )
        if rationale:
            print(f"      rationale: {rationale}")


def _save_report(run: Any, atoms: list[ResearchAtom], paper_title: Optional[str], args: argparse.Namespace) -> Path:
    out_dir = BACKEND / "outputs" / "formalizations" / "_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_paper = (args.paper_id or "unknown").replace("/", "_").replace(".", "_")
    filename = f"{safe_paper}_{run.run_id[:8]}_full_paper.json"
    out_path = out_dir / filename
    payload = {
        "paper_id": args.paper_id,
        "paper_title": paper_title,
        "run_id": run.run_id,
        "job_id": run.job_id,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "summary": run.summary,
        "settings": {
            "max_iterations_per_atom": args.max_iterations,
            "max_axle_calls_per_atom": args.max_axle_calls,
            "parallelism": args.parallelism,
        },
        "atoms": {
            atom_id: {
                "label": (af.label.value if af.label else None),
                "rationale": af.rationale,
                "confidence": af.confidence,
                "used_assumptions": af.used_assumptions,
                "llm_call_count": af.llm_call_count,
                "tool_calls": [
                    {
                        "name": tc.tool_name,
                        "status": tc.status,
                        "okay": (tc.result_summary or {}).get("okay"),
                        "errors": (tc.result_summary or {}).get("lean_errors"),
                        "first_error": ((tc.result_summary or {}).get("first_errors") or [None])[0],
                        "error": tc.error,
                    }
                    for tc in af.tool_calls
                ],
                "artifacts": [
                    {
                        "kind": art.kind,
                        "iteration": art.iteration,
                        "axle_check_okay": art.axle_check_okay,
                        "axle_verify_okay": art.axle_verify_okay,
                        "lean_code": art.lean_code,
                    }
                    for art in af.artifacts
                ],
                "error": af.error,
            }
            for atom_id, af in run.atom_formalizations.items()
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return out_path


def _ts() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


if __name__ == "__main__":
    asyncio.run(main())
