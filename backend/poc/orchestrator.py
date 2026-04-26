"""PoC orchestrator wired to the v0.4 source-grounded ingestion path.

arXiv source bundle → assembled TeX → ParsedPaper → ResearchAtoms →
testability filter → metric extraction → scaffold generation → zip.

The orchestrator no longer touches PDFs. The API hands it a job whose
``tex_path`` already points at an assembled TeX document produced by
``ingestion.fetch_arxiv_source``; the orchestrator parses it the same
way the review pipeline does, then runs the PoC-specific agents over
the extracted atoms.
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import httpx

from agents.atom_extractor import AtomExtractorAgent
from agents.base import AgentContext
from config import settings
from core.event_bus import event_bus
from core.job_store import job_store
from ingestion import parse_tex
from models import (
    DAGEvent,
    DAGEventType,
    PaperSource,
    ResearchAtom,
    SourceKind,
    is_reviewable,
)
from poc.agents.claim_filter import ClaimFilterAgent
from poc.agents.metric_extractor import MetricExtractorAgent
from poc.agents.scaffold_generator import ScaffoldGeneratorAgent

logger = logging.getLogger(__name__)

_SCAFFOLD_FILES = (
    "implementation.py",
    "test_harness.py",
    "results_logger.py",
    "requirements.txt",
    "README.md",
)

_OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "poc"


def _poc_model() -> str:
    return settings.poc_scaffold_model or settings.openai_model


def _make_poc_client() -> "AsyncOpenAI":
    from openai import AsyncOpenAI
    api_key = (
        os.getenv(settings.poc_scaffold_api_key_env)
        or getattr(settings, settings.poc_scaffold_api_key_env.lower(), None)
        or settings.openai_api_key
    )
    base_url = (
        settings.poc_scaffold_base_url
        or settings.openai_base_url
        or None
    )
    kwargs: dict = {
        "api_key": api_key or "missing-api-key",
        "http_client": httpx.AsyncClient(
            timeout=settings.poc_scaffold_timeout_seconds,
            follow_redirects=True,
        ),
    }
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


class PoCOrchestrator:
    async def run(self, job_id: str, **kwargs) -> None:
        try:
            await self._run(job_id)
        except Exception as exc:
            logger.exception("PoC orchestrator failed for %s", job_id)
            job_store.update(job_id, status="error", error=str(exc))

    async def _run(self, job_id: str) -> None:
        job_store.set_status(job_id, "processing")
        job = job_store.get(job_id)

        if not event_bus.channel_exists(job_id):
            event_bus.create_channel(job_id)

        # ── 1. Parse TeX → ParsedPaper ────────────────────────────────────────
        tex_path = job.get("tex_path")
        if not tex_path:
            raise RuntimeError("PoC job has no tex_path; submit via /poc with arxiv_url")

        tex_text = Path(tex_path).read_text(encoding="utf-8", errors="replace")
        paper_source = _build_source(job)
        paper = parse_tex(tex_text, paper_source)

        paper_metadata = {
            "title": paper.title,
            "abstract": paper.abstract,
            "sections": [
                {"title": s.heading, "content": s.content}
                for s in paper.sections
            ],
        }
        job_store.update(
            job_id,
            paper_id=paper.paper_id,
            paper_title=paper.title,
            paper_metadata=paper_metadata,
            parsed_paper=paper.model_dump(),
        )

        # ── 2. Extract research atoms (replaces ClaimExtractorAgent) ──────────
        poc_client = _make_poc_client()
        poc_model = _poc_model()

        ext_result = await AtomExtractorAgent(
            client=poc_client, model=poc_model
        ).run(
            AgentContext(job_id=job_id, parsed_paper=paper)
        )
        if ext_result.status == "error":
            raise RuntimeError(f"atom extraction failed: {ext_result.error}")

        raw_atoms = ext_result.output.get("atoms") or []
        atoms = [ResearchAtom.model_validate(a) for a in raw_atoms]
        if not atoms:
            raise RuntimeError("atom extraction produced zero atoms")

        # PoC only wants atoms that look like real claims worth testing —
        # discard prose-only types like proof_step / example up front.
        candidate_atoms = [a for a in atoms if is_reviewable(a)] or atoms

        job_store.update(
            job_id,
            atoms=[a.model_dump() for a in atoms],
            claims={a.atom_id: _atom_to_claim_dict(a) for a in candidate_atoms},
        )

        # ── 3. Filter atoms (testable vs theoretical) ─────────────────────────
        filter_result = await ClaimFilterAgent(
            client=poc_client, model=poc_model
        ).run(
            AgentContext(job_id=job_id, extra={"atoms": candidate_atoms})
        )
        testable_ids: set = set(filter_result.output.get("testable", []))
        classifications: dict = filter_result.output.get("classifications", {})

        for atom in candidate_atoms:
            testability = "testable" if atom.atom_id in testable_ids else "theoretical"
            await event_bus.publish(job_id, DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=DAGEventType.ATOM_CREATED,
                payload={
                    "claim_id": atom.atom_id,
                    "atom_id": atom.atom_id,
                    "testability": testability,
                    "atom_type": atom.atom_type.value,
                    "section": atom.section_heading,
                    "reason": classifications.get(atom.atom_id, {}).get("reason", ""),
                },
                timestamp=datetime.utcnow(),
            ))

        # ── 4. Extract metrics in parallel for ALL candidate atoms ────────────
        metric_results = await asyncio.gather(
            *[
                MetricExtractorAgent(client=poc_client, model=poc_model).run(
                    AgentContext(
                        job_id=job_id,
                        parsed_paper=paper,
                        atom=atom,
                        extra={"paper_metadata": paper_metadata},
                    )
                )
                for atom in candidate_atoms
            ],
            return_exceptions=True,
        )

        poc_specs: dict = {}
        for atom, result in zip(candidate_atoms, metric_results):
            if isinstance(result, Exception):
                logger.warning("MetricExtractorAgent failed for %s: %s", atom.atom_id, result)
                continue
            if result.status in ("success", "inconclusive"):
                poc_specs[atom.atom_id] = result.output

        # Phase 1 stops here. Scaffolds are generated on demand via
        # ``generate_scaffolds`` once the user picks which atoms to test.
        job_store.update(
            job_id,
            poc_specs=poc_specs,
            claims={a.atom_id: _atom_to_claim_dict(a) for a in candidate_atoms},
            dag=_build_dag(candidate_atoms),
            scaffold_status="awaiting_selection",
        )

        job_store.set_status(job_id, "ready")

    async def generate_scaffolds(self, job_id: str, claim_ids: list[str]) -> None:
        """Phase 2: generate LLM scaffolds for the selected atoms and zip them.

        Updates ``scaffold_status`` to ``generating`` while running and
        ``ready`` once a zip exists. The zip only contains the selected atoms.
        """
        try:
            await self._generate_scaffolds(job_id, claim_ids)
        except Exception as exc:
            logger.exception("PoC scaffold generation failed for %s", job_id)
            job_store.update(
                job_id,
                scaffold_status="error",
                scaffold_error=str(exc),
            )

    async def _generate_scaffolds(self, job_id: str, claim_ids: list[str]) -> None:
        job = job_store.get(job_id)
        if not job:
            raise RuntimeError(f"job {job_id} not found")

        poc_specs: dict = dict(job.get("poc_specs") or {})
        atoms_raw: list = job.get("atoms") or []
        atoms_by_id = {a["atom_id"]: ResearchAtom.model_validate(a) for a in atoms_raw}
        paper_metadata: dict = job.get("paper_metadata") or {}

        selected = [cid for cid in claim_ids if cid in poc_specs and cid in atoms_by_id]
        if not selected:
            raise RuntimeError("no selected claim_ids match testable atoms with metrics")

        job_store.update(
            job_id,
            scaffold_status="generating",
            selected_claim_ids=selected,
        )

        semaphore = asyncio.Semaphore(settings.max_parallel_claims)

        async def _scaffold_one(atom: ResearchAtom, spec: dict) -> tuple:
            async with semaphore:
                result = await ScaffoldGeneratorAgent().run(
                    AgentContext(
                        job_id=job_id,
                        atom=atom,
                        extra={"poc_spec": spec, "paper_metadata": paper_metadata},
                    )
                )
                return atom.atom_id, result

        scaffold_results = await asyncio.gather(
            *[_scaffold_one(atoms_by_id[cid], poc_specs[cid]) for cid in selected],
            return_exceptions=True,
        )

        for item in scaffold_results:
            if isinstance(item, Exception):
                logger.warning("ScaffoldGeneratorAgent raised: %s", item)
                continue
            atom_id, result = item
            # Always merge whatever scaffold_files we got (even when the LLM
            # returned syntactically broken code) so the user gets the best
            # available draft to edit.
            spec_from_result = result.output.get("poc_spec")
            scaffold_files = result.output.get("scaffold_files") or {}
            if spec_from_result:
                poc_specs[atom_id] = spec_from_result
            elif scaffold_files:
                merged = dict(poc_specs.get(atom_id) or {})
                merged["scaffold_files"] = scaffold_files
                merged["readme"] = scaffold_files.get("README.md", "")
                poc_specs[atom_id] = merged

            await event_bus.publish(job_id, DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=DAGEventType.CHECK_COMPLETE,
                payload={"claim_id": atom_id, "atom_id": atom_id, "status": result.status},
                timestamp=datetime.utcnow(),
            ))

        # Zip only the selected atoms so the download matches the user's choice.
        selected_specs = {cid: poc_specs[cid] for cid in selected if cid in poc_specs}
        zip_path = await self._build_zip(job_id, selected_specs, paper_metadata)

        job_store.update(
            job_id,
            poc_specs=poc_specs,
            zip_path=zip_path,
            scaffold_status="ready",
        )

        await event_bus.publish(job_id, DAGEvent(
            event_id=str(uuid.uuid4()),
            job_id=job_id,
            event_type=DAGEventType.REPORT_READY,
            payload={"zip_path": zip_path, "selected_count": len(selected)},
            timestamp=datetime.utcnow(),
        ))

    async def _build_zip(self, job_id: str, poc_specs: dict, paper_metadata: dict) -> str:
        _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = str(_OUTPUTS_DIR / f"{job_id}_scaffold.zip")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("poc_scaffold/README.md", self._root_readme(poc_specs, paper_metadata))
            for atom_id, spec in poc_specs.items():
                scaffold_files = spec.get("scaffold_files", {})
                for filename in _SCAFFOLD_FILES:
                    content = scaffold_files.get(filename, "")
                    zf.writestr(f"poc_scaffold/{atom_id}/{filename}", content)

        with open(zip_path, "wb") as f:
            f.write(buf.getvalue())

        return zip_path

    def _root_readme(self, poc_specs: dict, paper_metadata: dict) -> str:
        title = paper_metadata.get("title", "Unknown Paper")
        entries = "\n".join(f"- `poc_scaffold/{aid}/`" for aid in poc_specs)
        return (
            f"# PoC Scaffold — {title}\n\n"
            "This archive contains proof-of-concept scaffolds for each testable atom.\n\n"
            "## Atoms included\n\n"
            f"{entries or '_(none)_'}\n\n"
            "## Running a scaffold\n\n"
            "```bash\n"
            "cd poc_scaffold/<atom_id>\n"
            "pip install -r requirements.txt\n"
            "pytest test_harness.py -v\n"
            "```\n\n"
            "## Uploading results\n\n"
            "After running tests, upload `poc_results.json`:\n"
            "`POST /poc/{session_id}/results`\n"
        )


def _atom_to_claim_dict(atom: ResearchAtom) -> dict:
    """Project a ResearchAtom into the ``claim``-shaped dict the PoC API surfaces.

    The frontend still speaks in ``claim_id`` / ``text`` / ``claim_type``; using
    atom_id as claim_id keeps that vocabulary stable while pointing at the
    underlying source-grounded atom.
    """
    return {
        "claim_id": atom.atom_id,
        "atom_id": atom.atom_id,
        "text": atom.text,
        "claim_type": atom.atom_type.value,
        "section": atom.section_heading,
        "section_id": atom.section_id,
        "equations": [eq.equation_id for eq in atom.equations],
        "citations": [c.citation_id for c in atom.citations],
        "importance": atom.importance.value,
        "source_excerpt": atom.source_span.raw_excerpt[:500],
    }


def _build_dag(atoms: list[ResearchAtom]) -> dict:
    """Minimal DAG payload: nodes only. PoC mode does not infer edges."""
    return {
        "nodes": [a.atom_id for a in atoms],
        "edges": {},
    }


def _build_source(job: dict) -> PaperSource:
    arxiv_id = job.get("arxiv_id")
    paper_id = arxiv_id or job.get("filename") or "unknown"
    return PaperSource(
        paper_id=paper_id,
        source_kind=SourceKind.ARXIV if arxiv_id else SourceKind.MANUAL_TEX,
        arxiv_id=arxiv_id,
        source_url=job.get("arxiv_source_url"),
        abs_url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None,
        source_archive_path=job.get("source_archive_path"),
        source_extract_dir=job.get("source_extract_dir"),
        main_tex_path=job.get("main_tex_path"),
        assembled_tex_path=job.get("tex_path"),
        fetched_at=datetime.utcnow(),
        content_hash="0" * 16,
    )
