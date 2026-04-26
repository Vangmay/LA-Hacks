from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from formalization.models import (
    AtomFormalization,
    FormalizationArtifact,
    FormalizationLabel,
    FormalizationRun,
    FormalizationStatus,
    ToolCallRecord,
)


class FormalizationStore:
    def __init__(self) -> None:
        self._runs: dict[str, FormalizationRun] = {}

    def create_run(
        self,
        *,
        job_id: str,
        paper_id: str,
        selected_atom_ids: list[str],
        options: Optional[dict] = None,
    ) -> FormalizationRun:
        run_id = str(uuid.uuid4())
        run = FormalizationRun(
            run_id=run_id,
            job_id=job_id,
            paper_id=paper_id,
            selected_atom_ids=selected_atom_ids,
            options=options or {},
        )
        self._runs[run_id] = run
        return run

    def exists(self, run_id: str) -> bool:
        return run_id in self._runs

    def get_run(self, run_id: str) -> Optional[FormalizationRun]:
        return self._runs.get(run_id)

    def set_run_status(
        self,
        run_id: str,
        status: FormalizationStatus,
        *,
        error: Optional[str] = None,
        completed: bool = False,
    ) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        run.status = status
        if error is not None:
            run.error = error
        if completed:
            run.completed_at = datetime.utcnow()
        self._recompute_summary(run)

    def ensure_atom(self, run_id: str, atom_id: str, paper_id: str) -> AtomFormalization:
        run = self._require_run(run_id)
        atom = run.atom_formalizations.get(atom_id)
        if atom is None:
            atom = AtomFormalization(atom_id=atom_id, paper_id=paper_id)
            run.atom_formalizations[atom_id] = atom
        return atom

    def update_atom_metadata(
        self,
        run_id: str,
        atom_id: str,
        *,
        text: Optional[str] = None,
        atom_type: Optional[str] = None,
        importance: Optional[str] = None,
        section_id: Optional[str] = None,
        section_heading: Optional[str] = None,
        queue_index: Optional[int] = None,
        queue_total: Optional[int] = None,
        max_iterations: Optional[int] = None,
        max_axle_calls: Optional[int] = None,
    ) -> None:
        atom = self._require_atom(run_id, atom_id)
        updates = {
            "text": text,
            "atom_type": atom_type,
            "importance": importance,
            "section_id": section_id,
            "section_heading": section_heading,
            "queue_index": queue_index,
            "queue_total": queue_total,
            "max_iterations": max_iterations,
            "max_axle_calls": max_axle_calls,
        }
        for key, value in updates.items():
            if value is not None:
                setattr(atom, key, value)

    def set_atom_context_summary(self, run_id: str, atom_id: str, summary: dict[str, Any]) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.context_summary = dict(summary)

    def set_atom_status(
        self,
        run_id: str,
        atom_id: str,
        status: FormalizationStatus,
        *,
        error: Optional[str] = None,
        completed: bool = False,
    ) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.status = status
        if error is not None:
            atom.error = error
        if completed:
            atom.completed_at = datetime.utcnow()
        self._recompute_summary(self._require_run(run_id))

    def append_llm_message(self, run_id: str, atom_id: str, message: dict) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.llm_messages.append(message)

    def increment_llm_call_count(self, run_id: str, atom_id: str) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.llm_call_count += 1

    def append_tool_call(self, run_id: str, atom_id: str, record: ToolCallRecord) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.tool_calls.append(record)

    def update_tool_call(self, run_id: str, atom_id: str, record: ToolCallRecord) -> None:
        atom = self._require_atom(run_id, atom_id)
        for index, existing in enumerate(atom.tool_calls):
            if existing.call_id == record.call_id:
                atom.tool_calls[index] = record
                return
        atom.tool_calls.append(record)

    def add_artifact(self, run_id: str, atom_id: str, artifact: FormalizationArtifact) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.artifacts.append(artifact)

    def update_artifact_status(
        self,
        run_id: str,
        atom_id: str,
        artifact_id: str,
        *,
        axle_check_okay: Optional[bool] = None,
        axle_verify_okay: Optional[bool] = None,
    ) -> None:
        atom = self._require_atom(run_id, atom_id)
        for artifact in atom.artifacts:
            if artifact.artifact_id != artifact_id:
                continue
            if axle_check_okay is not None:
                artifact.axle_check_okay = axle_check_okay
            if axle_verify_okay is not None:
                artifact.axle_verify_okay = axle_verify_okay
            return

    def finalize_atom(
        self,
        run_id: str,
        atom_id: str,
        *,
        label: FormalizationLabel,
        rationale: str,
        used_assumptions: Optional[list[str]] = None,
        confidence: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        atom = self._require_atom(run_id, atom_id)
        atom.status = FormalizationStatus.COMPLETE if error is None else FormalizationStatus.ERROR
        atom.label = label
        atom.rationale = rationale
        atom.used_assumptions = used_assumptions or []
        atom.confidence = max(0.0, min(1.0, confidence))
        atom.error = error
        atom.completed_at = datetime.utcnow()
        self._recompute_summary(self._require_run(run_id))

    def _require_run(self, run_id: str) -> FormalizationRun:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(f"formalization run {run_id} not found")
        return run

    def _require_atom(self, run_id: str, atom_id: str) -> AtomFormalization:
        run = self._require_run(run_id)
        atom = run.atom_formalizations.get(atom_id)
        if atom is None:
            raise KeyError(f"atom {atom_id} not found in formalization run {run_id}")
        return atom

    def _recompute_summary(self, run: FormalizationRun) -> None:
        summary = {label.value: 0 for label in FormalizationLabel}
        for atom in run.atom_formalizations.values():
            if atom.label is not None:
                summary[atom.label.value] = summary.get(atom.label.value, 0) + 1
        run.summary = summary


formalization_store = FormalizationStore()
