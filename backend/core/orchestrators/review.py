import asyncio
import logging

from core.job_store import job_store

logger = logging.getLogger(__name__)


class ReviewOrchestrator:
    """Stub — Person B implements full pipeline in Phase 2."""

    async def run(self, job_id: str, **kwargs) -> None:
        try:
            job_store.set_status(job_id, "processing")
            await asyncio.sleep(0.1)
            job_store.set_status(job_id, "complete")
        except Exception as e:
            logger.exception("Review orchestrator failed")
            job_store.update(job_id, status="error", error=str(e))
