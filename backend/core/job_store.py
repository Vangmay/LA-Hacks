from typing import Optional, Dict
import uuid


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, dict] = {}

    def create_job(self, mode: str, **kwargs) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "mode": mode,
            "status": "queued",
            **kwargs,
        }
        return job_id

    def get(self, job_id: str) -> Optional[dict]:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def set_status(self, job_id: str, status: str) -> None:
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status

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
                return True
        return False


job_store = JobStore()
