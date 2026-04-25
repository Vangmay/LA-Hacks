"""Monitored JSON-action loop for live deep-dive agents."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .llm import DeepDiveLLMProvider
from .llm import normalize_model_content
from .models import AgentExitReason, AgentModelRole, AgentRunResult, ResearchStage, SubagentPlan
from .tool_runtime import ToolRuntime
from .workspace import WorkspaceManager


WORKSPACE_TOOLS = {
    "read_workspace_file",
    "read_workspace_markdown",
    "write_workspace_markdown",
    "append_workspace_markdown",
    "patch_workspace_file",
}

PLACEHOLDER_MARKERS = (
    "no papers collected yet",
    "no findings have been distilled yet",
    "no findings yet",
    "no queries yet",
    "nothing recorded yet",
)

ARTIFACT_QUALITY_CONTRACTS: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "queries.md": [
        ("exact query or tool call", ("query", "searched", "tool")),
        ("parameters or filters", ("param", "limit", "offset", "field", "filter", "sort")),
        ("result count or failure state", ("result", "returned", "total", "empty", "failed", "error")),
        ("why it was run or follow-up it suggested", ("why", "purpose", "rationale", "follow-up", "next")),
    ],
    "papers.md": [
        ("paper identifier or source", ("paper id", "paperid", "arxiv", "semantic scholar", "s2", "doi")),
        ("title/year/metadata", ("title", "year", "publication", "venue", "authors")),
        ("relevance note", ("relevance", "relevant", "matters", "supports", "bucket", "why")),
    ],
    "findings.md": [
        ("finding, gap, risk, or proposal statement", ("finding", "gap", "risk", "proposal", "claim")),
        ("evidence grounding", ("evidence", "paper", "supports", "because", "based on")),
        ("uncertainty, limitation, or next check", ("uncertain", "uncertainty", "speculative", "limitation", "next", "falsification")),
    ],
    "memory.md": [
        ("stable running state", ("stable", "state", "fact", "remember", "current")),
        ("search thread or query direction", ("search", "thread", "query", "bucket")),
        ("open question, contradiction, or handoff prep", ("open", "question", "contradiction", "handoff", "next")),
    ],
}

TOP_LEVEL_ARGUMENT_KEYS = {
    "content",
    "end_line",
    "fields",
    "heading",
    "ids",
    "limit",
    "offset",
    "paper_id",
    "path",
    "query",
    "replacement",
    "sort",
    "start_line",
    "year",
}


def action_instructions(workspace_write_char_budget: int) -> str:
    return f"""Return exactly one JSON object.

Allowed forms:

{{"action":"<allowed tool>","arguments":{{...}},"memory_update":"short markdown note"}}
{{"action":"final","summary":"short summary","handoff_markdown":"# Hand-Off\\n..."}}

Rules:
- The `action` field must be exactly one allowed tool name or exactly `"final"`.
- Do not use a separate `tool_name` field.
- Valid: `{{"action":"read_workspace_markdown","arguments":{{"path":"memory.md"}}}}`.
- Valid search:
  `{{"action":"paper_bulk_search","arguments":{{"query":"attention ablation","limit":20}}}}`.
- Valid workspace append:
  `{{"action":"append_workspace_markdown","arguments":{{"path":"findings.md","heading":"Closest prior work","content":"..."}}}}`.
- Invalid: `{{"action":"tool","tool_name":"read_workspace_markdown","arguments":{{"path":"memory.md"}}}}`.
- Invalid search:
  `{{"action":"paper_bulk_search","query":"attention ablation","limit":20}}`.
- Invalid workspace append:
  `{{"action":"append_workspace_markdown","arguments":{{"heading":"Closest prior work","content":"..."}}}}`.
- Use only allowed tools.
- Every tool parameter must be inside the `arguments` object. Never put `query`,
  `paper_id`, `limit`, `fields`, `year`, `sort`, `path`, `heading`, or
  `content` at the top level.
