import asyncio
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from core.event_bus import event_bus
from core.job_store import job_store
from core.orchestrators.review import ReviewOrchestrator
from utils.arxiv import ArxivSourceError, fetch_arxiv_source, parse_arxiv_url

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
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = job_store.get(job_id)
    return {
        "status": job.get("status", "unknown"),
        "completed_claims": job.get("completed_claims", 0),
        "total_claims": job.get("total_claims", 0),
    }


@router.get("/{job_id}/stream")
async def stream(job_id: str):
    async def event_gen():
        async for event in event_bus.subscribe(job_id):
            yield {"event": "dag_update", "data": event.model_dump_json()}

    return EventSourceResponse(event_gen())


@router.get("/{job_id}/report")
async def get_report(job_id: str):
    if not job_store.exists(job_id):
        # Allow report fetch on unknown ids to return a mock for scaffolding;
        # Person B will tighten this.
        return _mock_report()
    job = job_store.get(job_id)
    if job.get("status") != "complete":
        raise HTTPException(status_code=202, detail="Review in progress")
    return job.get("report") or _mock_report()


@router.get("/{job_id}/dag")
async def get_dag(job_id: str):
    if not job_store.exists(job_id):
        return {"nodes": [], "edges": []}
    job = job_store.get(job_id) or {}
    if job.get("dag_snapshot"):
        return job["dag_snapshot"]
    return {"nodes": [], "edges": []}


@router.get("/{job_id}/report/markdown", response_class=PlainTextResponse)
async def get_markdown_report(job_id: str):
    return "# Mock Report"


def _mock_report() -> dict:
    return {
        "paper_title": "Mock Paper",
        "paper_hash": "0" * 16,
        "reviewed_at": datetime.utcnow().isoformat(),
        "total_claims": 0,
        "supported": 0,
        "contested": 0,
        "refuted": 0,
        "cascaded_failures": 0,
        "verdicts": [],
        "dag_summary": {"nodes": [], "edges": []},
        "markdown_report": "# Mock Report",
    }
