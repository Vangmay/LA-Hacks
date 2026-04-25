"""Reader Mode API routes.

POST /read                               — submit arXiv paper, create session
GET  /read/{session_id}/status           — session status
GET  /read/{session_id}/graph            — graph with comprehension overlay
GET  /read/{session_id}/atom/{atom_id}   — lazy annotation (runs 4 agents on miss)
POST /read/{session_id}/atom/{atom_id}/tutor  — Socratic tutor turn
POST /read/{session_id}/atom/{atom_id}/grade  — grade an exercise answer
PATCH /read/{session_id}/atom/{atom_id}/status — update comprehension state
GET  /read/{session_id}/study-guide      — compile markdown study guide
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from agents.base import AgentContext
from agents.exercise_generator import ExerciseGeneratorAgent
from agents.explainer import ExplainerAgent
from agents.glossary_agent import GlossaryAgent
from agents.prerequisite_mapper import PrerequisiteMapperAgent
from agents.socratic_tutor import SocraticTutorAgent
from config import settings
from core.job_store import job_store
from core.openai_client import make_async_openai
from core.orchestrators.reader import ReaderOrchestrator, _graph_snapshot
from ingestion.arxiv import ArxivSourceError, fetch_arxiv_source, parse_arxiv_url
from models import ResearchAtom, ResearchGraph

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = ReaderOrchestrator()

_JOB_ROOT = "/tmp/papercourt"

_VALID_STATUSES = {"understood", "in_progress", "flagged", "unvisited"}

_GRADE_SYSTEM = (
    "You are grading a student's answer to an exercise about a mathematical "
    "research atom. Compare their answer to the provided answer key. "
    "Be generous with partially correct answers. "
    "Return JSON only: {\"correct\": bool, \"feedback\": str}"
)


# ---------------------------------------------------------------------------
# Submission

@router.post("")
async def submit_reader(
    arxiv_url: str = Form(...),
    level: str = Form(default="undergraduate"),
):
    ref = parse_arxiv_url(arxiv_url)
    if not ref:
        raise HTTPException(status_code=400, detail=f"unrecognized arxiv url: {arxiv_url!r}")

    if level not in {"layperson", "undergraduate", "graduate", "expert"}:
        level = "undergraduate"

    session_id = job_store.create_job(mode="reader", comprehension_level=level)
    job_dir = os.path.join(_JOB_ROOT, session_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        source = await fetch_arxiv_source(ref, job_dir)
    except ArxivSourceError as exc:
        job_store.update(session_id, status="error", error=str(exc))
        raise HTTPException(status_code=502, detail=f"arxiv source ingestion failed: {exc}") from exc
    except Exception as exc:
        job_store.update(session_id, status="error", error=str(exc))
        raise HTTPException(status_code=502, detail=f"arxiv source fetch failed: {exc}") from exc

    assembled_path = os.path.join(job_dir, f"{ref.canonical}.assembled.tex")
    with open(assembled_path, "w", encoding="utf-8") as fh:
        fh.write(source.tex_text)

    job_store.update(
        session_id,
        arxiv_id=ref.canonical,
        arxiv_source_url=source.source_url,
        tex_path=assembled_path,
        source_archive_path=source.archive_path,
        source_extract_dir=source.extract_dir,
        main_tex_path=source.main_tex_path,
    )

    asyncio.create_task(_orchestrator.run(session_id))
    return {"session_id": session_id, "status": "processing"}


# ---------------------------------------------------------------------------
# Status

@router.get("/{session_id}/status")
async def get_status(session_id: str):
    _require_session(session_id)
    job = job_store.get(session_id)
    return {
        "session_id": session_id,
        "status": job.get("status"),
        "total_atoms": job.get("total_atoms", 0),
        "start_here": job.get("start_here", []),
        "comprehension_level": job.get("comprehension_level"),
        "paper_metadata": job.get("paper_metadata"),
        "error": job.get("error"),
    }


# ---------------------------------------------------------------------------
# Graph

@router.get("/{session_id}/graph")
async def get_graph(session_id: str):
    _require_session(session_id)
    job = job_store.get(session_id) or {}

    snapshot = job.get("graph_snapshot")
    if snapshot:
        # Freshen comprehension_status from live states (may have changed since last write).
        states = job.get("comprehension_states", {})
        start_here = set(job.get("start_here", []))
        for node in snapshot.get("nodes", []):
            node_id = node.get("id")
            if node_id:
                node["comprehension_status"] = states.get(node_id, "unvisited")
                node["start_here"] = node_id in start_here
        return snapshot

    return {"nodes": [], "edges": [], "start_here": []}


# ---------------------------------------------------------------------------
# Atom annotation (lazy)

@router.get("/{session_id}/atom/{atom_id}")
async def get_atom_annotation(
    session_id: str,
    atom_id: str,
    level: str = Query(default=None),
):
    _require_session(session_id)
    job = job_store.get(session_id) or {}

    effective_level = level or job.get("comprehension_level", "undergraduate")

    cached = job_store.get_annotation(session_id, atom_id)
    if cached is not None and cached.get("level") == effective_level:
        return cached

    # Resolve the atom from stored list.
    atom = _find_atom(job, atom_id)
    if atom is None:
        raise HTTPException(status_code=404, detail=f"Atom {atom_id!r} not found")

    if job.get("status") not in {"complete"}:
        raise HTTPException(status_code=202, detail="Session still processing")

    level = effective_level
    ctx = AgentContext(job_id=session_id, atom=atom, extra={"comprehension_level": level})

    explainer, prereqs, glossary, exercises = await asyncio.gather(
        ExplainerAgent().run(ctx),
        PrerequisiteMapperAgent().run(ctx),
        GlossaryAgent().run(ctx),
        ExerciseGeneratorAgent().run(ctx),
    )

    annotation = {
        "atom_id": atom_id,
        "level": level,
        "explanation": explainer.output.get("explanation", ""),
        "key_insight": explainer.output.get("key_insight", ""),
        "worked_example": explainer.output.get("worked_example"),
        "glossary": glossary.output.get("glossary", {}),
        "prerequisites": prereqs.output.get("prerequisites", []),
        "exercises": exercises.output.get("exercises", []),
        "comprehension_status": job.get("comprehension_states", {}).get(atom_id, "unvisited"),
    }

    job_store.set_annotation(session_id, atom_id, annotation)
    return annotation


# ---------------------------------------------------------------------------
# Socratic tutor

class TutorRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/{session_id}/atom/{atom_id}/tutor")
async def tutor(session_id: str, atom_id: str, body: TutorRequest):
    _require_session(session_id)
    job = job_store.get(session_id) or {}

    atom = _find_atom(job, atom_id)
    if atom is None:
        raise HTTPException(status_code=404, detail=f"Atom {atom_id!r} not found")

    ctx = AgentContext(
        job_id=session_id,
        atom=atom,
        extra={"user_message": body.message, "history": body.history},
    )
    result = await SocraticTutorAgent().run(ctx)
    if result.status == "error":
        raise HTTPException(status_code=500, detail=result.error or "tutor agent failed")
    return {"response": result.output.get("response", "")}


# ---------------------------------------------------------------------------
# Exercise grading

class GradeRequest(BaseModel):
    exercise_id: str
    answer: str


@router.post("/{session_id}/atom/{atom_id}/grade")
async def grade_exercise(session_id: str, atom_id: str, body: GradeRequest):
    _require_session(session_id)

    annotation = job_store.get_annotation(session_id, atom_id)
    if annotation is None:
        raise HTTPException(status_code=404, detail="Annotation not yet generated for this atom")

    exercise = next(
        (ex for ex in annotation.get("exercises", []) if ex.get("exercise_id") == body.exercise_id),
        None,
    )
    if exercise is None:
        raise HTTPException(status_code=404, detail=f"Exercise {body.exercise_id!r} not found")

    user_content = (
        f"Exercise: {exercise['prompt']}\n"
        f"Answer key: {exercise['answer_key']}\n"
        f"Student answer: {body.answer}"
    )

    client = make_async_openai()
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _GRADE_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception as exc:
        logger.exception("grading call failed for %s/%s", session_id, body.exercise_id)
        raise HTTPException(status_code=500, detail=f"grading failed: {exc}") from exc

    correct = bool(data.get("correct", False))
    feedback = str(data.get("feedback", ""))

    job_store.update_exercise_in_annotation(
        session_id, atom_id, body.exercise_id,
        user_answer=body.answer,
        graded=correct,
    )

    return {"correct": correct, "feedback": feedback}


# ---------------------------------------------------------------------------
# Comprehension status

class StatusUpdate(BaseModel):
    status: str


@router.patch("/{session_id}/atom/{atom_id}/status")
async def update_status(session_id: str, atom_id: str, body: StatusUpdate):
    _require_session(session_id)

    if body.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {sorted(_VALID_STATUSES)}",
        )

    job_store.set_comprehension_status(session_id, atom_id, body.status)

    # Keep annotation in sync if it exists.
    annotation = job_store.get_annotation(session_id, atom_id)
    if annotation is not None:
        annotation["comprehension_status"] = body.status

    # Rebuild graph snapshot so the UI gets fresh colours on next poll.
    job = job_store.get(session_id) or {}
    atoms_raw = job.get("atoms", [])
    graph_raw = job.get("graph")
    if atoms_raw and graph_raw:
        atoms = [ResearchAtom.model_validate(a) for a in atoms_raw]
        graph = ResearchGraph.model_validate(graph_raw)
        states = job.get("comprehension_states", {})
        job_store.update(session_id, graph_snapshot=_graph_snapshot(atoms, graph, states))

    return {"atom_id": atom_id, "status": body.status}


# ---------------------------------------------------------------------------
# Study guide

@router.get("/{session_id}/study-guide", response_class=PlainTextResponse)
async def study_guide(session_id: str):
    _require_session(session_id)
    job = job_store.get(session_id) or {}

    if job.get("status") != "complete":
        raise HTTPException(status_code=202, detail="Session still processing")

    return _build_study_guide(job)


# ---------------------------------------------------------------------------
# Helpers


def _require_session(session_id: str) -> None:
    if not job_store.exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found")


def _find_atom(job: dict, atom_id: str) -> ResearchAtom | None:
    raw = next(
        (a for a in job.get("atoms", []) if a.get("atom_id") == atom_id),
        None,
    )
    if raw is None:
        return None
    return ResearchAtom.model_validate(raw)


def _build_study_guide(job: dict) -> str:
    meta = job.get("paper_metadata", {})
    title = meta.get("title") or "Untitled Paper"
    arxiv_id = meta.get("arxiv_id") or ""

    annotations: dict[str, dict] = job.get("annotations", {})
    states: dict[str, str] = job.get("comprehension_states", {})
    graph_raw = job.get("graph", {})
    topo_order: list[str] = graph_raw.get("topological_order", [])
    start_here: set[str] = set(job.get("start_here", []))

    total = len(states)
    understood = sum(1 for s in states.values() if s == "understood")
    in_progress = sum(1 for s in states.values() if s == "in_progress")
    flagged = sum(1 for s in states.values() if s == "flagged")

    lines: list[str] = [
        f"# {title}",
        "",
        *(([f"**arXiv:** {arxiv_id}", ""]) if arxiv_id else []),
        "## Comprehension Progress",
        "",
        f"- Understood: {understood}/{total}",
        f"- In progress: {in_progress}",
        f"- Flagged for review: {flagged}",
        "",
    ]

    # Visited atom IDs in topological order, then any stragglers.
    visited_ids = [aid for aid in topo_order if aid in annotations]
    for aid in annotations:
        if aid not in visited_ids:
            visited_ids.append(aid)

    if not visited_ids:
        lines += ["*No atoms visited yet.*", ""]
        return "\n".join(lines)

    lines += ["## Atom Summaries", ""]

    all_glossary: dict[str, str] = {}
    prereq_index: dict[str, dict] = {}  # concept → {description, resource_links, count}

    _status_icon = {
        "understood": "✓",
        "in_progress": "⟳",
        "flagged": "⚑",
        "unvisited": "○",
    }

    for atom_id in visited_ids:
        ann = annotations[atom_id]
        status = states.get(atom_id, "unvisited")
        icon = _status_icon.get(status, "○")
        star = " ★" if atom_id in start_here else ""

        lines += [f"### {icon} {atom_id}{star}", ""]

        explanation = ann.get("explanation", "")
        key_insight = ann.get("key_insight", "")
        worked_example = ann.get("worked_example")

        if explanation:
            lines += ["**Explanation:**", "", explanation, ""]
        if key_insight:
            lines += [f"> **Key insight:** {key_insight}", ""]
        if worked_example:
            lines += ["**Worked example:**", "", f"```\n{worked_example}\n```", ""]

        exercises = ann.get("exercises", [])
        if exercises:
            lines += ["**Exercises:**", ""]
            for ex in exercises:
                lines.append(f"- {ex.get('prompt', '')}")
                lines.append(f"  *Answer:* {ex.get('answer_key', '')}")
            lines.append("")

        # Accumulate glossary and prerequisites.
        for term, defn in ann.get("glossary", {}).items():
            if term and defn:
                all_glossary[term] = defn

        for prereq in ann.get("prerequisites", []):
            concept = prereq.get("concept", "")
            if not concept:
                continue
            if concept not in prereq_index:
                prereq_index[concept] = {
                    "description": prereq.get("description", ""),
                    "resource_links": prereq.get("resource_links", []),
                    "count": 0,
                }
            prereq_index[concept]["count"] += 1

    if all_glossary:
        lines += ["## Glossary", ""]
        for term in sorted(all_glossary):
            lines.append(f"**{term}**: {all_glossary[term]}")
        lines.append("")

    if prereq_index:
        lines += ["## Prerequisite Reading", ""]
        for concept, data in sorted(prereq_index.items(), key=lambda x: -x[1]["count"]):
            count = data["count"]
            desc = data["description"]
            links = data["resource_links"]
            suffix = f" — needed by {count} atom(s)" if count > 1 else ""
            if links:
                lines.append(f"- [{concept}]({links[0]}){suffix}")
            else:
                lines.append(f"- **{concept}**{suffix}")
            if desc:
                lines.append(f"  {desc}")
        lines.append("")

    return "\n".join(lines)