- Every workspace read/write/append action must include `arguments.path`.
- Every workspace write/append action must include `arguments.content`.
- Prefer workspace append/write tools after research tools so durable memory stays current.
- Workspace read/write/append tools have a separate high budget and do not
  spend the research/API budget.
- Search/API tools spend the research budget. When that budget is exhausted,
  you must switch into workspace-only finalization: update `queries.md`,
  `papers.md`, `findings.md`, `memory.md`, and then return `final`.
- For `papers.md`, write at most one paper record per action.
- For `findings.md`, write at most one finding or proposal seed per action.
- Do not place full abstracts in workspace write/append action payloads; store
  paper ID, title, year, source, and a compact relevance note.
- Avoid raw double quote characters inside string values; use apostrophes in
  markdown notes unless you correctly JSON-escape the quotes.
- Keep each workspace write concise enough to fit in one valid JSON object.
- Keep `write_workspace_markdown` and `append_workspace_markdown` `content`
  payloads under `{workspace_write_char_budget}` characters per action.
- For long notes, split them across multiple append actions instead of one large
  JSON payload.
- The markdown files should be detailed overall. The per-action budget is only
  a JSON safety boundary; continue appending additional chunks until the
  appropriate files contain enough evidence, papers, query details, findings,
  and durable memory. Placeholder text such as 'no papers collected yet' or
  'no findings yet' is not acceptable documentation.
- Artifact content contract:
  - `queries.md`: exact query/tool, parameters or filters, result count or
    failure state, and why the query was run or what follow-up it suggested.
  - `papers.md`: paper identifier/source, title/year/metadata, and relevance
    note for why the paper matters.
  - `findings.md`: finding/gap/risk/proposal statement, evidence grounding,
    and uncertainty, limitation, or next check.
  - `memory.md`: stable running state, search thread or query direction, and
    open question, contradiction, or handoff preparation.
