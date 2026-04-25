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


ACTION_INSTRUCTIONS = """Return exactly one JSON object.

Allowed forms:

{"action":"tool","tool_name":"<allowed tool>","arguments":{...},"memory_update":"short markdown note"}
{"action":"final","summary":"short summary","handoff_markdown":"# Hand-Off\\n..."}

Rules:
- Use only allowed tools.
- Prefer workspace append/write tools after research tools so durable memory stays current.
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
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.workspace = workspace
        self.max_steps = max_steps

    async def run_subagent(self, plan: SubagentPlan, stage: ResearchStage) -> AgentRunResult:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": plan.system_prompt},
            {
                "role": "user",
                "content": (
                    ACTION_INSTRUCTIONS
                    + "\nAllowed executable tools:\n"
                    + "\n".join(f"- {name}" for name in sorted(plan.allowed_tools))
                    + "\n\nStart by reading memory.md, then execute the strongest research loop for your taste."
                ),
            },
        ]
        trace_path = plan.workspace_path / "tool_calls.jsonl"
        tool_calls_used = 0
        llm_steps = 0
        exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
        summary = ""

        for _ in range(self.max_steps):
            llm_steps += 1
            action = await self.llm.chat_json(role=plan.model_role, messages=messages)
            self._write_trace(trace_path, {"type": "llm_action", "step": llm_steps, "action": action})

            action_type = action.get("action")
            if action_type == "final":
                handoff = action.get("handoff_markdown", "")
                if not handoff:
                    raise RuntimeError(f"{plan.subagent_id} final action omitted handoff_markdown")
                self.workspace.write_owned_markdown(plan.workspace_path, "handoff.md", handoff)
                summary = action.get("summary") or "Live subagent completed."
                exit_reason = AgentExitReason.COMPLETED
                break

            if action_type != "tool":
                raise RuntimeError(f"{plan.subagent_id} returned invalid action: {action}")

            tool_name = action.get("tool_name")
            if tool_name not in plan.allowed_tools:
                raise RuntimeError(f"{plan.subagent_id} requested disallowed tool: {tool_name}")
            if tool_calls_used >= plan.max_tool_calls:
                exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
                break

            arguments = action.get("arguments")
            if not isinstance(arguments, dict):
                raise RuntimeError(f"{plan.subagent_id} provided invalid arguments for {tool_name}: {arguments}")

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
                        "tool_calls_used": tool_calls_used,
                    },
                )
                raise
            tool_calls_used += 1
            trace_entry = {
                "type": "tool_result",
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
                "tool_calls_used": tool_calls_used,
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
            messages.append({"role": "user", "content": "Tool result:\n" + json.dumps(result, default=str)})

            if tool_calls_used >= plan.max_tool_calls:
                exit_reason = AgentExitReason.MAX_TOOL_CALLS_REACHED
                break

        if not (plan.workspace_path / "handoff.md").exists():
            handoff = await self._force_handoff(plan, messages, exit_reason)
            self.workspace.write_owned_markdown(plan.workspace_path, "handoff.md", handoff)
            summary = f"{plan.subagent_id} stopped at {exit_reason.value}; forced handoff written."

        profile = self.llm.profile_for(plan.model_role)
        return AgentRunResult(
            agent_id=plan.subagent_id,
            stage=stage,
            exit_reason=exit_reason,
            tool_calls_used=tool_calls_used,
            workspace_path=plan.workspace_path,
            artifacts=[plan.workspace_path / "handoff.md", trace_path],
            summary=summary or f"{plan.subagent_id} completed live research loop.",
            model_provider=profile.provider,
            model_name=profile.model,
            llm_steps_used=llm_steps,
            tool_trace_path=trace_path,
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
