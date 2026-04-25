import asyncio
import logging
import os
import tempfile
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from agents.base import AgentContext
from agents.claim_extractor import ClaimExtractorAgent
from agents.dag_builder import DAGBuilderAgent
from agents.parser import ParserAgent
from core.event_bus import event_bus
from core.job_store import job_store
from core.orchestrators.review import ReviewOrchestrator
from models import DAGEvent, DAGEventType

logger = logging.getLogger(__name__)
router = APIRouter()

_orchestrator = ReviewOrchestrator()
_parser = ParserAgent()
_claim_extractor = ClaimExtractorAgent()
_dag_builder = DAGBuilderAgent()

_TMP_DIR = os.path.join(tempfile.gettempdir(), "papercourt")


async def _run_pipeline(job_id: str, pdf_path: str) -> None:
    try:
        job_store.set_status(job_id, "parsing")
        parse_result = await _parser.run(AgentContext(job_id=job_id, extra={"pdf_path": pdf_path}))
        if parse_result.status == "error":
            job_store.update(job_id, status="error", error=f"parsing failed: {parse_result.error}")
            return

        job_store.set_status(job_id, "extracting")
        extract_result = await _claim_extractor.run(
            AgentContext(job_id=job_id, extra={"parser_output": parse_result.output})
        )
        if extract_result.status == "error":
            job_store.update(job_id, status="error", error=f"extraction failed: {extract_result.error}")
            return

        claims = extract_result.output.get("claims", [])
        job_store.update(job_id, total_claims=len(claims))

        dag_result = await _dag_builder.run(
            AgentContext(job_id=job_id, extra={"claims": claims})
        )
        dag_obj = dag_result.output.get("dag")
        dag_dict = dag_obj.to_dict() if dag_obj else {"nodes": [], "edges": []}

        for node_id in dag_dict.get("nodes", []):
            await event_bus.publish(job_id, DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=DAGEventType.NODE_CREATED,
                claim_id=node_id,
                payload={"claim_id": node_id},
                timestamp=datetime.utcnow(),
            ))

        job_store.update(job_id, dag=dag_dict, claims=claims, node_verdicts={})

        job_store.set_status(job_id, "reviewing")
        await _orchestrator.run(job_id, pdf_path=pdf_path, claims=claims, dag=dag_obj)

        await event_bus.publish(job_id, DAGEvent(
            event_id=str(uuid.uuid4()),
            job_id=job_id,
            event_type=DAGEventType.REVIEW_COMPLETE,
            claim_id=None,
            payload={"total_claims": len(claims)},
            timestamp=datetime.utcnow(),
        ))

        if job_store.get(job_id).get("status") not in ("complete", "error"):
            job_store.set_status(job_id, "complete")

    except Exception as e:
        logger.exception("Pipeline failed for job %s", job_id)
        job_store.update(job_id, status="error", error=str(e))


@router.post("")
async def submit_review(file: UploadFile = File(...)):
    os.makedirs(_TMP_DIR, exist_ok=True)
    job_id = job_store.create_job(mode="review", filename=file.filename)
    if not event_bus.channel_exists(job_id):
        event_bus.create_channel(job_id)

    pdf_path = os.path.join(_TMP_DIR, f"{job_id}.pdf")
    content = await file.read()
    with open(pdf_path, "wb") as fh:
        fh.write(content)

    asyncio.create_task(_run_pipeline(job_id, pdf_path))
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}/status")
async def get_status(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job {job_id} not found", "job_id": job_id},
        )
    job = job_store.get(job_id)
    return {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "completed_claims": job.get("completed_claims", 0),
        "total_claims": job.get("total_claims", 0),
    }


@router.get("/{job_id}/stream")
async def stream_events(request: Request, job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job {job_id} not found", "job_id": job_id},
        )

    last_event_id = request.headers.get("last-event-id")

    async def event_gen():
        queue: asyncio.Queue = asyncio.Queue()

        async def drain():
            try:
                async for event in event_bus.subscribe(job_id, last_event_id):
                    await queue.put(event)
                    if event.event_type == DAGEventType.REVIEW_COMPLETE:
                        break
            finally:
                await queue.put(None)

        drain_task = asyncio.create_task(drain())
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event is None:
                        break
                    yield {
                        "event": "dag_update",
                        "id": event.event_id,
                        "data": event.model_dump_json(),
                    }
                    if event.event_type == DAGEventType.REVIEW_COMPLETE:
                        break
                except asyncio.TimeoutError:
                    yield {"comment": "heartbeat"}
        finally:
            drain_task.cancel()
            try:
                await drain_task
            except asyncio.CancelledError:
                pass

    return EventSourceResponse(event_gen())


@router.get("/{job_id}/report")
async def get_report(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job {job_id} not found", "job_id": job_id},
        )
    job = job_store.get(job_id)
    if job.get("status") != "complete":
        raise HTTPException(
            status_code=202,
            detail={"error": "Review in progress", "job_id": job_id},
        )
    report = job.get("report")
    if not report:
        raise HTTPException(
            status_code=404,
            detail={"error": "Report not yet available", "job_id": job_id},
        )
    return report


@router.get("/{job_id}/dag")
async def get_dag(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job {job_id} not found", "job_id": job_id},
        )
    job = job_store.get(job_id)
    dag = job.get("dag") or {"nodes": [], "edges": []}
    node_verdicts = job.get("node_verdicts") or {}

    nodes = [
        {"id": node_id, **({"verdict": node_verdicts[node_id]} if node_id in node_verdicts else {})}
        for node_id in dag.get("nodes", [])
    ]
    return {"nodes": nodes, "edges": dag.get("edges", [])}


@router.get("/{job_id}/report/markdown", response_class=PlainTextResponse)
async def get_markdown_report(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job {job_id} not found", "job_id": job_id},
        )
    job = job_store.get(job_id)
    if job.get("status") != "complete":
        raise HTTPException(
            status_code=202,
            detail={"error": "Review in progress", "job_id": job_id},
        )
    report = job.get("report") or {}
    return report.get("markdown_report") or "# No report available"
