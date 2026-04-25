"""Filesystem workspace helpers for isolated research agents."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import InvestigatorPlan, SubagentPlan


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    return "_".join(part for part in cleaned.split("_") if part)[:80] or "untitled"


class WorkspaceManager:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run_root(self, run_id: str) -> Path:
        return self.root / slugify(run_id)

    def prepare_run(self, run_id: str) -> Path:
        root = self.run_root(run_id)
        for rel in ("shared", "investigators", "critique", "final"):
            (root / rel).mkdir(parents=True, exist_ok=True)
        self.write_markdown(
            root / "README.md",
            "# Research Deep-Dive Run\n\n"
            f"- Run id: `{run_id}`\n"
            f"- Created UTC: `{datetime.now(timezone.utc).isoformat()}`\n\n"
            "This folder is owned by the research deep-dive orchestrator.\n",
        )
        return root

    def investigator_path(self, run_id: str, investigator_id: str) -> Path:
        path = self.run_root(run_id) / "investigators" / slugify(investigator_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def subagent_path(self, investigator_path: Path, subagent_id: str) -> Path:
        path = investigator_path / "subagents" / slugify(subagent_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_markdown(self, path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_json(self, path: Path, data: Any) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    def initialize_investigator(self, plan: InvestigatorPlan) -> None:
        self.write_markdown(
            plan.workspace_path / "README.md",
            f"# {plan.investigator_id}\n\n"
            f"- Section: `{plan.section_title}`\n"
            "- Owns synthesis for this section only.\n"
            "- Reads its subagent folders after their tool budgets are exhausted.\n",
        )
        self.write_markdown(plan.workspace_path / "system_prompt.md", plan.system_prompt)

    def initialize_subagent(self, plan: SubagentPlan) -> None:
        self.write_markdown(
            plan.workspace_path / "README.md",
            f"# {plan.subagent_id}\n\n"
            f"- Investigator: `{plan.investigator_id}`\n"
            f"- Section: `{plan.section_title}`\n"
            f"- Taste: `{plan.taste.label}`\n"
            f"- Max tool calls: `{plan.max_tool_calls}`\n",
        )
        self.write_markdown(plan.workspace_path / "system_prompt.md", plan.system_prompt)
        self.write_markdown(
            plan.workspace_path / "memory.md",
            "# Memory\n\n"
            "## Stable Facts\n\n"
            "## Search Threads\n\n"
            "## Candidate Papers\n\n"
            "## Open Questions\n\n"
            "## Hand-Off Summary\n\n",
        )
        self.write_json(plan.workspace_path / "taste.json", plan.taste.model_dump())
