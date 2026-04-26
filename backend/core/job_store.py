import json
import logging
import os
import uuid
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class JobStore:
    def __init__(self, store_path: str = "/tmp/papercourt/jobs.json") -> None:
        self._store_path = store_path
        self._jobs: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._store_path):
            try:
                with open(self._store_path, "r", encoding="utf-8") as f:
                    self._jobs = json.load(f)
                logger.info(f"Loaded {len(self._jobs)} jobs from {self._store_path}")
            except Exception as e:
                logger.error(f"Failed to load jobs from {self._store_path}: {e}")

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump(self._jobs, f)
        except Exception as e:
            logger.error(f"Failed to save jobs to {self._store_path}: {e}")

    def create_job(self, mode: str, **kwargs) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "mode": mode,
            "status": "queued",
            **kwargs,
        }
        self._save()
        return job_id

    def get(self, job_id: str) -> Optional[dict]:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)
            self._save()

    def set_status(self, job_id: str, status: str) -> None:
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            self._save()

    def exists(self, job_id: str) -> bool:
        return job_id in self._jobs

    def get_all(self, mode: Optional[str] = None) -> list[dict]:
        jobs = self._jobs.values()
        if mode:
            jobs = [j for j in jobs if j.get("mode") == mode]
        return list(jobs)

    # ------------------------------------------------------------------
    # Reader session helpers

    def set_annotation(self, session_id: str, atom_id: str, annotation: dict) -> None:
        job = self._jobs.get(session_id)
        if job is not None:
            annotations = job.setdefault("annotations", {})
            annotations[atom_id] = annotation
            self._save()

    def get_annotation(self, session_id: str, atom_id: str) -> Optional[dict]:
        job = self._jobs.get(session_id)
        if job is None:
            return None
        return job.get("annotations", {}).get(atom_id)

    def set_comprehension_status(self, session_id: str, atom_id: str, status: str) -> None:
        job = self._jobs.get(session_id)
        if job is not None:
            states = job.setdefault("comprehension_states", {})
            states[atom_id] = status
            self._save()

    def get_comprehension_status(self, session_id: str, atom_id: str) -> Optional[str]:
        job = self._jobs.get(session_id)
        if job is None:
            return None
        return job.get("comprehension_states", {}).get(atom_id)

    def update_exercise_in_annotation(
        self, session_id: str, atom_id: str, exercise_id: str, **fields
    ) -> bool:
        annotation = self.get_annotation(session_id, atom_id)
        if annotation is None:
            return False
        for ex in annotation.get("exercises", []):
            if ex.get("exercise_id") == exercise_id:
                ex.update(fields)
                self._save()
                return True
        return False


job_store = JobStore()
