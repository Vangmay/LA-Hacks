"""Review-mode API endpoints for arXiv TeX source jobs."""

import asyncio
import logging
import os

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from core.event_bus import event_bus
from core.job_store import job_store
from core.orchestrators.review import ReviewOrchestrator
from ingestion.arxiv import ArxivSourceError, fetch_arxiv_source, parse_arxiv_url

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = ReviewOrchestrator()

_JOB_ROOT = "/tmp/papercourt"


class ArxivSubmission(BaseModel):
    arxiv_url: str


@router.post("")
async def submit_review(arxiv_url: str = Form(...)):
    """Submit an arXiv URL/id for TeX-source review via form data."""
    return await _submit_arxiv_review(arxiv_url)


@router.post("/arxiv")
async def submit_review_arxiv(submission: ArxivSubmission):
    """Submit an arXiv URL/id for TeX-source review via JSON."""
    return await _submit_arxiv_review(submission.arxiv_url)


async def _submit_arxiv_review(arxiv_url: str):
    """Create a review job from an arXiv URL/id and queue orchestration."""
    ref = parse_arxiv_url(arxiv_url)
    if not ref:
        raise HTTPException(status_code=400, detail=f"unrecognized arxiv url: {arxiv_url!r}")

    job_id = job_store.create_job(mode="review", filename=f"{ref.canonical}.tex")
    event_bus.create_channel(job_id)
    job_dir = os.path.join(_JOB_ROOT, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        source = await fetch_arxiv_source(ref, job_dir)
    except ArxivSourceError as e:
        logger.warning("arxiv source ingestion failed for %s: %s", ref.canonical, e)
        job_store.update(job_id, status="error", error=f"source ingestion failed: {e}")
        raise HTTPException(status_code=502, detail=f"arxiv source ingestion failed: {e}") from e
    except Exception as e:
        logger.exception("arxiv source fetch failed for %s", ref.canonical)
        job_store.update(job_id, status="error", error=f"fetch failed: {e}")
        raise HTTPException(status_code=502, detail=f"arxiv source fetch failed: {e}") from e

    assembled_path = os.path.join(job_dir, f"{ref.canonical}.assembled.tex")
    with open(assembled_path, "w", encoding="utf-8") as fh:
        fh.write(source.tex_text)

    job_store.update(
        job_id,
        arxiv_id=ref.canonical,
        arxiv_source_url=source.source_url,
        parser_kind="tex",
        tex_path=assembled_path,
        source_archive_path=source.archive_path,
        source_extract_dir=source.extract_dir,
        main_tex_path=source.main_tex_path,
        tex_paths=source.tex_paths,
    )

    asyncio.create_task(_orchestrator.run(job_id))
    return {
        "job_id": job_id,
        "status": "queued",
        "parser_kind": "tex",
        "arxiv_id": ref.canonical,
        "source_url": source.source_url,
    }


@router.get("/{job_id}/status")
async def get_status(job_id: str):
    """Return queue and progress metadata for a review job."""
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = job_store.get(job_id)
    return {
        "status": job.get("status", "unknown"),
        "completed_atoms": job.get("completed_atoms", 0),
        "total_atoms": job.get("total_atoms", 0),
        "paper_id": job.get("paper_id"),
        "paper_title": job.get("paper_title"),
        "error": job.get("error"),
    }


@router.get("/{job_id}/stream")
async def stream(job_id: str):
    """Stream review DAG events for a job."""
    async def event_gen():
        async for event in event_bus.subscribe(job_id):
            yield {"event": "dag_update", "data": event.model_dump_json()}

    return EventSourceResponse(event_gen())


@router.get("/{job_id}/report")
async def get_report(job_id: str):
    """Return the completed review report for a job."""
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = job_store.get(job_id)
    if job.get("status") != "complete":
        raise HTTPException(status_code=202, detail="Review in progress")
    report = job.get("report")
    if not report:
        raise HTTPException(status_code=500, detail="Review report missing")
    return report


@router.get("/{job_id}/dag")
async def get_dag(job_id: str):
    """Return the latest DAG snapshot for a review job."""
    if not job_store.exists(job_id):
        return {"nodes": [], "edges": []}
    job = job_store.get(job_id) or {}
    if job.get("dag_snapshot"):
        return job["dag_snapshot"]
    return {"nodes": [], "edges": []}


@router.get("/{job_id}/atoms/{atom_id}")
async def get_atom(job_id: str, atom_id: str):
    """Return one source-grounded atom plus its verdict when available."""
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = job_store.get(job_id) or {}
    atom = next((a for a in job.get("atoms", []) if a.get("atom_id") == atom_id), None)
    if atom is None:
        raise HTTPException(status_code=404, detail=f"Atom {atom_id} not found")
    verdict = next((v for v in job.get("verdicts", []) if v.get("atom_id") == atom_id), None)
    return {"atom": atom, "verdict": verdict}


@router.get("/{job_id}/report/markdown", response_class=PlainTextResponse)
async def get_markdown_report(job_id: str):
    """Return the completed review report as markdown."""
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = job_store.get(job_id)
    if job.get("status") != "complete":
        raise HTTPException(status_code=202, detail="Review in progress")
    report = job.get("report") or {}
    markdown = report.get("markdown_report")
    if not markdown:
        raise HTTPException(status_code=500, detail="Markdown report missing")
    return markdown