- Before final, ensure handoff_markdown contains searched queries, important papers, findings, uncertainty, and next steps.
- Do not include prose outside the JSON object.
"""


class LiveAgentRunner:
    def __init__(
        self,
        *,
        llm: DeepDiveLLMProvider,
        tools: ToolRuntime,
        workspace: WorkspaceManager,
        max_steps: int,
        workspace_write_char_budget: int,
        max_workspace_tool_calls: int,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.workspace = workspace
        self.max_steps = max_steps
        self.workspace_write_char_budget = workspace_write_char_budget
        self.max_workspace_tool_calls = max_workspace_tool_calls

    async def run_subagent(self, plan: SubagentPlan, stage: ResearchStage) -> AgentRunResult:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": plan.system_prompt},
            {
                "role": "user",
                "content": (
                    action_instructions(self.workspace_write_char_budget)
                    + "\nAllowed executable tools:\n"
                    + "\n".join(f"- {name}" for name in sorted(plan.allowed_tools))
                    + "\n\nStart by reading memory.md, then execute the strongest research loop for your taste."
                    + "\n\nCurrent artifact status:\n"
                    + self._artifact_status(plan.workspace_path)
                    + "\n\n"
                    + self._documentation_repair_directive(plan.workspace_path)
                ),
            },
        ]
        trace_path = plan.workspace_path / "tool_calls.jsonl"
        research_tool_calls_used = 0
        workspace_tool_calls_used = 0
        llm_steps = 0
        exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
        summary = ""
        research_budget_exhausted = False

        for _ in range(self.max_steps):
            llm_steps += 1
            action = await self.llm.chat_json(role=plan.model_role, messages=messages)
            self._write_trace(trace_path, {"type": "llm_action", "step": llm_steps, "action": action})

            action_type = action.get("action")
            if action_type == "final":
                repair_target = self._documentation_repair_target(plan.workspace_path)
                if repair_target:
                    repair_issue = _artifact_quality_issue(
                        (plan.workspace_path / repair_target).read_text(encoding="utf-8")
                        if (plan.workspace_path / repair_target).exists()
                        else "",
                        repair_target,
                    )
                    messages.append({"role": "assistant", "content": json.dumps(action)})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"`{repair_target}` is not ready for final handoff: {repair_issue}. "
                                "Return exactly one JSON object now using `append_workspace_markdown` "
                                f"with `arguments.path` set to `{repair_target}` and content that satisfies "
                                "that artifact's required content contract."
                            ),
                        }
                    )
                    continue
                handoff = action.get("handoff_markdown", "")
                if not handoff:
                    raise RuntimeError(f"{plan.subagent_id} final action omitted handoff_markdown")
                self.workspace.write_owned_markdown(plan.workspace_path, "handoff.md", handoff)
                summary = action.get("summary") or "Live subagent completed."
                exit_reason = AgentExitReason.COMPLETED
                break

            validation_error = self._action_validation_error(action, plan)
            if validation_error:
                self._write_rejected_action_trace(
                    trace_path,
                    action=action,
                    reason=validation_error,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                messages.append({"role": "assistant", "content": json.dumps(action)})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Rejected action without spending any tool budget: "
                            f"{validation_error}\n\n"
                            "Return exactly one corrected JSON object. Keep every tool parameter "
                            "inside `arguments`; workspace actions need `arguments.path`, and "
                            "workspace write/append actions need `arguments.content`."
                        ),
                    }
                )
                continue

            tool_name = str(action_type)

            arguments = action.get("arguments")
            assert isinstance(arguments, dict)

            is_workspace_tool = tool_name in WORKSPACE_TOOLS
            if is_workspace_tool:
                if workspace_tool_calls_used >= self.max_workspace_tool_calls:
                    raise RuntimeError(
                        f"{plan.subagent_id} exceeded workspace tool budget "
                        f"({self.max_workspace_tool_calls})"
                    )
            else:
                if research_budget_exhausted or research_tool_calls_used >= plan.max_tool_calls:
                    research_budget_exhausted = True
                    self._write_rejected_action_trace(
                        trace_path,
                        action=action,
                        reason="research/API tool budget is exhausted; only workspace tools and final are allowed",
                        llm_steps=llm_steps,
                        research_tool_calls_used=research_tool_calls_used,
                        workspace_tool_calls_used=workspace_tool_calls_used,
                    )
                    messages.append({"role": "assistant", "content": json.dumps(action)})
                    messages.append(
                        {
                            "role": "user",
                            "content": self._research_budget_exhausted_message(plan.workspace_path),
                        }
                    )
                    continue

            try:
                result = await self.tools.execute(tool_name, arguments, plan.workspace_path)
            except Exception as exc:
                self._write_trace(
                    trace_path,
                    {
                        "type": "tool_error",
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "error": str(exc),
                        "research_tool_calls_used": research_tool_calls_used,
                        "workspace_tool_calls_used": workspace_tool_calls_used,
                    },
                )
                raise
            if is_workspace_tool:
                workspace_tool_calls_used += 1
            else:
                research_tool_calls_used += 1
            trace_entry = {
                "type": "tool_result",
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
                "tool_calls_used": research_tool_calls_used + workspace_tool_calls_used,
                "research_tool_calls_used": research_tool_calls_used,
                "workspace_tool_calls_used": workspace_tool_calls_used,
            }
            self._write_trace(trace_path, trace_entry)

            memory_update = action.get("memory_update")
            if memory_update:
                self.workspace.append_owned_markdown(
                    plan.workspace_path,
                    "memory.md",
                    str(memory_update),
                    heading=f"Step {llm_steps}: {tool_name}",
                )

            messages.append({"role": "assistant", "content": json.dumps(action)})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool result:\n"
                        + json.dumps(result, default=str)
                        + "\n\nCurrent artifact status:\n"
                        + self._artifact_status(plan.workspace_path)
                        + "\n\n"
                        + self._documentation_repair_directive(plan.workspace_path)
                        + (
                            "\n\n" + self._research_budget_exhausted_message(plan.workspace_path)
                            if research_budget_exhausted
                            else ""
                        )
                    ),
                }
            )

            if not is_workspace_tool and research_tool_calls_used >= plan.max_tool_calls:
                exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
                research_budget_exhausted = True
                messages.append(
                    {
                        "role": "user",
                        "content": self._research_budget_exhausted_message(plan.workspace_path),
                    }
                )

        if not (plan.workspace_path / "handoff.md").exists():
            handoff = await self._force_handoff(plan, messages, exit_reason)
            self.workspace.write_owned_markdown(plan.workspace_path, "handoff.md", handoff)
            summary = f"{plan.subagent_id} stopped at {exit_reason.value}; forced handoff written."

        profile = self.llm.profile_for(plan.model_role)
        return AgentRunResult(
            agent_id=plan.subagent_id,
            stage=stage,
            exit_reason=exit_reason,
            tool_calls_used=research_tool_calls_used,
            workspace_path=plan.workspace_path,
            artifacts=[
                plan.workspace_path / "handoff.md",
                plan.workspace_path / "findings.md",
                plan.workspace_path / "papers.md",
                plan.workspace_path / "queries.md",
                plan.workspace_path / "memory.md",
                trace_path,
            ],
            summary=summary or f"{plan.subagent_id} completed live research loop.",
            model_provider=profile.provider,
            model_name=profile.model,
            llm_steps_used=llm_steps,
            tool_trace_path=trace_path,
            research_tool_calls_used=research_tool_calls_used,
            workspace_tool_calls_used=workspace_tool_calls_used,
        )

    async def _force_handoff(
        self,
        plan: SubagentPlan,
        messages: list[dict[str, str]],
        exit_reason: AgentExitReason,
    ) -> str:
        messages = messages + [
            {
                "role": "user",
                "content": (
                    f"Tool boundary reached with exit reason `{exit_reason.value}`. "
                    "Write only the final handoff markdown now. Include searched tools, paper IDs, "
                    "findings, uncertainty, and next steps. Do not request another tool."
                ),
            }
        ]
        content = normalize_model_content(
            await self.llm.chat_markdown(role=plan.model_role, messages=messages)
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return content
        if parsed.get("action") == "final" and parsed.get("handoff_markdown"):
            return str(parsed["handoff_markdown"])
        return content

    def _write_trace(self, path: Path, entry: dict[str, Any]) -> None:
        entry = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def _write_rejected_action_trace(
        self,
        path: Path,
        *,
        action: dict[str, Any],
        reason: str,
        llm_steps: int,
        research_tool_calls_used: int,
        workspace_tool_calls_used: int,
    ) -> None:
        self._write_trace(
            path,
            {
                "type": "rejected_action",
                "step": llm_steps,
                "action": action,
                "reason": reason,
                "research_tool_calls_used": research_tool_calls_used,
                "workspace_tool_calls_used": workspace_tool_calls_used,
            },
        )

    def _action_validation_error(self, action: dict[str, Any], plan: SubagentPlan) -> str:
        action_type = action.get("action")
        if action_type == "tool":
            return "obsolete `action=tool` protocol is not supported; put the tool name directly in `action`"
        if not isinstance(action_type, str):
            return "`action` must be a string tool name or `final`"
        if action_type not in plan.allowed_tools:
            return f"`{action_type}` is not an allowed executable tool for this agent"
        arguments = action.get("arguments")
        if not isinstance(arguments, dict):
            misplaced = sorted(TOP_LEVEL_ARGUMENT_KEYS.intersection(action))
            if misplaced:
                return (
                    "tool parameters appeared at the top level instead of inside `arguments`: "
                    + ", ".join(misplaced)
                )
            return "`arguments` must be an object"
        misplaced = sorted(TOP_LEVEL_ARGUMENT_KEYS.intersection(action))
        if misplaced:
            return (
                "tool parameters appeared at the top level instead of inside `arguments`: "
                + ", ".join(misplaced)
            )
        if action_type in WORKSPACE_TOOLS:
            if not arguments.get("path"):
                return f"`{action_type}` requires `arguments.path`"
            if action_type in {"write_workspace_markdown", "append_workspace_markdown"}:
                content = arguments.get("content")
                if not isinstance(content, str) or not content.strip():
                    return f"`{action_type}` requires non-empty `arguments.content`"
        return ""

    def _artifact_status(self, workspace_path: Path) -> str:
        rows = []
        for relative_path in ("memory.md", "queries.md", "papers.md", "findings.md", "handoff.md"):
            path = workspace_path / relative_path
            if not path.exists():
                rows.append(f"- `{relative_path}`: missing")
                continue
            text = path.read_text(encoding="utf-8")
            meaningful = _meaningful_markdown_chars(text)
            issue = _artifact_quality_issue(text, relative_path)
            state = "ready" if not issue else f"needs repair: {issue}"
            rows.append(f"- `{relative_path}`: {state}; {meaningful} meaningful chars")
        return "\n".join(rows)

    def _documentation_repair_directive(self, workspace_path: Path) -> str:
        target = self._documentation_repair_target(workspace_path)
        if not target:
            return (
                "Documentation status: required markdown files have started accumulating content. "
                "Keep enriching them with detailed, chunked notes as research progresses."
            )
        issue = _artifact_quality_issue(
            (workspace_path / target).read_text(encoding="utf-8")
            if (workspace_path / target).exists()
            else "",
            target,
        )
        return (
            "Documentation repair needed before more broad searching: "
            f"`{target}` is not satisfying its artifact contract: {issue}. "
            "The next action must append a detailed, evidence-bearing chunk to "
            "that file using `append_workspace_markdown`. Do not run another "
            "search until this file has the required kind of content."
        )

    def _documentation_repair_target(self, workspace_path: Path) -> str:
        for relative_path in ("queries.md", "papers.md", "findings.md", "memory.md"):
            path = workspace_path / relative_path
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if _artifact_quality_issue(text, relative_path):
                return relative_path
        return ""

    def _research_budget_exhausted_message(self, workspace_path: Path) -> str:
        return (
            "Research/API tool budget is exhausted. Search/API tools are now forbidden. "
            "You still have a separate large workspace-tool budget. Use only workspace "
            "tools to make the markdown artifacts detailed: update `queries.md`, "
            "`papers.md`, `findings.md`, and `memory.md`, then return `final` with "
            "a handoff. Current artifact status:\n"
            + self._artifact_status(workspace_path)
            + "\n\n"
            + self._documentation_repair_directive(workspace_path)
        )


def _meaningful_markdown_chars(text: str) -> int:
    meaningful_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        meaningful_lines.append(stripped)
    return len("\n".join(meaningful_lines))


def _artifact_quality_issue(text: str, relative_path: str) -> str:
    if _meaningful_markdown_chars(text) == 0:
        return "empty beyond headings"
    lowered = text.lower()
    placeholders = [marker for marker in PLACEHOLDER_MARKERS if marker in lowered]
    if placeholders:
        return f"placeholder text still present: {placeholders[0]}"
    missing = [
        label
        for label, terms in ARTIFACT_QUALITY_CONTRACTS.get(relative_path, [])
        if not any(term in lowered for term in terms)
    ]
    if missing:
        return "missing " + "; missing ".join(missing)
    return ""


def _action_updates_markdown(action: dict[str, Any], relative_path: str) -> bool:
    if action.get("action") not in {"append_workspace_markdown", "write_workspace_markdown"}:
        return False
    arguments = action.get("arguments")
    if not isinstance(arguments, dict):
        return False
    if arguments.get("path") != relative_path:
        return False
    content = arguments.get("content")
    return isinstance(content, str) and bool(content.strip())
