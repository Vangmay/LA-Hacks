"""PoC-mode API endpoints.

PoC ingestion is now arXiv-source-grounded: a submission carries an
arXiv URL/id, the API fetches and assembles the e-print TeX bundle,
records the source paths on the job, and hands off to ``poc.orchestrator``
which parses the TeX, extracts research atoms, and runs the PoC-specific
filter/metric/scaffold pipeline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agents.base import AgentContext
from core.event_bus import event_bus
from core.job_store import job_store
from ingestion.arxiv import ArxivSourceError, fetch_arxiv_source, parse_arxiv_url
from poc.agents.reproducibility_report import ReproducibilityReportAgent
from poc.agents.results_analyzer import ResultsAnalyzerAgent
from poc.orchestrator import PoCOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = PoCOrchestrator()

_JOB_ROOT = "/tmp/papercourt"


class ArxivSubmission(BaseModel):
    arxiv_url: str


# ── POST /poc ──────────────────────────────────────────────────────────────────


@router.post("")
async def submit_poc(
    request: Request,
    arxiv_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Submit an arXiv URL/id for a PoC job.

    Accepts ``{arxiv_url: ...}`` JSON or a form-encoded ``arxiv_url`` field.
    Legacy file uploads are rejected — PoC is now TeX-source-grounded.
    """
    submitted_url = arxiv_url
    if submitted_url is None:
        try:
            body = await request.json()
        except (json.JSONDecodeError, ValueError):
            body = None
        if isinstance(body, dict):
            submitted_url = body.get("arxiv_url")

    if not submitted_url:
        if file is not None:
            raise HTTPException(
                status_code=400,
                detail="PoC mode now requires an arxiv_url; PDF uploads are no longer accepted.",
            )
        raise HTTPException(status_code=400, detail="arxiv_url is required")

    return await _submit_arxiv_poc(submitted_url)


