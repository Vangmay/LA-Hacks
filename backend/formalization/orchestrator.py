from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from formalization.agent import FormalizationAgent
from formalization.config import formalization_settings
from formalization.context_builder import build_context, load_review_job, rehydrate_job
from formalization.event_bus import formalization_event_bus
from formalization.events import FormalizationEvent, FormalizationEventType
from formalization.models import FormalizationLabel, FormalizationStatus
from formalization.store import formalization_store

logger = logging.getLogger(__name__)


class FormalizationOrchestrator:
    def __init__(self, agent: Optional[FormalizationAgent] = None) -> None:
        self.agent = agent or FormalizationAgent()

    async def run(self, run_id: str) -> None:
        run = formalization_store.get_run(run_id)
        if run is None:
            logger.error("formalization run %s not found", run_id)
            return

        formalization_store.set_run_status(run_id, FormalizationStatus.BUILDING_CONTEXT)
        await _publish(
            run_id,
            FormalizationEventType.RUN_STARTED,
            payload={
                "run_id": run_id,
                "job_id": run.job_id,
                "selected_atom_ids": run.selected_atom_ids,
                "runtime": formalization_settings.runtime_metadata(),
            },
        )

        try:
            job = load_review_job(run.job_id)
            paper, atoms, graph = rehydrate_job(job)
            atom_by_id = {atom.atom_id: atom for atom in atoms}
            total_atoms = len(run.selected_atom_ids)
            for index, atom_id in enumerate(run.selected_atom_ids, start=1):
                atom = atom_by_id[atom_id]
                formalization_store.ensure_atom(run_id, atom_id, atom.paper_id)
                await _publish(
                    run_id,
                    FormalizationEventType.ATOM_QUEUED,
                    atom_id=atom_id,
                    payload={
                        "atom_id": atom_id,
                        "atom_type": atom.atom_type.value,
                        "importance": atom.importance.value,
                        "text": atom.text[:500],
                        "section_id": atom.section_id,
                        "section_heading": atom.section_heading,
                        "queue_index": index,
                        "queue_total": total_atoms,
                        "max_iterations": formalization_settings.formalization_max_iterations_per_atom,
                        "max_axle_calls": formalization_settings.formalization_max_axle_calls_per_atom,
                    },
                )

            semaphore = asyncio.Semaphore(max(1, formalization_settings.formalization_parallelism))

            async def run_one(atom_id: str) -> None:
                async with semaphore:
                    await self._run_one(run_id, job, paper, atoms, graph, atom_id)

            await asyncio.gather(*(run_one(atom_id) for atom_id in run.selected_atom_ids))
            formalization_store.set_run_status(
                run_id,
                FormalizationStatus.COMPLETE,
                completed=True,
            )
            run = formalization_store.get_run(run_id)
            await _publish(
                run_id,
                FormalizationEventType.RUN_COMPLETE,
                payload={"summary": run.summary if run else {}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("formalization run %s failed", run_id)
            formalization_store.set_run_status(
                run_id,
                FormalizationStatus.ERROR,
                error=str(exc),
                completed=True,
            )
            await _publish(run_id, FormalizationEventType.RUN_ERROR, payload={"error": str(exc)})

    async def _run_one(
        self,
        run_id: str,
        job: dict[str, Any],
        paper: Any,
        atoms: list[Any],
        graph: Any,
        atom_id: str,
    ) -> None:
        try:
            formalization_store.set_atom_status(run_id, atom_id, FormalizationStatus.BUILDING_CONTEXT)
            context = build_context(job=job, paper=paper, atoms=atoms, graph=graph, atom_id=atom_id)
            await _publish(
                run_id,
                FormalizationEventType.ATOM_CONTEXT_BUILT,
                atom_id=atom_id,
                payload={
                    "atom_id": atom_id,
                    "equations": len(context.get("equations") or []),
                    "citations": len(context.get("citations") or []),
                    "dependencies": len(context.get("dependencies") or []),
                    "nearby_prose_chars": len(context.get("nearby_prose") or ""),
                    "tex_excerpt_chars": len(context.get("tex_excerpt") or ""),
                    "section_heading": context.get("section_heading"),
                    "atom_text": context.get("atom_text"),
                    "formalization_hints": context.get("formalization_hints") or [],
                },
            )
            await self.agent.run_atom(run_id=run_id, atom_id=atom_id, context=context)
        except Exception as exc:  # noqa: BLE001
            logger.exception("formalization atom %s failed", atom_id)
            formalization_store.finalize_atom(
                run_id,
                atom_id,
                label=FormalizationLabel.FORMALIZATION_FAILED,
                rationale=f"Formalization failed with an internal error: {exc}",
                confidence=0.0,
                error=str(exc),
            )
            await _publish(
                run_id,
                FormalizationEventType.ATOM_ERROR,
                atom_id=atom_id,
                payload={"error": str(exc)},
            )


async def _publish(
    run_id: str,
    event_type: FormalizationEventType,
    *,
    atom_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    try:
        await formalization_event_bus.publish(
            run_id,
            FormalizationEvent(
                event_id=str(uuid.uuid4()),
                run_id=run_id,
                event_type=event_type,
                atom_id=atom_id,
                payload=payload or {},
                timestamp=datetime.utcnow(),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("formalization orchestrator failed to emit event: %s", exc)
