import asyncio
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from sse_starlette.sse import EventSourceResponse

from core.job_store import job_store
from core.event_bus import event_bus
from core.orchestrators.poc import PoCOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = PoCOrchestrator()


@router.post("")
async def submit_poc(file: UploadFile = File(None)):
    session_id = job_store.create_job(mode="poc", filename=file.filename if file else None)
    event_bus.create_channel(session_id)
    asyncio.create_task(_orchestrator.run(session_id))
    return {"session_id": session_id, "status": "queued"}


@router.get("/{session_id}/claims")
async def list_claims(session_id: str):
    return {"total": 1, "testable": 1, "theoretical": 0, "claims": []}


@router.get("/{session_id}/claim/{claim_id}/spec")
async def get_spec(session_id: str, claim_id: str):
    return {
        "spec_id": "spec_001",
        "claim_id": claim_id,
        "testability": "testable",
        "success_criteria": [],
        "failure_criteria": [],
        "scaffold_files": {"README.md": "# Mock scaffold"},
        "readme": "Mock",
    }


@router.get("/{session_id}/scaffold.zip")
async def get_scaffold_zip(session_id: str):
    raise HTTPException(status_code=202, detail="not ready")


@router.post("/{session_id}/results")
async def upload_results(session_id: str, file: UploadFile = File(None)):
    return {"status": "analyzing"}


@router.get("/{session_id}/report")
async def get_report(session_id: str):
    if not job_store.exists(session_id):
        raise HTTPException(status_code=202, detail="not ready")
    job = job_store.get(session_id)
    if job.get("status") != "complete":
        raise HTTPException(status_code=202, detail="not ready")
    return job.get("report") or {
        "session_id": session_id,
        "paper_title": "Mock Paper",
        "total_testable_claims": 0,
        "reproduced": 0,
        "partial": 0,
        "failed": 0,
        "reproduction_rate": 0.0,
        "results": [],
        "gap_analyses": [],
        "what_to_try_next": [],
        "markdown_report": "# Mock reproducibility report",
    }


@router.get("/{session_id}/dag")
async def get_dag(session_id: str):
    return {"nodes": [], "edges": []}


@router.get("/{session_id}/stream")
async def stream(session_id: str):
    async def event_gen():
        yield {"event": "heartbeat", "data": "ok"}

    return EventSourceResponse(event_gen())
