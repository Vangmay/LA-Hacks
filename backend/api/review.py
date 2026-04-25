import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from core.event_bus import event_bus
from core.job_store import job_store
from core.orchestrators.review import ReviewOrchestrator
from utils.arxiv import fetch_paper, parse_arxiv_url

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = ReviewOrchestrator()

_JOB_ROOT = "/tmp/papercourt"


class ArxivSubmission(BaseModel):
    arxiv_url: str


@router.post("")
async def submit_review(
    file: Optional[UploadFile] = File(None),
    arxiv_url: Optional[str] = Form(None),
):
    """Submit a paper for review via either PDF upload or arXiv URL.

    Body forms:
      - multipart file upload as ``file`` field
      - form field ``arxiv_url`` (URL or bare arXiv id)
    """
    if file is None and not arxiv_url:
        raise HTTPException(
            status_code=400,
            detail="provide either a PDF file or arxiv_url",
        )

    job_id = job_store.create_job(
        mode="review",
        filename=file.filename if file else None,
    )
    event_bus.create_channel(job_id)
    job_dir = os.path.join(_JOB_ROOT, job_id)
    os.makedirs(job_dir, exist_ok=True)

    pdf_path: Optional[str] = None
    html_path: Optional[str] = None
    parser_kind: str = "pdf"
    arxiv_id: Optional[str] = None

    if arxiv_url:
        ref = parse_arxiv_url(arxiv_url)
        if not ref:
            raise HTTPException(status_code=400, detail=f"unrecognized arxiv url: {arxiv_url!r}")
        arxiv_id = ref.canonical
        try:
            fetched = await fetch_paper(ref, job_dir)
        except Exception as e:
            logger.exception("arxiv fetch failed for %s", ref.canonical)
            job_store.update(job_id, status="error", error=f"fetch failed: {e}")
            raise HTTPException(status_code=502, detail=f"arxiv fetch failed: {e}") from e
        pdf_path = fetched.pdf_path
        if fetched.html_text:
            html_path = os.path.join(job_dir, f"{ref.canonical}.html")
            with open(html_path, "w", encoding="utf-8") as fh:
                fh.write(fetched.html_text)
            parser_kind = "html"
        if not pdf_path and not html_path:
            job_store.update(job_id, status="error", error="arxiv returned no fetchable formats")
            raise HTTPException(status_code=502, detail="arxiv returned no fetchable formats")

    if file is not None:
        target = os.path.join(job_dir, "upload.pdf")
        contents = await file.read()
        with open(target, "wb") as fh:
            fh.write(contents)
        pdf_path = target
        parser_kind = "pdf"

    job_store.update(
        job_id,
        pdf_path=pdf_path,
        html_path=html_path,
        parser_kind=parser_kind,
        arxiv_id=arxiv_id,
    )

    asyncio.create_task(_orchestrator.run(job_id))
    return {
        "job_id": job_id,
        "status": "queued",
        "parser_kind": parser_kind,
        "arxiv_id": arxiv_id,
    }


@router.post("/arxiv")
async def submit_review_arxiv(submission: ArxivSubmission):
    """JSON-body convenience wrapper around POST /review with arxiv_url."""
    return await submit_review(file=None, arxiv_url=submission.arxiv_url)


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
        # Heartbeat once and close — real streaming added by Person B.
        yield {"event": "heartbeat", "data": "ok"}

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
