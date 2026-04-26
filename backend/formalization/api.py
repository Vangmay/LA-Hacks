from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from formalization.context_builder import (
    FormalizationContextError,
    load_review_job,
    rehydrate_job,
    validate_atom_selection,
)
from formalization.event_bus import formalization_event_bus
from formalization.events import FormalizationEvent, FormalizationEventType
from formalization.config import formalization_settings
from formalization.models import FormalizationOptions
from formalization.orchestrator import FormalizationOrchestrator
from formalization.outputs import merged_lean
from formalization.store import formalization_store
from core.sse import LoopSafeEventSourceResponse

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = FormalizationOrchestrator()
_TERMINAL_EVENT_TYPES = {
    FormalizationEventType.RUN_COMPLETE,
    FormalizationEventType.RUN_ERROR,
}
_HEARTBEAT_INTERVAL_SECONDS = 15.0


class FormalizationStartResponse(BaseModel):
    run_id: str
    status: str
    selected_atom_ids: list[str] = Field(default_factory=list)
    runtime: dict = Field(default_factory=dict)


@router.post("/{job_id}", response_model=FormalizationStartResponse)
async def start_formalization(job_id: str, request: Optional[FormalizationOptions] = None):
    return await _create_run(job_id, atom_ids=request.atom_ids if request else None, options=request.options if request else {})


@router.post("/{job_id}/atom/{atom_id}", response_model=FormalizationStartResponse)
async def start_atom_formalization(job_id: str, atom_id: str, request: Optional[FormalizationOptions] = None):
    options = request.options if request else {}
    return await _create_run(job_id, atom_ids=[atom_id], options=options)


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = formalization_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Formalization run {run_id} not found")
    return run.model_dump()


@router.get("/runs/{run_id}/atom/{atom_id}")
async def get_atom_formalization(run_id: str, atom_id: str):
    run = formalization_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Formalization run {run_id} not found")
    atom = run.atom_formalizations.get(atom_id)
    if atom is None:
        raise HTTPException(status_code=404, detail=f"Formalization atom {atom_id} not found")
    return atom.model_dump()


@router.get("/runs/{run_id}/stream")
async def stream(request: Request, run_id: str):
    if not formalization_store.exists(run_id):
        raise HTTPException(status_code=404, detail=f"Formalization run {run_id} not found")

    last_event_id = request.headers.get("last-event-id")

    async def event_gen():
        queue: asyncio.Queue = asyncio.Queue()
        snapshot_cursor = last_event_id or formalization_event_bus.latest_event_id(run_id)
        run = formalization_store.get_run(run_id)
        snapshot_id = f"snapshot-{uuid.uuid4()}"
        yield {
            "event": "formalization_update",
            "id": snapshot_id,
            "data": FormalizationEvent(
                event_id=snapshot_id,
                run_id=run_id,
                event_type=FormalizationEventType.RUN_SNAPSHOT,
                payload={
                    "run": run.model_dump() if run else {},
                    "runtime": formalization_settings.runtime_metadata(),
                    "live": True,
                },
                timestamp=datetime.utcnow(),
            ).model_dump_json(),
        }

        async def drain():
            try:
                async for event in formalization_event_bus.subscribe(run_id, snapshot_cursor):
                    await queue.put(event)
                    if event.event_type in _TERMINAL_EVENT_TYPES:
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
                    if event is None:
                        break
                    yield {
                        "event": "formalization_update",
                        "id": event.event_id,
                        "data": event.model_dump_json(),
                    }
                    if event.event_type in _TERMINAL_EVENT_TYPES:
                        break
                except asyncio.TimeoutError:
                    yield {"comment": "heartbeat"}
        finally:
            drain_task.cancel()
            try:
                await drain_task
            except asyncio.CancelledError:
                pass

    return LoopSafeEventSourceResponse(event_gen())


@router.get("/runs/{run_id}/lean", response_class=PlainTextResponse)
async def get_lean(run_id: str):
    run = formalization_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Formalization run {run_id} not found")
    content = merged_lean(run)
    if not content.strip():
        raise HTTPException(status_code=404, detail="No Lean artifacts recorded")
    return PlainTextResponse(content, media_type="text/x-lean")


async def _create_run(
    job_id: str,
    *,
    atom_ids: Optional[list[str]],
    options: dict,
) -> FormalizationStartResponse:
    try:
        job = load_review_job(job_id)
        paper, atoms, _graph = rehydrate_job(job)
        selected_atom_ids = validate_atom_selection(atoms, atom_ids)
    except FormalizationContextError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    if not selected_atom_ids:
        raise HTTPException(status_code=400, detail="No reviewable atoms selected for formalization")

    run = formalization_store.create_run(
        job_id=job_id,
        paper_id=paper.paper_id,
        selected_atom_ids=selected_atom_ids,
        options=options,
    )
    formalization_event_bus.create_channel(run.run_id)
    asyncio.create_task(_orchestrator.run(run.run_id))
    return FormalizationStartResponse(
        run_id=run.run_id,
        status=run.status.value,
        selected_atom_ids=selected_atom_ids,
        runtime=formalization_settings.runtime_metadata(),
    )
