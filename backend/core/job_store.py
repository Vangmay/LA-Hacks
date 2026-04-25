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


job_store = JobStore()
