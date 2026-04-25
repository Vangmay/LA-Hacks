import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from core.job_store import job_store
from core.event_bus import event_bus
from core.orchestrators.review import ReviewOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = ReviewOrchestrator()


@router.post("")
async def submit_review(file: UploadFile = File(None)):
    job_id = job_store.create_job(mode="review", filename=file.filename if file else None)
    event_bus.create_channel(job_id)
    asyncio.create_task(_orchestrator.run(job_id))
    return {"job_id": job_id, "status": "queued"}


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
