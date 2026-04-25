"""Monitored JSON-action loop for live deep-dive agents."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .llm import DeepDiveLLMProvider
from .llm import LLMJSONParseError
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
        ("parameters or filters", ("argument", "param", "limit", "offset", "field", "filter", "sort")),
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
        ("uncertainty, limitation, or next check", ("caveat", "confidence", "uncertain", "uncertainty", "speculative", "limitation", "next", "falsification")),
    ],
    "proposal_seeds.md": [
        ("proposal seed or idea statement", ("proposal seed", "candidate novelty", "core idea", "claim")),
        ("evidence trigger", ("evidence", "trigger", "paper", "finding", "gap", "contradiction")),
        ("collision or falsification risk", ("collision", "prior", "future", "falsification", "risk")),
        ("validation path", ("validation", "experiment", "proof", "benchmark", "implementation")),
    ],
    "memory.md": [
        ("stable running state", ("stable", "state", "fact", "remember", "current")),
        ("search thread or query direction", ("search", "thread", "query", "bucket")),
        ("open question, contradiction, or handoff prep", ("open", "question", "contradiction", "handoff", "next")),
    ],
}

PAPER_RESULT_TOOLS = {
    "resolve_arxiv_paper",
    "get_paper_metadata",
    "get_paper_tldr",
    "get_paper_embedding",
    "get_references",
    "get_citations",
    "paper_bulk_search",
    "paper_relevance_search",
    "batch_get_papers",
    "rank_candidates_by_specter2_similarity",
    "google_scholar_search",
}

RESEARCH_RESULT_TOOLS = PAPER_RESULT_TOOLS

STRUCTURED_SECTION_FIELDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "queries.md": (
        "Query",
        (
            "Tool",
            "Arguments",
            "Result count",
            "Top result IDs",
            "Why this query was run",
            "Follow-up",
        ),
    ),
    "papers.md": (
        "Paper",
        (
            "Paper ID",
            "Year",
            "Source bucket",
            "Found by",
            "Relation to seed",
            "Why it matters",
            "Caveat",
        ),
    ),
    "findings.md": (
        "Finding",
        (
            "Claim",
            "Confidence",
            "Evidence",
            "Why it matters",
            "Caveat",
        ),
    ),
    "proposal_seeds.md": (
        "Proposal Seed",
        (
            "Status",
            "Seed-paper hook",
            "Evidence trigger",
            "Candidate novelty",
            "Technical mechanism",
            "Closest prior-work collision",
            "Minimum validation",
            "Falsification risk",
            "Why this is not generic",
            "Confidence",
            "Required next search",
        ),
    ),
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


@dataclass(frozen=True)
class WorkspaceEvidenceState:
    research_tool_results: int
    paper_ids_seen: int
    query_sections: int
    paper_sections: int
    finding_sections: int
    proposal_seed_sections: int
    has_any_search: bool
    has_paper_results: bool
    has_multiple_sources: bool
    has_candidate_papers: bool


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
- The runtime automatically records research/API tool outputs into
  `raw_tool_results.jsonl` and appends structured `Query:` entries to
  `queries.md`. Your job is to distill that evidence into selected `Paper:`
  records, `Finding:` records, memory, and final handoff.
- The markdown files should be detailed overall. The per-action budget is only
  a JSON safety boundary; continue appending additional chunks until the
  appropriate files contain enough evidence, papers, query details, findings,
  and durable memory. Placeholder text such as 'no papers collected yet' or
  'no findings yet' is not acceptable documentation.
- Artifact content contract:
  - `queries.md`: exact query/tool, parameters or filters, result count or
    failure state, and why the query was run or what follow-up it suggested.
    Preferred shape: `## Query: <short name>` with `Tool`, `Arguments`,
    `Result count`, `Top result IDs`, `Why this query was run`, and `Follow-up`.
  - `papers.md`: paper identifier/source, title/year/metadata, and relevance
    note for why the paper matters.
    Preferred shape: `## Paper: <title or id>` with `Paper ID`, `Year`,
    `Source bucket`, `Found by`, `Relation to seed`, `Why it matters`, and
    `Caveat`.
  - `findings.md`: finding/gap/risk/proposal statement, evidence grounding,
    and uncertainty, limitation, or next check.
    Preferred shape: `## Finding: <short name>` with `Claim`, `Confidence`,
    `Evidence`, `Why it matters`, and `Caveat`.
  - `proposal_seeds.md` in novelty mode: concrete idea seeds derived from
    evidence, not generic future-work prose. Preferred shape:
    `## Proposal Seed: <title>` with status, seed-paper hook, evidence trigger,
    candidate novelty, mechanism, collision risks, validation, falsification,
    why it is not generic, confidence, and next search.
  - `memory.md`: stable running state, search thread or query direction, and
    open question, contradiction, or handoff preparation.
- Use structured headings:
  - `## Query: <short name>`
  - `## Paper: <title or paper id>`
  - `## Finding: <short name>`
  - `## Proposal Seed: <title>`
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
                    + self._artifact_contract_message()
                ),
            },
        ]
        trace_path = plan.workspace_path / "tool_calls.jsonl"
        raw_trace_path = plan.workspace_path / "raw_tool_results.jsonl"
        research_tool_calls_used = 0
        workspace_tool_calls_used = 0
        llm_steps = 0
        exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
        summary = ""
        research_budget_exhausted = False

        for _ in range(self.max_steps):
            llm_steps += 1
            try:
                action = await self.llm.chat_json(role=plan.model_role, messages=messages)
            except LLMJSONParseError as exc:
                self._handle_malformed_json_action(
                    trace_path,
                    messages,
                    exc,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                continue
            if not isinstance(action, dict):
                self._handle_non_object_json_action(
                    trace_path,
                    messages,
                    action,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                continue
            self._write_trace(trace_path, {"type": "llm_action", "step": llm_steps, "action": action})

            action_type = action.get("action")
            if action_type == "final":
                if not self._evidence_state(plan.workspace_path).has_any_search:
                    messages.append({"role": "assistant", "content": json.dumps(action)})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Final is premature because no research/API tool result exists yet. "
                                "Read memory if needed, then run a research/API tool before writing final."
                            ),
                        }
                    )
                    continue
                repair_target = self._documentation_repair_target(plan.workspace_path, before_final=True)
                if repair_target:
                    repair_issue = _artifact_quality_issue(
                        (plan.workspace_path / repair_target).read_text(encoding="utf-8")
                        if (plan.workspace_path / repair_target).exists()
                        else "",
                        repair_target,
                        self._evidence_state(plan.workspace_path),
                        before_final=True,
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
                self._handle_tool_execution_error(
                    trace_path=trace_path,
                    raw_trace_path=raw_trace_path,
                    messages=messages,
                    action=action,
                    tool_name=tool_name,
                    arguments=arguments,
                    exc=exc,
                    is_workspace_tool=is_workspace_tool,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                continue
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
            if not is_workspace_tool:
                self._write_raw_tool_result(
                    raw_trace_path,
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                self._append_auto_query_entry(
                    plan.workspace_path,
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    query_index=research_tool_calls_used,
                )

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
                        + (
                            self._documentation_repair_directive(plan.workspace_path)
                            if research_tool_calls_used > 0 or research_budget_exhausted
                            else self._artifact_contract_message()
                        )
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
            repair_result = await self._workspace_repair_loop(
                plan,
                messages,
                trace_path,
                raw_trace_path,
                research_tool_calls_used,
                workspace_tool_calls_used,
                start_step=llm_steps,
            )
            llm_steps = repair_result["llm_steps"]
            workspace_tool_calls_used = repair_result["workspace_tool_calls_used"]
            exit_reason = repair_result["exit_reason"]
            summary = repair_result["summary"]

        if not (plan.workspace_path / "handoff.md").exists():
            missing = self._missing_final_artifacts(plan.workspace_path)
            if missing:
                exit_reason = AgentExitReason.INCOMPLETE_ARTIFACTS
                handoff = self._forced_incomplete_handoff(plan, exit_reason, missing)
                self.workspace.write_owned_markdown(plan.workspace_path, "handoff.md", handoff)
                summary = (
                    f"{plan.subagent_id} stopped with incomplete artifacts; "
                    "forced incomplete handoff written."
                )
            else:
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
                plan.workspace_path / "proposal_seeds.md",
                plan.workspace_path / "papers.md",
                plan.workspace_path / "queries.md",
                plan.workspace_path / "memory.md",
                trace_path,
                raw_trace_path,
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

    async def _workspace_repair_loop(
        self,
        plan: SubagentPlan,
        messages: list[dict[str, str]],
        trace_path: Path,
        raw_trace_path: Path,
        research_tool_calls_used: int,
        workspace_tool_calls_used: int,
        *,
        start_step: int,
    ) -> dict[str, Any]:
        llm_steps = start_step
        exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
        summary = ""
        if not self._evidence_state(plan.workspace_path).has_any_search:
            return {
                "llm_steps": llm_steps,
                "workspace_tool_calls_used": workspace_tool_calls_used,
                "exit_reason": AgentExitReason.INCOMPLETE_ARTIFACTS,
                "summary": "Workspace repair skipped because no research/API evidence exists.",
            }
        repair_steps = max(80, min(200, self.max_workspace_tool_calls - workspace_tool_calls_used))
        messages.append(
            {
                "role": "user",
                "content": (
                    "Workspace-only repair phase. Search/API tools are forbidden. "
                    "Use workspace tools to repair any missing artifact contracts, then return final. "
                    "Current artifact status:\n"
                    + self._artifact_status(plan.workspace_path)
                    + "\n\n"
                    + self._documentation_repair_directive(plan.workspace_path, before_final=True)
                ),
            }
        )
        for _ in range(repair_steps):
            llm_steps += 1
            try:
                action = await self.llm.chat_json(role=plan.model_role, messages=messages)
            except LLMJSONParseError as exc:
                self._handle_malformed_json_action(
                    trace_path,
                    messages,
                    exc,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                continue
            if not isinstance(action, dict):
                self._handle_non_object_json_action(
                    trace_path,
                    messages,
                    action,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                continue
            self._write_trace(trace_path, {"type": "llm_action", "step": llm_steps, "action": action})
            action_type = action.get("action")
            if action_type == "final":
                if not self._evidence_state(plan.workspace_path).has_any_search:
                    messages.append({"role": "assistant", "content": json.dumps(action)})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Final is premature because no research/API tool result exists yet. "
                                "Use any remaining allowed research/API tool before final."
                            ),
                        }
                    )
                    continue
                repair_target = self._documentation_repair_target(plan.workspace_path, before_final=True)
                if repair_target:
                    messages.append({"role": "assistant", "content": json.dumps(action)})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Final is still premature. "
                                + self._documentation_repair_directive(
                                    plan.workspace_path,
                                    before_final=True,
                                )
                            ),
                        }
                    )
                    continue
                handoff = action.get("handoff_markdown", "")
                if not handoff:
                    messages.append({"role": "assistant", "content": json.dumps(action)})
                    messages.append(
                        {
                            "role": "user",
                            "content": "Final action must include non-empty `handoff_markdown`.",
                        }
                    )
                    continue
                self.workspace.write_owned_markdown(plan.workspace_path, "handoff.md", handoff)
                return {
                    "llm_steps": llm_steps,
                    "workspace_tool_calls_used": workspace_tool_calls_used,
                    "exit_reason": AgentExitReason.COMPLETED,
                    "summary": action.get("summary") or "Live subagent completed after workspace repair.",
                }

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
                            f"{validation_error}. Use a workspace tool or final."
                        ),
                    }
                )
                continue

            tool_name = str(action_type)
            arguments = action.get("arguments")
            assert isinstance(arguments, dict)
            if tool_name not in WORKSPACE_TOOLS:
                self._write_rejected_action_trace(
                    trace_path,
                    action=action,
                    reason="workspace-only repair phase forbids research/API tools",
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                messages.append({"role": "assistant", "content": json.dumps(action)})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Search/API tools are forbidden now. Use only workspace tools to repair "
                            "artifacts, then return final."
                        ),
                    }
                )
                continue
            if workspace_tool_calls_used >= self.max_workspace_tool_calls:
                break
            try:
                result = await self.tools.execute(tool_name, arguments, plan.workspace_path)
            except Exception as exc:
                self._handle_tool_execution_error(
                    trace_path=trace_path,
                    raw_trace_path=raw_trace_path,
                    messages=messages,
                    action=action,
                    tool_name=tool_name,
                    arguments=arguments,
                    exc=exc,
                    is_workspace_tool=True,
                    llm_steps=llm_steps,
                    research_tool_calls_used=research_tool_calls_used,
                    workspace_tool_calls_used=workspace_tool_calls_used,
                )
                continue
            workspace_tool_calls_used += 1
            self._write_trace(
                trace_path,
                {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "tool_calls_used": research_tool_calls_used + workspace_tool_calls_used,
                    "research_tool_calls_used": research_tool_calls_used,
                    "workspace_tool_calls_used": workspace_tool_calls_used,
                },
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
                        + self._documentation_repair_directive(
                            plan.workspace_path,
                            before_final=True,
                        )
                    ),
                }
            )
        return {
            "llm_steps": llm_steps,
            "workspace_tool_calls_used": workspace_tool_calls_used,
            "exit_reason": exit_reason,
            "summary": summary,
        }

    def _forced_incomplete_handoff(
        self,
        plan: SubagentPlan,
        exit_reason: AgentExitReason,
        missing: list[str],
    ) -> str:
        return (
            "# Forced Incomplete Handoff\n\n"
            f"- Agent: `{plan.subagent_id}`\n"
            f"- Exit reason: `{exit_reason.value}`\n\n"
            "The runtime could not obtain complete markdown artifacts before the "
            "loop boundary. Treat this handoff as incomplete and do not use it as "
            "strong evidence without inspecting raw tool logs.\n\n"
            "## Missing Or Weak Required Artifacts\n\n"
            + "\n".join(f"- {item}" for item in missing)
            + "\n\n"
            "## Available Artifact Status\n\n"
            + self._artifact_status(plan.workspace_path)
            + "\n"
        )

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

    def _handle_malformed_json_action(
        self,
        trace_path: Path,
        messages: list[dict[str, str]],
        exc: LLMJSONParseError,
        *,
        llm_steps: int,
        research_tool_calls_used: int,
        workspace_tool_calls_used: int,
    ) -> None:
        raw = exc.content.strip()
        self._write_rejected_action_trace(
            trace_path,
            action={"raw_content": raw[:4000]},
            reason="model response was not parseable as one JSON object",
            llm_steps=llm_steps,
            research_tool_calls_used=research_tool_calls_used,
            workspace_tool_calls_used=workspace_tool_calls_used,
        )
        messages.append({"role": "assistant", "content": raw[:4000]})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Rejected response without spending any tool budget: it was not parseable "
                    "as exactly one JSON object. Return exactly one corrected JSON object now. "
                    "Use JSON string escaping for markdown newlines and quotes; keep every tool "
                    "parameter inside `arguments`."
                ),
            }
        )

    def _handle_non_object_json_action(
        self,
        trace_path: Path,
        messages: list[dict[str, str]],
        action: Any,
        *,
        llm_steps: int,
        research_tool_calls_used: int,
        workspace_tool_calls_used: int,
    ) -> None:
        rendered = json.dumps(action, default=str)[:4000]
        self._write_rejected_action_trace(
            trace_path,
            action={"json_value": action},
            reason="model response JSON was not an object action",
            llm_steps=llm_steps,
            research_tool_calls_used=research_tool_calls_used,
            workspace_tool_calls_used=workspace_tool_calls_used,
        )
        messages.append({"role": "assistant", "content": rendered})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Rejected response without spending any tool budget: JSON was valid, "
                    "but the action loop requires exactly one JSON object, not a list or "
                    "scalar. Return exactly one corrected JSON object now with `action` "
                    "and `arguments` fields."
                ),
            }
        )

    def _handle_tool_execution_error(
        self,
        *,
        trace_path: Path,
        raw_trace_path: Path,
        messages: list[dict[str, str]],
        action: dict[str, Any],
        tool_name: str,
        arguments: dict[str, Any],
        exc: Exception,
        is_workspace_tool: bool,
        llm_steps: int,
        research_tool_calls_used: int,
        workspace_tool_calls_used: int,
    ) -> None:
        error_result = {
            "error": True,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "tool_name": tool_name,
            "arguments": arguments,
        }
        self._write_trace(
            trace_path,
            {
                "type": "tool_error",
                "step": llm_steps,
                "tool_name": tool_name,
                "arguments": arguments,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "research_tool_calls_used": research_tool_calls_used,
                "workspace_tool_calls_used": workspace_tool_calls_used,
            },
        )
        if not is_workspace_tool:
            self._write_raw_tool_result(
                raw_trace_path,
                tool_name=tool_name,
                arguments=arguments,
                result=error_result,
                research_tool_calls_used=research_tool_calls_used,
                workspace_tool_calls_used=workspace_tool_calls_used,
            )
            self._append_auto_query_entry(
                trace_path.parent,
                tool_name=tool_name,
                arguments=arguments,
                result=error_result,
                query_index=llm_steps,
            )

        messages.append({"role": "assistant", "content": json.dumps(action)})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Tool execution failed, but the run is continuing and no tool budget "
                    "was spent by this failed action.\n\n"
                    f"- Tool: `{tool_name}`\n"
                    f"- Error type: `{type(exc).__name__}`\n"
                    f"- Error: {str(exc)[:2000]}\n\n"
                    "Return exactly one JSON object that recovers: use a fallback tool, "
                    "retry with corrected arguments, search by title/query instead of a "
                    "bad paper id, or update workspace notes with the failure before "
                    "continuing. Do not repeat the exact same failing call unless you "
                    "changed the arguments."
                ),
            }
        )

    def _write_raw_tool_result(
        self,
        path: Path,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        research_tool_calls_used: int,
        workspace_tool_calls_used: int,
    ) -> None:
        self._write_trace(
            path,
            {
                "type": "raw_research_tool_result",
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
                "paper_ids": _extract_paper_ids(result),
                "research_tool_calls_used": research_tool_calls_used,
                "workspace_tool_calls_used": workspace_tool_calls_used,
            },
        )

    def _append_auto_query_entry(
        self,
        workspace_path: Path,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        query_index: int,
    ) -> None:
        paper_ids = _extract_paper_ids(result)[:12]
        if isinstance(result, dict) and result.get("error"):
            result_count = f"failed ({result.get('error_type', 'tool error')})"
        else:
            result_count = str(_result_count(result))
        query_text = arguments.get("query") or arguments.get("paper_id") or arguments.get("arxiv_url") or tool_name
        content = (
            f"- Tool: `{tool_name}`\n"
            f"- Arguments: `{json.dumps(arguments, default=str, sort_keys=True)}`\n"
            f"- Result count: `{result_count}`\n"
            f"- Top result IDs: {', '.join(paper_ids) if paper_ids else '(none extracted)'}\n"
            f"- Why this query was run: selected by the agent as research step {query_index} "
            "for its assigned taste and open questions.\n"
            "- Follow-up: promote relevant papers into `papers.md`, distill evidence into "
            "`findings.md`, and update `memory.md` with state, open questions, or contradictions.\n"
        )
        self.workspace.append_owned_markdown(
            workspace_path,
            "queries.md",
            content,
            heading=f"Query: {tool_name} {query_index} - {str(query_text)[:80]}",
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
            if action_type == "patch_workspace_file":
                for key in ("start_line", "end_line", "replacement"):
                    if key not in arguments:
                        return f"`patch_workspace_file` requires `arguments.{key}`"
        return ""

    def _artifact_status(self, workspace_path: Path) -> str:
        rows = []
        state = self._evidence_state(workspace_path)
        for relative_path in self._tracked_artifacts(workspace_path):
            path = workspace_path / relative_path
            if not path.exists():
                rows.append(f"- `{relative_path}`: missing")
                continue
            text = path.read_text(encoding="utf-8")
            meaningful = _meaningful_markdown_chars(text)
            if not _artifact_due(
                relative_path,
                state,
                novelty_mode=self._is_novelty_workspace(workspace_path),
                before_final=False,
            ):
                status = "not due until supporting evidence exists"
            else:
                issue = _artifact_quality_issue(text, relative_path, state)
                status = "ready" if not issue else f"needs repair: {issue}"
            rows.append(f"- `{relative_path}`: {status}; {meaningful} meaningful chars")
        return "\n".join(rows)

    def _documentation_repair_directive(self, workspace_path: Path, *, before_final: bool = False) -> str:
        target = self._documentation_repair_target(workspace_path, before_final=before_final)
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
            self._evidence_state(workspace_path),
            before_final=before_final,
        )
        boundary = "before final handoff" if before_final else "before more broad searching"
        final_sentence = (
            "Do not return final until this file has the required kind of content."
            if before_final
            else "Do not run another search until this file has the required kind of content."
        )
        return (
            f"Documentation repair needed {boundary}: "
            f"`{target}` is not satisfying its artifact contract: {issue}. "
            "The next action must append a detailed, evidence-bearing chunk to "
            f"that file using `append_workspace_markdown`. {final_sentence}"
        )

    def _artifact_contract_message(self) -> str:
        return (
            "Artifact contract: when you have evidence to record, keep all "
            "required markdown files current. `queries.md` needs query/tool, "
            "parameters, result count/failure state, and rationale/follow-up. "
            "`papers.md` needs paper ID/source, title/year/metadata, and "
            "relevance. `findings.md` needs finding/gap/risk/proposal, evidence, "
            "and uncertainty/next check. In novelty mode, `proposal_seeds.md` "
            "needs concrete idea seeds with evidence trigger, mechanism, collision "
            "risk, validation, falsification, confidence, and next search. "
            "`memory.md` needs durable running state, search thread, and open "
            "question/contradiction/handoff prep."
        )

    def _documentation_repair_target(self, workspace_path: Path, *, before_final: bool = False) -> str:
        state = self._evidence_state(workspace_path)
        novelty_mode = self._is_novelty_workspace(workspace_path)
        candidates: list[str] = []
        if before_final:
            candidates = ["queries.md", "papers.md", "findings.md", "memory.md"]
            if novelty_mode:
                candidates.insert(3, "proposal_seeds.md")
        else:
            if state.has_any_search:
                candidates.append("queries.md")
            if state.has_paper_results:
                candidates.append("papers.md")
            if state.has_candidate_papers and state.has_multiple_sources:
                candidates.append("findings.md")
            if novelty_mode and state.finding_sections > 0:
                candidates.append("proposal_seeds.md")
            if state.has_any_search:
                candidates.append("memory.md")
        for relative_path in candidates:
            if not _artifact_due(
                relative_path,
                state,
                novelty_mode=novelty_mode,
                before_final=before_final,
            ):
                continue
            path = workspace_path / relative_path
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if _artifact_quality_issue(text, relative_path, state, before_final=before_final):
                return relative_path
        return ""

    def _missing_final_artifacts(self, workspace_path: Path) -> list[str]:
        state = self._evidence_state(workspace_path)
        novelty_mode = self._is_novelty_workspace(workspace_path)
        missing = []
        for relative_path in self._tracked_artifacts(workspace_path, include_handoff=False):
            if not _artifact_due(
                relative_path,
                state,
                novelty_mode=novelty_mode,
                before_final=True,
            ):
                continue
            path = workspace_path / relative_path
            issue = _artifact_quality_issue(
                path.read_text(encoding="utf-8") if path.exists() else "",
                relative_path,
                state,
                before_final=True,
            )
            if issue:
                missing.append(f"`{relative_path}`: {issue}")
        return missing

    def _tracked_artifacts(self, workspace_path: Path, *, include_handoff: bool = True) -> tuple[str, ...]:
        artifacts = ["memory.md", "queries.md", "papers.md", "findings.md"]
        if self._is_novelty_workspace(workspace_path):
            artifacts.append("proposal_seeds.md")
        if include_handoff:
            artifacts.append("handoff.md")
        return tuple(artifacts)

    def _is_novelty_workspace(self, workspace_path: Path) -> bool:
        prompt = workspace_path / "system_prompt.md"
        return prompt.exists() and "novelty_ideation" in prompt.read_text(encoding="utf-8")

    def _evidence_state(self, workspace_path: Path) -> WorkspaceEvidenceState:
        trace_path = workspace_path / "tool_calls.jsonl"
        research_tool_results = 0
        paper_ids: set[str] = set()
        if trace_path.exists():
            for line in trace_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "tool_result":
                    continue
                tool_name = str(entry.get("tool_name") or "")
                if tool_name not in WORKSPACE_TOOLS:
                    research_tool_results += 1
                    if tool_name in PAPER_RESULT_TOOLS:
                        paper_ids.update(_extract_paper_ids(entry.get("result")))
        paper_id_count = len(paper_ids)
        paper_sections = _count_sections(_read_text(workspace_path / "papers.md"), "Paper")
        return WorkspaceEvidenceState(
            research_tool_results=research_tool_results,
            paper_ids_seen=paper_id_count,
            query_sections=_count_sections(_read_text(workspace_path / "queries.md"), "Query"),
            paper_sections=paper_sections,
            finding_sections=_count_sections(_read_text(workspace_path / "findings.md"), "Finding"),
            proposal_seed_sections=_count_sections(
                _read_text(workspace_path / "proposal_seeds.md"),
                "Proposal Seed",
            ),
            has_any_search=research_tool_results > 0,
            has_paper_results=bool(paper_ids),
            has_multiple_sources=research_tool_results >= 2 or paper_id_count >= 3,
            has_candidate_papers=paper_sections >= 2 or paper_id_count >= 3,
        )

    def _research_budget_exhausted_message(self, workspace_path: Path) -> str:
        return (
            "Research/API tool budget is exhausted. Search/API tools are now forbidden. "
            "You still have a separate large workspace-tool budget. Use only workspace "
            "tools to make the markdown artifacts detailed: update `queries.md`, "
            "`papers.md`, `findings.md`, `proposal_seeds.md` when due, and `memory.md`, then return `final` with "
            "a handoff. Current artifact status:\n"
            + self._artifact_status(workspace_path)
            + "\n\n"
            + self._documentation_repair_directive(workspace_path, before_final=True)
        )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _meaningful_markdown_chars(text: str) -> int:
    meaningful_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        meaningful_lines.append(stripped)
    return len("\n".join(meaningful_lines))


def _artifact_due(
    relative_path: str,
    state: WorkspaceEvidenceState,
    *,
    novelty_mode: bool,
    before_final: bool,
) -> bool:
    if relative_path == "queries.md":
        return state.has_any_search
    if relative_path == "papers.md":
        return state.has_paper_results
    if relative_path == "findings.md":
        return state.has_candidate_papers and state.has_multiple_sources
    if relative_path == "proposal_seeds.md":
        return novelty_mode and (state.finding_sections > 0 or (before_final and state.has_candidate_papers))
    if relative_path == "memory.md":
        return state.has_any_search
    if relative_path == "handoff.md":
        return before_final
    return before_final


def _artifact_quality_issue(
    text: str,
    relative_path: str,
    state: WorkspaceEvidenceState | None = None,
    *,
    before_final: bool = False,
) -> str:
    if _meaningful_markdown_chars(text) == 0:
        return "empty beyond headings"
    lowered = text.lower()
    placeholders = [marker for marker in PLACEHOLDER_MARKERS if marker in lowered]
    if placeholders:
        return f"placeholder text still present: {placeholders[0]}"
    if relative_path == "queries.md" and (before_final or (state and state.has_any_search)):
        required = min(2, max(1, state.research_tool_results if state else 1)) if before_final else 1
        issue = _structured_section_issue(text, relative_path, required)
        if issue:
            return issue
    if relative_path == "papers.md" and (before_final or (state and state.has_paper_results)):
        required = 3 if before_final else 1
        issue = _structured_section_issue(text, relative_path, required)
        if issue:
            return issue
    if relative_path == "findings.md" and (
        before_final or (state and state.has_candidate_papers and state.has_multiple_sources)
    ):
        required = 2 if before_final else 1
        issue = _structured_section_issue(text, relative_path, required)
        if issue:
            return issue
    if relative_path == "proposal_seeds.md" and (
        before_final or (state and (state.finding_sections > 0 or state.has_candidate_papers))
    ):
        issue = _structured_section_issue(text, relative_path, 1)
        if issue:
            return issue
    missing = [
        label
        for label, terms in ARTIFACT_QUALITY_CONTRACTS.get(relative_path, [])
        if not any(term in lowered for term in terms)
    ]
    if missing:
        return "missing " + "; missing ".join(missing)
    return ""


def _count_sections(text: str, prefix: str) -> int:
    return len(re.findall(rf"^##\s+{re.escape(prefix)}:", text, flags=re.MULTILINE | re.IGNORECASE))


def _structured_section_issue(text: str, relative_path: str, required: int) -> str:
    section = STRUCTURED_SECTION_FIELDS.get(relative_path)
    if not section:
        return ""
    prefix, required_fields = section
    sections = _extract_sections(text, prefix)
    if len(sections) < required:
        return f"missing at least {required} structured `## {prefix}:` sections"
    complete_sections = [
        body
        for body in sections
        if all(re.search(rf"^\s*-\s*{re.escape(field)}\s*:", body, flags=re.MULTILINE | re.IGNORECASE) for field in required_fields)
    ]
    if len(complete_sections) < required:
        return (
            f"needs at least {required} complete `## {prefix}:` sections with fields: "
            + ", ".join(required_fields)
        )
    return ""


def _extract_sections(text: str, prefix: str) -> list[str]:
    pattern = re.compile(
        rf"^##\s+{re.escape(prefix)}:.*?(?=^##\s+|\Z)",
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    return [match.group(0) for match in pattern.finditer(text)]


def _extract_paper_ids(value: Any, limit: int = 200) -> list[str]:
    found: list[str] = []

    def visit(item: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(item, dict):
            paper_id = item.get("paperId") or item.get("paper_id") or item.get("canonical_paper_id")
            if isinstance(paper_id, str) and paper_id:
                found.append(paper_id)
            external_ids = item.get("externalIds")
            if isinstance(external_ids, dict):
                arxiv = external_ids.get("ArXiv") or external_ids.get("arXiv")
                doi = external_ids.get("DOI")
                if isinstance(arxiv, str) and arxiv:
                    found.append(f"ARXIV:{arxiv}")
                if isinstance(doi, str) and doi:
                    found.append(f"DOI:{doi}")
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return _dedupe_keep_order(found)[:limit]


def _result_count(result: Any) -> int:
    if isinstance(result, dict):
        total = result.get("total")
        if isinstance(total, int):
            return total
        for key in ("papers", "references", "citations", "ranked_candidates", "organic_results"):
            value = result.get(key)
            if isinstance(value, list):
                return len(value)
        if "paper" in result or "canonical_paper_id" in result or "paper_id" in result:
            return 1
    if isinstance(result, list):
        return len(result)
    return 0


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


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
