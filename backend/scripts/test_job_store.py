from __future__ import annotations

from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from pathlib import Path

from core.job_store import JobStore
from models.jobs import JobStatus


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_datetime_and_enum_persistence() -> None:
    with TemporaryDirectory() as tmp:
        store_path = str(Path(tmp) / "jobs.json")
        store = JobStore(store_path)
        created_at = datetime(2026, 4, 26, 12, 30, tzinfo=timezone.utc)
        job_id = store.create_job(
            mode="review",
            created_at=created_at,
            status=JobStatus.PROCESSING,
        )

        reloaded = JobStore(store_path)
        job = reloaded.get(job_id) or {}
        _assert(job["created_at"] == created_at.isoformat(), "datetime should be serialized")
        _assert(job["status"] == JobStatus.PROCESSING.value, "enum should be serialized")


def test_corrupt_store_is_quarantined() -> None:
    with TemporaryDirectory() as tmp:
        store_path = Path(tmp) / "jobs.json"
        store_path.write_text('{"broken": ', encoding="utf-8")

        store = JobStore(str(store_path))
        _assert(store.get_all() == [], "corrupt store should load as empty")
        _assert(not store_path.exists(), "corrupt store should be moved aside")
        _assert(Path(f"{store_path}.corrupt").exists(), "corrupt backup should exist")


if __name__ == "__main__":
    test_datetime_and_enum_persistence()
    test_corrupt_store_is_quarantined()
    print("job store persistence tests OK")
