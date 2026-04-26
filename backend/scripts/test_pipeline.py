"""Live end-to-end test for the v0.4 ResearchAtom review pipeline.

Usage from repo root:
    python backend/scripts/test_pipeline.py https://arxiv.org/abs/1706.03762
    python backend/scripts/test_pipeline.py --papers-file good_papers.txt

This script makes real OpenAI calls. It intentionally exercises the same
central pipeline as ReviewOrchestrator without resurrecting legacy ClaimUnit
agents.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import dotenv

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

dotenv.load_dotenv(BACKEND / ".env")

from agents.atom_extractor import AtomExtractorAgent  # noqa: E402
from agents.base import AgentContext  # noqa: E402
from agents.cascade import apply_cascade  # noqa: E402
from agents.challenge_agent import ChallengeAgent  # noqa: E402
from agents.defense_agent import DefenseAgent  # noqa: E402
from agents.exercise_generator import ExerciseGeneratorAgent  # noqa: E402
from agents.explainer import ExplainerAgent  # noqa: E402
from agents.glossary_agent import GlossaryAgent  # noqa: E402
from agents.graph_builder import GraphBuilderAgent  # noqa: E402
from agents.prerequisite_mapper import PrerequisiteMapperAgent  # noqa: E402
from agents.report_agent import build_review_report  # noqa: E402
from agents.socratic_tutor import SocraticTutorAgent  # noqa: E402
from agents.verdict_aggregator import aggregate_verdict  # noqa: E402
from checks import run_algebraic_sanity, run_citation_probe, run_numeric_probe  # noqa: E402
from config import settings  # noqa: E402
from core.citation_linker import link_citations_to_atoms  # noqa: E402
from core.equation_linker import link_equations_to_atoms  # noqa: E402
from ingestion.arxiv import fetch_arxiv_source, parse_arxiv_url  # noqa: E402
from ingestion.tex_parser import parse_tex  # noqa: E402
from models import (  # noqa: E402
    AtomVerdict,
    Challenge,
    CheckKind,
    CheckResult,
    CheckStatus,
    PaperSource,
    ParsedPaper,
    Rebuttal,
    ResearchAtom,
    ResearchGraph,
    SourceKind,
    is_reviewable,
)


async def run_one(
    arxiv_value: str,
    max_review_atoms: Optional[int],
    *,
    skip_reader_probe: bool,
) -> int:
    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set. Add it to backend/.env and re-run.")
        return 1

    ref = parse_arxiv_url(arxiv_value)
    if not ref:
        print(f"Could not parse arXiv URL/id: {arxiv_value!r}")
        return 1

    job_id = f"manual-{uuid.uuid4().hex[:8]}"
    pipeline: dict[str, Any] = {
        "job_id": job_id,
        "arxiv_id": ref.canonical,
        "source_url": ref.source_url,
    }

    with tempfile.TemporaryDirectory() as tmp:
        print(f"\n=== {ref.canonical}: fetch arXiv TeX source ===")
        source = await fetch_arxiv_source(ref, tmp)
        tex_hash = hashlib.md5(source.tex_text.encode("utf-8")).hexdigest()[:16]
        assembled_path = Path(tmp) / f"{ref.canonical.replace('/', '_')}.assembled.tex"
        assembled_path.write_text(source.tex_text, encoding="utf-8")
        paper_source = PaperSource(
            paper_id=ref.canonical,
            source_kind=SourceKind.ARXIV,
            arxiv_id=ref.canonical,
            source_url=source.source_url,
            abs_url=f"https://arxiv.org/abs/{ref.canonical}",
            pdf_url=f"https://arxiv.org/pdf/{ref.canonical}",
            source_archive_path=source.archive_path,
            source_extract_dir=source.extract_dir,
            main_tex_path=source.main_tex_path,
            assembled_tex_path=str(assembled_path),
            fetched_at=datetime.utcnow(),
            content_hash=tex_hash,
        )
        pipeline["source"] = {
            "main_tex_path": source.main_tex_path,
            "tex_files": len(source.tex_paths),
            "chars": len(source.tex_text),
            "content_hash": tex_hash,
        }
        print(f"  main: {Path(source.main_tex_path).name}")
        print(f"  tex files: {len(source.tex_paths)}")
        print(f"  chars: {len(source.tex_text)}")

        print("=== parse ===")
        paper = parse_tex(source.tex_text, paper_source)
        pipeline["parser"] = {
            "title": paper.title,
            "sections": len(paper.sections),
            "equations": len(paper.equations),
            "bibliography": len(paper.bibliography),
            "warnings": paper.parser_warnings,
        }
        print(f"  title: {paper.title[:100]!r}")
        print(f"  sections={len(paper.sections)} equations={len(paper.equations)} bibliography={len(paper.bibliography)}")

        print("=== extract atoms ===")
        atoms, atom_warnings = await _extract_atoms(job_id, paper)
        atoms = link_equations_to_atoms(paper, atoms)
        atoms = link_citations_to_atoms(paper, atoms)
        pipeline["atoms"] = [a.model_dump() for a in atoms]
        pipeline["atom_extraction_warnings"] = atom_warnings
        by_type: dict[str, int] = {}
        for atom in atoms:
            by_type[atom.atom_type.value] = by_type.get(atom.atom_type.value, 0) + 1
        print(f"  atoms: {len(atoms)}")
        if atom_warnings:
            print(f"  atom warnings: {len(atom_warnings)}")
            for warning in atom_warnings[:5]:
                print(f"    warning: {warning}")
        for atom_type, count in sorted(by_type.items()):
            print(f"    {atom_type}: {count}")
        _print_atom_samples(atoms)

        print("=== build graph ===")
        graph = await _build_graph(job_id, atoms)
        pipeline["graph"] = graph.model_dump()
        print(f"  edges={len(graph.edges)} roots={len(graph.roots)} warnings={len(graph.warnings)}")

        if skip_reader_probe:
            print("=== reader mode probe skipped ===")
            reader_annotation = {}
        else:
            print("=== reader mode probe (one atom) ===")
            reader_annotation = await _run_reader_probe(job_id, atoms)
        pipeline["reader_probe"] = reader_annotation

        review_atoms = [a for a in atoms if is_reviewable(a)]
        if max_review_atoms is not None:
            review_atoms = review_atoms[:max_review_atoms]
            print(f"=== review first {len(review_atoms)} reviewable atom(s) ===")
        else:
            print(f"=== review all {len(review_atoms)} reviewable atom(s) ===")

        verdicts = await _review_atoms(job_id, paper, review_atoms, graph)
        verdict_by_atom = {v.atom_id: v for v in verdicts}
        for atom in atoms:
            if atom.atom_id not in verdict_by_atom:
                verdicts.append(aggregate_verdict(atom, [], [], []))

        verdicts = apply_cascade(verdicts, graph)
        report = build_review_report(
            job_id=job_id,
            paper=paper,
            atoms=atoms,
            graph=graph,
            verdicts=verdicts,
            arxiv_id=ref.canonical,
            tex_path=str(assembled_path),
        )
        pipeline["verdicts"] = [v.model_dump() for v in verdicts]
        pipeline["report"] = report.model_dump()

    out_path = _save(pipeline, ref.canonical, tex_hash)
    summary = report.summary
    print("=== summary ===")
    print(
        f"  reviewed={summary.total_reviewed_atoms} no_objection={summary.no_objection_found} "
        f"contested={summary.contested} likely_flawed={summary.likely_flawed} "
        f"refuted={summary.refuted} not_checkable={summary.not_checkable}"
    )
    print(f"  output: {out_path}")
    return 0


async def _extract_atoms(job_id: str, paper: ParsedPaper) -> tuple[list[ResearchAtom], list[str]]:
    result = await AtomExtractorAgent().run(AgentContext(job_id=job_id, parsed_paper=paper))
    if result.status == "error":
        raise RuntimeError(f"atom extraction failed: {result.error}")
    atoms = [ResearchAtom.model_validate(a) for a in result.output.get("atoms", [])]
    if not atoms:
        raise RuntimeError("atom extraction produced zero atoms")
    warnings = [str(w) for w in result.output.get("warnings", [])]
    return atoms, warnings


async def _build_graph(job_id: str, atoms: list[ResearchAtom]) -> ResearchGraph:
    result = await GraphBuilderAgent().run(AgentContext(job_id=job_id, extra={"atoms": atoms}))
    graph = result.output.get("graph")
    if graph is None:
        raise RuntimeError(f"graph builder produced no graph: {result.error}")
    return ResearchGraph.model_validate(graph)


async def _review_atoms(
    job_id: str,
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
) -> list[AtomVerdict]:
    challenge_agent = ChallengeAgent()
    defense_agent = DefenseAgent()
    semaphore = asyncio.Semaphore(max(1, settings.max_parallel_claims))

    async def review_one(atom: ResearchAtom) -> AtomVerdict:
        async with semaphore:
            checks: list[CheckResult] = []
            alg = run_algebraic_sanity(atom, paper)
            cite = run_citation_probe(atom)
            try:
                num = await run_numeric_probe(atom)
            except Exception as exc:  # noqa: BLE001
                num = CheckResult(
                    check_id=f"check_num_{atom.atom_id}_err",
                    atom_id=atom.atom_id,
                    kind=CheckKind.NUMERIC_COUNTEREXAMPLE_PROBE,
                    status=CheckStatus.INCONCLUSIVE,
                    summary=f"numeric probe error: {exc}",
                    confidence=0.0,
                    error=str(exc),
                )
            checks = [alg, num, cite]

            ctx = AgentContext(
                job_id=job_id,
                parsed_paper=paper,
                atom=atom,
                graph=graph,
                checks=checks,
            )
            ch_result = await challenge_agent.run(ctx)
            challenges = [
                Challenge.model_validate(c)
                for c in ch_result.output.get("challenges", [])
            ]

            rebuttals: list[Rebuttal] = []
            if challenges:
                df_result = await defense_agent.run(
                    AgentContext(
                        job_id=job_id,
                        parsed_paper=paper,
                        atom=atom,
                        graph=graph,
                        checks=checks,
                        challenges=challenges,
                    )
                )
                rebuttals = [
                    Rebuttal.model_validate(r)
                    for r in df_result.output.get("rebuttals", [])
                ]

            verdict = aggregate_verdict(atom, checks, challenges, rebuttals)
            print(
                f"  {atom.atom_id}: {atom.atom_type.value} -> {verdict.label.value} "
                f"(checks={len(checks)} challenges={len(challenges)} rebuttals={len(rebuttals)})"
            )
            return verdict

    results = await asyncio.gather(*(review_one(atom) for atom in atoms), return_exceptions=True)
    verdicts: list[AtomVerdict] = []
    for atom, result in zip(atoms, results):
        if isinstance(result, Exception):
            print(f"  {atom.atom_id}: review error: {result}")
            verdicts.append(aggregate_verdict(atom, [], [], []))
        else:
            verdicts.append(result)
    return verdicts


async def _run_reader_probe(job_id: str, atoms: list[ResearchAtom]) -> dict[str, Any]:
    """Run all five Reader Mode agents on the most important available atom."""
    from models import AtomImportance  # noqa: PLC0415

    priority = [AtomImportance.CORE, AtomImportance.HIGH, AtomImportance.MEDIUM, AtomImportance.LOW]
    probe_atom: Optional[ResearchAtom] = None
    for importance in priority:
        candidates = [a for a in atoms if a.importance == importance]
        if candidates:
            probe_atom = candidates[0]
            break
    if probe_atom is None:
        print("  no atoms to probe")
        return {}

    print(f"  probing atom: {probe_atom.atom_id} [{probe_atom.atom_type.value}] {probe_atom.text[:80]!r}")

    ctx = AgentContext(
        job_id=job_id,
        atom=probe_atom,
        extra={"comprehension_level": "graduate"},
    )

    explainer, prereqs, glossary, exercises = await asyncio.gather(
        ExplainerAgent().run(ctx),
        PrerequisiteMapperAgent().run(ctx),
        GlossaryAgent().run(ctx),
        ExerciseGeneratorAgent().run(ctx),
    )

    tutor_ctx = AgentContext(
        job_id=job_id,
        atom=probe_atom,
        extra={
            "user_message": "What is the key insight of this atom and why does it matter?",
            "history": [],
        },
    )
    tutor = await SocraticTutorAgent().run(tutor_ctx)

    for label, result in [
        ("explainer", explainer),
        ("prerequisites", prereqs),
        ("glossary", glossary),
        ("exercises", exercises),
        ("tutor", tutor),
    ]:
        status = result.status
        err = f" ({result.error})" if result.error else ""
        print(f"    {label}: {status}{err}")

    return {
        "atom_id": probe_atom.atom_id,
        "atom_type": probe_atom.atom_type.value,
        "comprehension_level": "graduate",
        "explainer": explainer.output,
        "prerequisites": prereqs.output,
        "glossary": glossary.output,
        "exercises": exercises.output,
        "tutor": tutor.output,
    }


def _print_atom_samples(atoms: list[ResearchAtom], limit: int = 12) -> None:
    print("  sample atoms for manual extraction review:")
    for atom in atoms[:limit]:
        text = " ".join(atom.text.split())
        print(
            f"    {atom.atom_id} [{atom.atom_type.value}, {atom.section_heading or '?'}] "
            f"{text[:170]}"
        )


def _save(data: dict[str, Any], arxiv_id: str, tex_hash: str) -> Path:
    out_dir = BACKEND / "outputs"
    out_dir.mkdir(exist_ok=True)
    safe_name = arxiv_id.replace("/", "_").replace(".", "_")
    out_path = out_dir / f"{safe_name}_{tex_hash}_pipeline.json"
    safe = json.loads(json.dumps(data, default=str))
    out_path.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def _papers_from_file(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


async def main_async(args: argparse.Namespace) -> int:
    papers = list(args.arxiv_url or [])
    if args.papers_file:
        papers.extend(_papers_from_file(Path(args.papers_file)))
    if not papers:
        print("Provide an arXiv URL/id or --papers-file.")
        return 1

    exit_code = 0
    for paper in papers:
        try:
            exit_code = max(
                exit_code,
                await run_one(
                    paper,
                    args.max_review_atoms,
                    skip_reader_probe=args.skip_reader_probe,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"\n{paper}: pipeline failed: {exc}")
            exit_code = 1
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arxiv_url", nargs="*", help="arXiv URL(s) or bare arXiv id(s)")
    parser.add_argument("--papers-file", help="File containing arXiv URLs/ids, one per line")
    parser.add_argument(
        "--max-review-atoms",
        type=int,
        default=None,
        help="Optional cap for the expensive check/challenge/defense stage.",
    )
    parser.add_argument(
        "--skip-reader-probe",
        action="store_true",
        help="Skip the reader-mode LLM probe during extraction/graph smoke tests.",
    )
    return asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
