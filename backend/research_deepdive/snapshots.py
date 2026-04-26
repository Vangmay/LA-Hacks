"""Filesystem snapshots for research deep-dive workspaces."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DeepDiveConfig
from .workspace import slugify

SUBAGENT_ARTIFACTS = (
    "memory.md",
    "queries.md",
    "papers.md",
    "findings.md",
    "proposal_seeds.md",
    "handoff.md",
)
SHARED_ARTIFACTS = (
    "director_plan.md",
    "planning_trace.md",
    "cross_investigator_deep_dive.md",
    "proposal_families.md",
    "global_evidence_map.md",
    "unresolved_conflicts.md",
)

_README_RUN_RE = re.compile(r"-\s*Run id:\s*`([^`]+)`")
_README_CREATED_RE = re.compile(r"-\s*Created UTC:\s*`([^`]+)`")
_PROMPT_FIELD_RE = re.compile(r"-\s*([^:\n]+):\s*`([^`]+)`")


def research_workspace_root(config: DeepDiveConfig | None = None) -> Path:
    root = (config or DeepDiveConfig()).normalized().workspace_root
    if root.is_absolute() or root.exists():
        return root
    repo_relative = Path(__file__).resolve().parents[2] / root
    if repo_relative.exists() or (root.parts and root.parts[0] == "backend"):
        return repo_relative
    return root


def resolve_run_root(run_id: str, config: DeepDiveConfig | None = None) -> Path:
    root = research_workspace_root(config).resolve()
    candidate = (root / slugify(run_id)).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"run path escapes workspace root: {run_id}")
    return candidate


def resolve_artifact_path(run_id: str, artifact_path: str, config: DeepDiveConfig | None = None) -> Path:
    run_root = resolve_run_root(run_id, config)
    candidate = (run_root / artifact_path).resolve()
    if candidate != run_root and run_root not in candidate.parents:
        raise ValueError(f"artifact path escapes run root: {artifact_path}")
    return candidate


def list_run_summaries(config: DeepDiveConfig | None = None) -> list[dict[str, Any]]:
    root = research_workspace_root(config)
    if not root.exists():
        return []
    summaries = [
        summarize_run(path)
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]
    return sorted(
        summaries,
        key=lambda item: item.get("created_utc") or item.get("mtime") or "",
        reverse=True,
    )


def summarize_run(run_root: Path) -> dict[str, Any]:
    readme = _read_text(run_root / "README.md")
    run_id = _regex_value(_README_RUN_RE, readme) or run_root.name
    created = _regex_value(_README_CREATED_RE, readme)
    plans = _load_plans(run_root)
    subagent_count = sum(len(plan.get("subagents") or []) for plan in plans)
    handoff_count = len(list(run_root.glob("investigators/*/subagents/*/handoff.md")))
    synthesis_count = len(list(run_root.glob("investigators/*/synthesis.md")))
    critique_count = len(list(run_root.glob("critique/*/critique.md")))
    tool_event_count = _count_jsonl_files(run_root.glob("investigators/*/subagents/*/tool_calls.jsonl"))
    final_report = run_root / "final" / "research_deep_dive_report.md"
    prompt_fields = _prompt_fields_from_plans(plans)
    status = _infer_status(
        final_report=final_report,
        critique_count=critique_count,
        synthesis_count=synthesis_count,
        handoff_count=handoff_count,
        plans=plans,
    )
    return {
        "run_id": run_id,
        "created_utc": created,
        "mtime": datetime.fromtimestamp(run_root.stat().st_mtime, timezone.utc).isoformat(),
        "status": status,
        "workspace_path": str(run_root),
        "arxiv_url": prompt_fields.get("arxiv url", ""),
        "paper_id": prompt_fields.get("paper id", ""),
        "research_objective": prompt_fields.get("research objective", ""),
        "investigator_count": len(plans) or len(list((run_root / "investigators").glob("*"))),
        "subagent_count": subagent_count,
        "handoff_count": handoff_count,
        "synthesis_count": synthesis_count,
        "critique_count": critique_count,
        "tool_event_count": tool_event_count,
        "final_report_available": final_report.exists(),
    }


def build_run_snapshot(run_id: str, config: DeepDiveConfig | None = None) -> dict[str, Any]:
    run_root = resolve_run_root(run_id, config)
    if not run_root.exists():
        raise FileNotFoundError(run_id)

    plans = _load_plans(run_root)
    summary = summarize_run(run_root)
    investigators = []
    subagents = []

    planned_investigator_ids = set()
    for plan in plans:
        investigator_id = str(plan.get("investigator_id") or Path(plan.get("workspace_path", "")).name)
        planned_investigator_ids.add(investigator_id)
        investigator_path = run_root / "investigators" / slugify(investigator_id)
        synthesis_md = _read_text(investigator_path / "synthesis.md")
        subagent_ids: list[str] = []
        for sub_plan in plan.get("subagents") or []:
            subagent = _snapshot_subagent(run_root, plan, sub_plan)
            subagent_ids.append(subagent["id"])
            subagents.append(subagent)
        investigators.append(
            {
                "id": investigator_id,
                "section_id": plan.get("section_id", ""),
                "section_title": plan.get("section_title", investigator_id),
                "workspace_path": _rel(run_root, investigator_path),
                "status": "completed" if synthesis_md else ("running" if subagent_ids else "planned"),
                "subagent_ids": subagent_ids,
                "synthesis_md": synthesis_md,
                "artifact_meta": _artifact_meta(investigator_path / "synthesis.md"),
            }
        )

    for investigator_path in sorted((run_root / "investigators").glob("*")):
        if not investigator_path.is_dir() or investigator_path.name in planned_investigator_ids:
            continue
        synthesis_md = _read_text(investigator_path / "synthesis.md")
        fallback_subagents = []
        for subagent_path in sorted((investigator_path / "subagents").glob("*")):
            if subagent_path.is_dir():
                fallback_subagents.append(_snapshot_subagent_from_path(run_root, investigator_path, subagent_path))
        subagents.extend(fallback_subagents)
        investigators.append(
            {
                "id": investigator_path.name,
                "section_id": "",
                "section_title": _read_section_from_readme(investigator_path / "README.md") or investigator_path.name,
                "workspace_path": _rel(run_root, investigator_path),
                "status": "completed" if synthesis_md else "running",
                "subagent_ids": [item["id"] for item in fallback_subagents],
                "synthesis_md": synthesis_md,
                "artifact_meta": _artifact_meta(investigator_path / "synthesis.md"),
            }
        )

    critiques = []
    for path in sorted((run_root / "critique").glob("*")):
        artifact = path / "critique.md"
        if path.is_dir():
            critiques.append(
                {
                    "critic_id": path.name,
                    "lens": _critic_lens(path.name),
                    "status": "completed" if artifact.exists() else "planned",
                    "workspace_path": _rel(run_root, path),
                    "markdown": _read_text(artifact),
                    "artifact_meta": _artifact_meta(artifact),
                }
            )

    shared = {
        name.replace(".md", ""): {
            "path": f"shared/{name}",
            "content": _read_text(run_root / "shared" / name),
            "artifact_meta": _artifact_meta(run_root / "shared" / name),
        }
        for name in SHARED_ARTIFACTS
        if (run_root / "shared" / name).exists()
    }

    final_path = run_root / "final" / "research_deep_dive_report.md"
    snapshot = {
        "metadata": {
            **summary,
            "stage": summary["status"],
        },
        "investigators": investigators,
        "subagents": subagents,
        "shared": shared,
        "critiques": critiques,
        "final_report": {
            "available": final_path.exists(),
            "path": "final/research_deep_dive_report.md",
            "markdown": _read_text(final_path),
            "artifact_meta": _artifact_meta(final_path),
        },
    }
    snapshot["counts"] = {
        "investigators": len(investigators),
        "subagents": len(subagents),
        "completed_subagents": sum(1 for item in subagents if item["status"] == "completed"),
        "syntheses": sum(1 for item in investigators if item.get("synthesis_md")),
        "critiques": sum(1 for item in critiques if item["status"] == "completed"),
        "tool_events": sum(len(item.get("tool_events") or []) for item in subagents),
    }
    return snapshot


def _snapshot_subagent(
    run_root: Path,
    plan: dict[str, Any],
    sub_plan: dict[str, Any],
) -> dict[str, Any]:
    subagent_id = str(sub_plan.get("subagent_id") or Path(sub_plan.get("workspace_path", "")).name)
    investigator_id = str(sub_plan.get("investigator_id") or plan.get("investigator_id") or "")
    subagent_path = run_root / "investigators" / slugify(investigator_id) / "subagents" / slugify(subagent_id)
    return _snapshot_subagent_common(
        run_root=run_root,
        subagent_path=subagent_path,
        subagent_id=subagent_id,
        investigator_id=investigator_id,
        section_title=str(sub_plan.get("section_title") or plan.get("section_title") or ""),
        taste=sub_plan.get("taste") or _read_json(subagent_path / "taste.json") or {},
        allowed_tools=list(sub_plan.get("allowed_tools") or []),
        max_tool_calls=int(sub_plan.get("max_tool_calls") or 0),
    )


def _snapshot_subagent_from_path(run_root: Path, investigator_path: Path, subagent_path: Path) -> dict[str, Any]:
    readme = _read_text(subagent_path / "README.md")
    return _snapshot_subagent_common(
        run_root=run_root,
        subagent_path=subagent_path,
        subagent_id=subagent_path.name,
        investigator_id=investigator_path.name,
        section_title=_markdown_field(readme, "Section") or "",
        taste=_read_json(subagent_path / "taste.json") or {},
        allowed_tools=[],
        max_tool_calls=_int_or_zero(_markdown_field(readme, "Max tool calls")),
    )


def _snapshot_subagent_common(
    *,
    run_root: Path,
    subagent_path: Path,
    subagent_id: str,
    investigator_id: str,
    section_title: str,
    taste: dict[str, Any],
    allowed_tools: list[str],
    max_tool_calls: int,
) -> dict[str, Any]:
    artifacts = {name.removesuffix(".md"): _read_text(subagent_path / name) for name in SUBAGENT_ARTIFACTS}
    artifact_meta = {name.removesuffix(".md"): _artifact_meta(subagent_path / name) for name in SUBAGENT_ARTIFACTS}
    tool_events = _read_tool_events(subagent_path / "tool_calls.jsonl")
    budget = _budget_from_tool_events(tool_events, max_tool_calls=max_tool_calls)
    status = "completed" if artifacts.get("handoff") else ("running" if tool_events else "planned")
    summary = _final_summary(tool_events) or _handoff_summary(artifacts.get("handoff", ""))
    return {
        "id": subagent_id,
        "investigator_id": investigator_id,
        "section_title": section_title,
        "workspace_path": _rel(run_root, subagent_path),
        "status": status,
        "taste": taste,
        "allowed_tools": allowed_tools,
        "max_tool_calls": max_tool_calls,
        "budget": budget,
        "summary": summary,
        "artifacts": artifacts,
        "artifact_meta": artifact_meta,
        "tool_events": tool_events,
    }


def _read_tool_events(path: Path, limit: int = 1200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(_compact_tool_event(entry))
    return events[-limit:]


def _compact_tool_event(entry: dict[str, Any]) -> dict[str, Any]:
    action = entry.get("action") if isinstance(entry.get("action"), dict) else {}
    tool_name = entry.get("tool_name") or action.get("tool_name") or action.get("action") or ""
    return {
        "ts": entry.get("ts"),
        "type": entry.get("type"),
        "step": entry.get("step"),
        "tool_name": tool_name,
        "arguments": entry.get("arguments") or action.get("arguments") or {},
        "action": action or entry.get("action") or {},
        "result_preview": _preview(entry.get("result")),
        "reason": entry.get("reason", ""),
        "error": entry.get("error", ""),
        "error_type": entry.get("error_type", ""),
        "tool_calls_used": entry.get("tool_calls_used"),
        "research_tool_calls_used": entry.get("research_tool_calls_used"),
        "workspace_tool_calls_used": entry.get("workspace_tool_calls_used"),
    }


def _budget_from_tool_events(events: list[dict[str, Any]], *, max_tool_calls: int) -> dict[str, int]:
    research = 0
    workspace = 0
    llm_steps = 0
    total = 0
    for event in events:
        research = max(research, _int_or_zero(event.get("research_tool_calls_used")))
        workspace = max(workspace, _int_or_zero(event.get("workspace_tool_calls_used")))
        total = max(total, _int_or_zero(event.get("tool_calls_used")))
        llm_steps = max(llm_steps, _int_or_zero(event.get("step")))
    return {
        "research_used": research if research else total,
        "research_max": max_tool_calls,
        "workspace_used": workspace,
        "workspace_max": 0,
        "llm_steps": llm_steps,
    }


def _load_plans(run_root: Path) -> list[dict[str, Any]]:
    plans = []
    for path in sorted((run_root / "shared").glob("investigator_*_plan.json")):
        data = _read_json(path)
        if isinstance(data, dict):
            plans.append(data)
    return plans


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""


def _artifact_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "char_count": 0, "mtime": ""}
    text = _read_text(path)
    return {
        "exists": True,
        "char_count": len(text),
        "mtime": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def _count_jsonl_files(paths: Any) -> int:
    count = 0
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as handle:
                count += sum(1 for line in handle if line.strip())
        except OSError:
            continue
    return count


def _infer_status(
    *,
    final_report: Path,
    critique_count: int,
    synthesis_count: int,
    handoff_count: int,
    plans: list[dict[str, Any]],
) -> str:
    if final_report.exists():
        return "completed"
    if critique_count:
        return "critique"
    if synthesis_count:
        return "investigator_synthesis"
    if handoff_count:
        return "subagent_research"
    if plans:
        return "investigator_planning"
    return "bootstrap"


def _prompt_fields_from_plans(plans: list[dict[str, Any]]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for plan in plans:
        prompt = str(plan.get("system_prompt") or "")
        for key, value in _PROMPT_FIELD_RE.findall(prompt):
            fields.setdefault(key.strip().lower(), value.strip())
    return fields


def _regex_value(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _markdown_field(text: str, name: str) -> str:
    match = re.search(rf"-\s*{re.escape(name)}:\s*`([^`]+)`", text)
    return match.group(1).strip() if match else ""


def _read_section_from_readme(path: Path) -> str:
    return _markdown_field(_read_text(path), "Section")


def _critic_lens(critic_id: str) -> str:
    return {
        "coverage_critic": "coverage and search recall",
        "novelty_critic": "novelty and closest-prior-work pressure",
        "evidence_critic": "source grounding and citation quality",
        "skeptic_critic": "overclaiming, contradictions, and weak inference",
    }.get(critic_id, critic_id.replace("_", " "))


def _preview(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, dict) and value.get("truncated") and value.get("prefix"):
        text = str(value.get("prefix"))
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, default=str)
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def _final_summary(events: list[dict[str, Any]]) -> str:
    for event in reversed(events):
        action = event.get("action")
        if isinstance(action, dict) and action.get("action") == "final":
            return str(action.get("summary") or "")
    return ""


def _handoff_summary(text: str, limit: int = 500) -> str:
    lines = [line.strip("#- *` ") for line in text.splitlines() if line.strip()]
    return " ".join(lines[:4])[:limit]


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
