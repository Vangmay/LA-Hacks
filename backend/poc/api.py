import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from backend.agents.base import AgentContext
from backend.poc.agents.reproducibility_report import ReproducibilityReportAgent
from backend.poc.agents.results_analyzer import ResultsAnalyzerAgent
from backend.core.event_bus import event_bus
from backend.core.job_store import job_store
from backend.poc.orchestrator import PoCOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = PoCOrchestrator()


# ── POST /poc ──────────────────────────────────────────────────────────────────

@router.post("")
async def submit_poc(file: Optional[UploadFile] = File(None)):
    pdf_path = ""
    filename = None

    if file is not None:
        filename = file.filename
        contents = await file.read()
        suffix = Path(filename).suffix if filename else ".pdf"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(contents)
        tmp.close()
        pdf_path = tmp.name

    session_id = job_store.create_job(mode="poc", filename=filename, pdf_path=pdf_path)
    if not event_bus.channel_exists(session_id):
        event_bus.create_channel(session_id)
    asyncio.create_task(_orchestrator.run(session_id))
    return {"session_id": session_id, "status": "processing"}


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

    if dag is None:
        return {"nodes": [], "edges": []}

    testable_ids = set(poc_specs.keys())

    nodes = [
        {
            "id": node_id,
            "testability": "testable" if node_id in testable_ids else "theoretical",
            "reproduction_status": claim_statuses.get(node_id, "PENDING"),
        }
        for node_id in dag.nodes
    ]
    edges = [
        {"from": from_id, "to": to_id}
        for from_id, targets in dag.edges.items()
        for to_id in targets
    ]

    return {"nodes": nodes, "edges": edges}
