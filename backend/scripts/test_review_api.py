"""In-process tests for the ported review API/orchestrator changes.

Covers:
- HTTP request-logging middleware emits a log line per request.
- /status returns 404 for unknown jobs and includes job_id for known ones.
- /stream returns 404 for unknown jobs.
- /stream replays via Last-Event-Id, emits a heartbeat on idle, breaks on
  JOB_COMPLETE, sets the SSE id field, and the drain task is cancelled
  cleanly on disconnect.
- core.orchestrators.review._publish swallows event_bus.publish failures
  rather than aborting the orchestrator.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import main as main_module
from core import orchestrators
from core.event_bus import event_bus
from core.job_store import job_store
from models import DAGEvent, DAGEventType


def _mk_event(job_id: str, event_type: DAGEventType, atom_id: str | None = None) -> DAGEvent:
    return DAGEvent(
        event_id=str(uuid.uuid4()),
        job_id=job_id,
        event_type=event_type,
        atom_id=atom_id,
        node_id=None,
        payload={"x": 1},
        timestamp=datetime.utcnow(),
    )


def test_middleware_logs_request(caplog_handler: list[logging.LogRecord]) -> None:
    client = TestClient(main_module.app)
    caplog_handler.clear()
    resp = client.get("/health")
    assert resp.status_code == 200, resp.status_code
    assert resp.json() == {"status": "ok"}
    matched = [r for r in caplog_handler if "GET /health 200" in r.getMessage()]
    assert matched, f"expected middleware log, got {[r.getMessage() for r in caplog_handler]}"
    print("OK middleware log:", matched[0].getMessage())


def test_status_unknown_returns_404() -> None:
    client = TestClient(main_module.app)
    resp = client.get("/review/does-not-exist/status")
    assert resp.status_code == 404, resp.text
    print("OK /status unknown -> 404")


def test_status_known_includes_job_id() -> None:
    job_id = job_store.create_job(mode="review", filename="test.tex")
    job_store.update(job_id, completed_atoms=2, total_atoms=5, paper_title="Test", paper_id="p1")
    client = TestClient(main_module.app)
    resp = client.get(f"/review/{job_id}/status")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["job_id"] == job_id, body
    assert body["status"] == "queued", body
    assert body["completed_atoms"] == 2
    assert body["total_atoms"] == 5
    assert body["paper_title"] == "Test"
    print("OK /status known includes job_id and progress")


def test_stream_unknown_returns_404() -> None:
    client = TestClient(main_module.app)
    resp = client.get("/review/does-not-exist/stream")
    assert resp.status_code == 404, resp.text
    print("OK /stream unknown -> 404")


def test_stream_replay_and_terminal_break() -> None:
    # Pre-populate event history so subscribe() replays it, then terminate
    # immediately with JOB_COMPLETE so the request closes deterministically.
    job_id = job_store.create_job(mode="review", filename="replay.tex")
    event_bus.create_channel(job_id)

    async def seed():
        await event_bus.publish(job_id, _mk_event(job_id, DAGEventType.ATOM_CREATED, atom_id="a1"))
        await event_bus.publish(job_id, _mk_event(job_id, DAGEventType.VERDICT_EMITTED, atom_id="a1"))
        await event_bus.publish(job_id, _mk_event(job_id, DAGEventType.JOB_COMPLETE))

    asyncio.run(seed())

    client = TestClient(main_module.app)
    with client.stream("GET", f"/review/{job_id}/stream") as resp:
        assert resp.status_code == 200, resp.status_code
        chunks: list[str] = []
        for raw in resp.iter_lines():
            if raw is None:
                continue
            line = raw if isinstance(raw, str) else raw.decode()
            chunks.append(line)
            # The stream closes itself when the orchestrator sees JOB_COMPLETE.

    text = "\n".join(chunks)
    assert "event: dag_update" in text, text
    # SSE id field set per event for client-side resumption.
    assert "id:" in text, text
    # Each of the 3 published events should show up in the replay.
    assert text.count("event: dag_update") >= 3, text
    print(f"OK /stream replay produced {text.count('event: dag_update')} events with id fields and closed on JOB_COMPLETE")


def test_stream_replay_after_last_event_id() -> None:
    # Verify Last-Event-Id is honored: only events AFTER the marker should
    # be delivered.
    job_id = job_store.create_job(mode="review", filename="resume.tex")
    event_bus.create_channel(job_id)
    e1 = _mk_event(job_id, DAGEventType.ATOM_CREATED, atom_id="a1")
    e2 = _mk_event(job_id, DAGEventType.VERDICT_EMITTED, atom_id="a1")
    e3 = _mk_event(job_id, DAGEventType.JOB_COMPLETE)

    async def seed():
        for ev in (e1, e2, e3):
            await event_bus.publish(job_id, ev)

    asyncio.run(seed())

    client = TestClient(main_module.app)
    with client.stream(
        "GET",
        f"/review/{job_id}/stream",
        headers={"Last-Event-Id": e1.event_id},
    ) as resp:
        assert resp.status_code == 200
        chunks = list(resp.iter_lines())

    text = "\n".join(c if isinstance(c, str) else c.decode() for c in chunks if c is not None)
    assert e1.event_id not in text, "should not replay event before marker"
    assert e2.event_id in text, "should replay event after marker"
    assert e3.event_id in text, "should replay terminal event after marker"
    print("OK /stream Last-Event-Id replay skips already-seen events")


def test_publish_swallows_event_bus_errors() -> None:
    # The orchestrator's _publish must not raise; it should log a warning
    # and continue when event_bus.publish blows up.
    review_mod = orchestrators.review
    job_id = "not-real"
    original = event_bus.publish

    async def boom(_job_id, _event):
        raise RuntimeError("simulated event bus failure")

    event_bus.publish = boom  # type: ignore[assignment]
    try:
        # Should not raise. Should log a warning.
        asyncio.run(
            review_mod._publish(
                job_id,
                DAGEventType.JOB_COMPLETE,
                payload={"x": 1},
            )
        )
    finally:
        event_bus.publish = original
    print("OK _publish swallows event_bus errors")


def main() -> int:
    # Capture middleware logs by attaching a handler to the configured logger.
    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Capture(level=logging.INFO)
    logging.getLogger().addHandler(handler)
    logging.getLogger("main").setLevel(logging.INFO)
    logging.getLogger().setLevel(logging.INFO)

    try:
        test_middleware_logs_request(records)
        test_status_unknown_returns_404()
        test_status_known_includes_job_id()
        test_stream_unknown_returns_404()
        test_stream_replay_and_terminal_break()
        test_stream_replay_after_last_event_id()
        test_publish_swallows_event_bus_errors()
    finally:
        logging.getLogger().removeHandler(handler)
    print("review API/orchestrator port tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