async def _submit_arxiv_poc(arxiv_url: str) -> dict:
    ref = parse_arxiv_url(arxiv_url)
    if not ref:
        raise HTTPException(status_code=400, detail=f"unrecognized arxiv url: {arxiv_url!r}")

    session_id = job_store.create_job(mode="poc", filename=f"{ref.canonical}.tex")
    if not event_bus.channel_exists(session_id):
        event_bus.create_channel(session_id)

    job_dir = os.path.join(_JOB_ROOT, session_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        source = await fetch_arxiv_source(ref, job_dir)
    except ArxivSourceError as e:
        logger.warning("arxiv source ingestion failed for %s: %s", ref.canonical, e)
        job_store.update(session_id, status="error", error=f"source ingestion failed: {e}")
        raise HTTPException(status_code=502, detail=f"arxiv source ingestion failed: {e}") from e
    except Exception as e:
        logger.exception("arxiv source fetch failed for %s", ref.canonical)
        job_store.update(session_id, status="error", error=f"fetch failed: {e}")
        raise HTTPException(status_code=502, detail=f"arxiv source fetch failed: {e}") from e

    assembled_path = os.path.join(job_dir, f"{ref.canonical}.assembled.tex")
    with open(assembled_path, "w", encoding="utf-8") as fh:
        fh.write(source.tex_text)

    job_store.update(
        session_id,
        arxiv_id=ref.canonical,
        arxiv_source_url=source.source_url,
        parser_kind="tex",
        tex_path=assembled_path,
        source_archive_path=source.archive_path,
        source_extract_dir=source.extract_dir,
        main_tex_path=source.main_tex_path,
        tex_paths=source.tex_paths,
    )

    asyncio.create_task(_orchestrator.run(session_id))
    return {
        "session_id": session_id,
        "status": "processing",
        "parser_kind": "tex",
        "arxiv_id": ref.canonical,
        "source_url": source.source_url,
    }


# ── GET /poc/sessions ─────────────────────────────────────────────────────────


@router.get("/sessions")
async def list_sessions():
    jobs = job_store.get_all(mode="poc")
    # Return reversed to show newest first
    sessions = []
    for j in reversed(jobs):
        sessions.append({
            "session_id": j.get("job_id"),
            "arxiv_id": j.get("arxiv_id", "unknown"),
            "title": j.get("paper_metadata", {}).get("title"),
            "status": j.get("status"),
        })
    return {"sessions": sessions}


# ── GET /poc/{session_id}/stream ───────────────────────────────────────────────


@router.get("/{session_id}/stream")
async def stream(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    async def event_gen():
        async for event in event_bus.subscribe(session_id):
            yield {
                "event": event.event_type.value,
                "data": json.dumps(event.payload),
                "id": event.event_id,
            }

    return EventSourceResponse(event_gen())


# ── GET /poc/{session_id}/claims ───────────────────────────────────────────────


@router.get("/{session_id}/claims")
async def list_claims(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    job = job_store.get(session_id)
    claims_map: dict = job.get("claims", {})
    poc_specs: dict = job.get("poc_specs", {})
    testable_ids = set(poc_specs.keys())

    claims_out = []
    for claim_id, claim_data in claims_map.items():
        spec = poc_specs.get(claim_id)
        spec_summary = (
            {k: v for k, v in spec.items() if k != "scaffold_files"} if spec else None
        )
        claims_out.append({
            "claim_id": claim_id,
            "text": claim_data.get("text", ""),
            "claim_type": claim_data.get("claim_type", ""),
            "section": claim_data.get("section"),
            "testability": "testable" if claim_id in testable_ids else "theoretical",
            "spec_summary": spec_summary,
        })

    return {
        "total": len(claims_out),
        "testable": len(testable_ids),
        "theoretical": len(claims_out) - len(testable_ids),
        "claims": claims_out,
    }


# ── GET /poc/{session_id}/claim/{claim_id}/spec ────────────────────────────────


@router.get("/{session_id}/claim/{claim_id}/spec")
async def get_spec(session_id: str, claim_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    poc_specs: dict = job_store.get(session_id).get("poc_specs", {})
    if claim_id not in poc_specs:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} is theoretical or not found")

    return poc_specs[claim_id]


# ── POST /poc/{session_id}/scaffold ───────────────────────────────────────────


class ScaffoldSelection(BaseModel):
    claim_ids: list[str]


@router.post("/{session_id}/scaffold")
async def generate_scaffolds(session_id: str, selection: ScaffoldSelection):
    """Trigger scaffold generation for a user-chosen subset of testable claims.

    Phase 1 (metrics) must already be complete; this returns 409 otherwise.
    Generation runs in the background; clients poll ``scaffold_status`` on
    the job or wait for the next report-ready SSE event before downloading
    ``/scaffold.zip``.
    """
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    job = job_store.get(session_id)
    if job.get("status") not in ("ready", "complete"):
        raise HTTPException(status_code=409, detail="Phase 1 not complete; metrics not ready")

    poc_specs: dict = job.get("poc_specs") or {}
    requested = [cid for cid in selection.claim_ids if cid]
    if not requested:
        raise HTTPException(status_code=400, detail="claim_ids must be a non-empty list")

    unknown = [cid for cid in requested if cid not in poc_specs]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"claim_ids not testable / no metrics extracted: {unknown}",
        )

    asyncio.create_task(_orchestrator.generate_scaffolds(session_id, requested))
    return {
        "status": "generating",
        "selected_claim_ids": requested,
    }


# ── GET /poc/{session_id}/scaffold/status ─────────────────────────────────────


@router.get("/{session_id}/scaffold/status")
async def get_scaffold_status(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    job = job_store.get(session_id)
    job_status = job.get("status")
    # Phase 1 has not finished while job is still 'processing'; only after the
    # orchestrator flips status to 'ready'/'complete' should the client see the
    # awaiting_selection state.
    scaffold_status = job.get("scaffold_status")
    if not scaffold_status:
        scaffold_status = (
            "awaiting_selection" if job_status in ("ready", "complete") else "phase_1"
        )
    return {
        "job_status": job_status,
        "scaffold_status": scaffold_status,
        "selected_claim_ids": job.get("selected_claim_ids", []),
        "scaffold_error": job.get("scaffold_error"),
        "zip_ready": bool(job.get("zip_path") and Path(job["zip_path"]).exists()),
    }


# ── GET /poc/{session_id}/scaffold.zip ────────────────────────────────────────


@router.get("/{session_id}/scaffold.zip")
async def get_scaffold_zip(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    job = job_store.get(session_id)
    zip_path: str = job.get("zip_path", "")

    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(status_code=202, detail="Scaffold not ready yet")

    paper_metadata: dict = job.get("paper_metadata", {})
    title = paper_metadata.get("title", session_id)
    safe = "".join(c if c.isalnum() else "_" for c in title)[:20]

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="poc_scaffold_{safe}.zip"'},
    )


# ── POST /poc/{session_id}/results ─────────────────────────────────────────────


@router.post("/{session_id}/results")
async def upload_results(
    session_id: str,
    request: Request,
    file: Optional[UploadFile] = File(None),
):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    raw = await file.read() if file is not None else await request.body()

    try:
        results_json = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {exc}")

    job = job_store.get(session_id)
    poc_specs = job.get("poc_specs", {})
    paper_metadata = job.get("paper_metadata", {})

    async def _analyze() -> None:
        try:
            analyzer_result = await ResultsAnalyzerAgent().run(
                AgentContext(
                    job_id=session_id,
                    extra={"results_json": results_json, "poc_specs": poc_specs},
                )
            )
            report_result = await ReproducibilityReportAgent().run(
                AgentContext(
                    job_id=session_id,
                    extra={
                        "session_id": session_id,
                        "experiment_results": analyzer_result.output.get("results", []),
                        "poc_specs": poc_specs,
                        "paper_metadata": paper_metadata,
                    },
                )
            )
            job_store.update(
                session_id,
                report=report_result.output.get("report", {}),
                analysis_status="complete",
            )
        except Exception as exc:
            logger.exception("Results analysis failed for %s", session_id)
            job_store.update(session_id, analysis_status="error", analysis_error=str(exc))

    job_store.update(session_id, analysis_status="analyzing")
    asyncio.create_task(_analyze())
    return {"status": "analyzing"}


# ── GET /poc/{session_id}/report ───────────────────────────────────────────────


@router.get("/{session_id}/report")
async def get_report(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    job = job_store.get(session_id)
    if job.get("analysis_status") != "complete":
        raise HTTPException(status_code=202, detail="Analysis in progress")

    report = job.get("report")
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


# ── GET /poc/{session_id}/report/markdown ─────────────────────────────────────


@router.get("/{session_id}/report/markdown")
async def get_report_markdown(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    job = job_store.get(session_id)
    if job.get("analysis_status") != "complete":
        raise HTTPException(status_code=202, detail="Analysis in progress")

    markdown = job.get("report", {}).get("markdown_report", "")
    return PlainTextResponse(content=markdown, media_type="text/markdown")


# ── GET /poc/{session_id}/dag ──────────────────────────────────────────────────


@router.get("/{session_id}/dag")
async def get_dag(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    job = job_store.get(session_id)
    dag = job.get("dag")
    poc_specs: dict = job.get("poc_specs", {})
    report: dict = job.get("report", {})

    # Build worst reproduction_status per claim from report results
    claim_statuses: dict = {}
    _rank = {"REPRODUCED": 0, "PARTIAL": 1, "FAILED": 2, "PENDING": -1}
    for result in report.get("results", []):
        cid = result["claim_id"]
        s = result["status"]
        if _rank.get(s, -1) > _rank.get(claim_statuses.get(cid, "PENDING"), -1):
            claim_statuses[cid] = s

    if not dag:
        return {"nodes": [], "edges": []}

    testable_ids = set(poc_specs.keys())

    nodes = [
        {
            "id": node_id,
            "testability": "testable" if node_id in testable_ids else "theoretical",
            "reproduction_status": claim_statuses.get(node_id, "PENDING"),
        }
        for node_id in dag.get("nodes", [])
    ]
    edges = [
        {"from": from_id, "to": to_id}
        for from_id, targets in (dag.get("edges") or {}).items()
        for to_id in targets
    ]

    return {"nodes": nodes, "edges": edges}
