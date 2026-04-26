"""Research deep-dive API endpoints."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from research_deepdive import DeepDiveConfig, DeepDiveOrchestrator, DeepDiveRunRequest
from research_deepdive.event_bus import deepdive_event_bus
from research_deepdive.events import DeepDiveEvent, DeepDiveEventType
from research_deepdive.snapshots import (
    build_run_snapshot,
    list_run_summaries,
    research_workspace_root,
    resolve_artifact_path,
    resolve_run_root,
)

router = APIRouter()

_HEARTBEAT_INTERVAL_SECONDS = 15.0
_TERMINAL_EVENTS = {DeepDiveEventType.RUN_FINALIZED, DeepDiveEventType.RUN_ERROR}
_live_runs: dict[str, dict] = {}
_live_tasks: dict[str, asyncio.Task] = {}


class ResearchStartRequest(BaseModel):
    arxiv_url: str
    run_id: str | None = None
    paper_id: str | None = None
    section_titles: list[str] = Field(default_factory=list)
    research_brief: str = ""
    research_objective: Literal["literature_review", "novelty_ideation"] = "novelty_ideation"
    mode: Literal["dry_run", "live"] = "live"
    max_investigators: int | None = None
    subagents_per_investigator: int | None = None
    subagent_tool_calls: int | None = None
    max_parallel_subagents: int | None = None
    dynamic_roster_enabled: bool | None = None


@router.get("/runs")
async def list_runs():
    """List old and current research deep-dive runs discovered on disk."""
    return {"runs": list_run_summaries()}


@router.post("/start")
async def start_research(req: ResearchStartRequest):
    """Start a deep-dive run and return immediately."""
    return await _start_research(req)


@router.post("/runs")
async def create_run(req: ResearchStartRequest):
    """Alias for clients that model research runs as a collection."""
    return await _start_research(req)


@router.get("/{run_id}/snapshot")
async def get_snapshot(run_id: str):
    try:
        snapshot = build_run_snapshot(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Research run {run_id} not found") from None
    return snapshot


@router.get("/{run_id}/status")
async def get_status(run_id: str):
    live = _live_runs.get(run_id, {})
    try:
        summary = build_run_snapshot(run_id)["metadata"]
    except FileNotFoundError:
        if not live:
            raise HTTPException(status_code=404, detail=f"Research run {run_id} not found") from None
        summary = {}
    return {
        **summary,
        **{key: value for key, value in live.items() if key != "task"},
        "run_id": run_id,
    }


@router.get("/{run_id}/stream")
async def stream_run(request: Request, run_id: str):
    """Stream a live run, starting with a filesystem snapshot for late joiners."""
    if not resolve_run_root(run_id).exists() and run_id not in _live_runs:
        raise HTTPException(status_code=404, detail=f"Research run {run_id} not found")

    last_event_id = request.headers.get("last-event-id")

    async def event_gen():
        snapshot_event = _snapshot_event(run_id)
        yield _sse_payload(snapshot_event)
        if run_id not in _live_runs and not deepdive_event_bus.channel_exists(run_id):
            return

        queue: asyncio.Queue = asyncio.Queue()

        async def drain():
            try:
                async for event in deepdive_event_bus.subscribe(run_id, last_event_id):
                    await queue.put(event)
                    if event.type in _TERMINAL_EVENTS:
                        break
            finally:
                await queue.put(None)

        drain_task = asyncio.create_task(drain())
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_INTERVAL_SECONDS)
                except asyncio.TimeoutError:
                    yield {"comment": "heartbeat"}
                    continue
                if event is None:
                    break
                yield _sse_payload(event)
                if event.type in _TERMINAL_EVENTS:
                    break
        finally:
            drain_task.cancel()
            try:
                await drain_task
            except asyncio.CancelledError:
                pass

    return EventSourceResponse(event_gen())


@router.get("/{run_id}/artifacts/{artifact_path:path}")
async def get_artifact(run_id: str, artifact_path: str):
    try:
        path = resolve_artifact_path(run_id, artifact_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_path} not found")
    text = path.read_text(encoding="utf-8")
    return {
        "run_id": run_id,
        "path": artifact_path,
        "content": text,
        "char_count": len(text),
        "mtime": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


@router.get("/{run_id}/report")
async def get_report(run_id: str):
    path = resolve_run_root(run_id) / "final" / "research_deep_dive_report.md"
    if not path.exists():
        raise HTTPException(status_code=202, detail="Research report is not ready")
    markdown = path.read_text(encoding="utf-8")
    return {"run_id": run_id, "path": "final/research_deep_dive_report.md", "markdown": markdown}


@router.get("/{run_id}/report/markdown", response_class=PlainTextResponse)
async def get_report_markdown(run_id: str):
    path = resolve_run_root(run_id) / "final" / "research_deep_dive_report.md"
    if not path.exists():
        raise HTTPException(status_code=202, detail="Research report is not ready")
    return path.read_text(encoding="utf-8")


@router.get("/{run_id}/shared/{artifact}")
async def get_shared(run_id: str, artifact: str):
    filename = artifact if artifact.endswith(".md") else f"{artifact}.md"
    return await get_artifact(run_id, f"shared/{filename}")


@router.get("/{run_id}/critique/{critic_id}")
async def get_critique(run_id: str, critic_id: str):
    return await get_artifact(run_id, f"critique/{critic_id}/critique.md")


async def _start_research(req: ResearchStartRequest):
    run_id = req.run_id or "research_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if run_id in _live_tasks and not _live_tasks[run_id].done():
        raise HTTPException(status_code=409, detail=f"Research run {run_id} is already running")

    config = _config_from_request(req)
    deepdive_event_bus.create_channel(run_id)
    _live_runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "stage": "queued",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": "",
        "error": "",
        "mode": req.mode,
    }

    request = DeepDiveRunRequest(
        run_id=run_id,
        arxiv_url=req.arxiv_url,
        paper_id=req.paper_id or req.arxiv_url,
        section_titles=req.section_titles or ["Core method", "Experiments", "Related work and novelty"],
        research_brief=req.research_brief
        or (
            "Run a monitored literature deep dive. Search references, citations, recent work, "
            "prior work, critiques, and novelty-relevant neighboring papers. Write durable "
            "markdown memory before handoff."
        ),
        research_objective=req.research_objective,
        mode=req.mode,
    )
    orchestrator = DeepDiveOrchestrator(config=config, event_bus=deepdive_event_bus)
    task = asyncio.create_task(_run_background(orchestrator, request))
    _live_tasks[run_id] = task
    return {
        "run_id": run_id,
        "status": "queued",
        "workspace_path": str(resolve_run_root(run_id, config)),
        "stream_url": f"/research/{run_id}/stream",
    }


async def _run_background(orchestrator: DeepDiveOrchestrator, request: DeepDiveRunRequest) -> None:
    _live_runs[request.run_id]["status"] = "running"
    try:
        result = await orchestrator.run(request)
    except Exception as exc:
        _live_runs[request.run_id].update(
            {
                "status": "error",
                "stage": "error",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }
        )
        await deepdive_event_bus.publish(
            DeepDiveEvent(
                type=DeepDiveEventType.RUN_ERROR,
                run_id=request.run_id,
                payload={"run_id": request.run_id, "stage": "unknown", "error": str(exc)},
            )
        )
        return

    _live_runs[request.run_id].update(
        {
            "status": "completed" if result.status == "success" else "error",
            "stage": "completed" if result.status == "success" else "error",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error": result.error or "",
            "workspace_path": str(result.workspace_path),
            "final_report_path": str(result.final_report_path) if result.final_report_path else "",
        }
    )


def _config_from_request(req: ResearchStartRequest) -> DeepDiveConfig:
    base = DeepDiveConfig()
    updates = {"workspace_root": research_workspace_root(base)}
    if req.max_investigators is not None:
        updates["max_investigators"] = req.max_investigators
    if req.subagents_per_investigator is not None:
        updates.update(
            {
                "subagents_per_investigator": req.subagents_per_investigator,
                "min_personas_per_investigator": req.subagents_per_investigator,
                "max_personas_per_investigator": req.subagents_per_investigator,
            }
        )
    if req.subagent_tool_calls is not None:
        updates["subagent_max_tool_calls"] = req.subagent_tool_calls
    if req.max_parallel_subagents is not None:
        updates["max_parallel_subagents"] = req.max_parallel_subagents
    if req.dynamic_roster_enabled is not None:
        updates["dynamic_roster_enabled"] = req.dynamic_roster_enabled
    return base.model_copy(update=updates).normalized()


def _snapshot_event(run_id: str) -> DeepDiveEvent:
    try:
        snapshot = build_run_snapshot(run_id)
    except FileNotFoundError:
        snapshot = {"metadata": {"run_id": run_id, "status": "queued"}, "investigators": [], "subagents": []}
    return DeepDiveEvent(
        type=DeepDiveEventType.RUN_SNAPSHOT,
        run_id=run_id,
        payload={"snapshot": snapshot},
    )


def _sse_payload(event: DeepDiveEvent) -> dict:
    return {
        "event": "research_update",
        "id": event.event_id,
        "data": event.model_dump_json(),
    }
