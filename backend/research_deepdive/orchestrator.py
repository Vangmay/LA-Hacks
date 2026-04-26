"""Config-driven orchestration for deep literature research runs."""
from __future__ import annotations

import asyncio
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .agent_runner import LiveAgentRunner
from .config import DeepDiveConfig
from .event_bus import DeepDiveEventBus
from .events import DeepDiveEvent, DeepDiveEventType
from .llm import DeepDiveLLMProvider
from .models import (
    AgentExitReason,
    AgentModelRole,
    AgentRunResult,
    CritiqueResult,
    DeepDiveRunRequest,
    DeepDiveRunResult,
    InvestigatorPlan,
    ResearchTaste,
    ResearchStage,
    SubagentPlan,
)
from .personas import (
    generate_research_tastes,
    persona_library_summary,
    validate_research_taste_roster,
)
from .prompts import PromptBook
from .tool_runtime import ToolRuntime
from .tools import build_default_tool_registry
from .workspace import WorkspaceManager, slugify


class DeepDiveOrchestrator:
    """Owns stage transitions for the research deep-dive pipeline.

    Live LLM/tool execution will plug into the same plan objects. The current
    dry-run path deliberately exercises prompt composition, workspace ownership,
    budget propagation, async subagent completion, critique, and finalization
    without external calls.
    """

    def __init__(
        self,
        config: DeepDiveConfig | None = None,
        prompt_book: PromptBook | None = None,
        llm_provider: DeepDiveLLMProvider | None = None,
        tool_runtime: ToolRuntime | None = None,
        event_bus: DeepDiveEventBus | None = None,
    ) -> None:
        self.config = (config or DeepDiveConfig()).normalized()
        self.prompt_book = prompt_book or PromptBook()
        self.tools = build_default_tool_registry()
        self.workspace = WorkspaceManager(self.config.workspace_root)
        self.llm = llm_provider or DeepDiveLLMProvider(self.config)
        self.event_bus = event_bus
        self.tool_runtime = tool_runtime or ToolRuntime(
            workspace=self.workspace,
            http_timeout_seconds=self.config.http_timeout_seconds,
            result_char_limit=self.config.tool_result_char_limit,
            semantic_scholar_min_interval_seconds=self.config.semantic_scholar_min_interval_seconds,
            semantic_scholar_max_retries=self.config.semantic_scholar_max_retries,
            serpapi_max_requests=self.config.serpapi_max_requests,
        )
        self.live_runner = LiveAgentRunner(
            llm=self.llm,
            tools=self.tool_runtime,
            workspace=self.workspace,
            max_steps=self.config.subagent_max_steps,
            workspace_write_char_budget=self.config.workspace_write_char_budget,
            max_workspace_tool_calls=self.config.subagent_max_workspace_tool_calls,
            event_bus=event_bus,
        )

    async def _emit(
        self,
        run_id: str,
        event_type: DeepDiveEventType,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if not self.event_bus:
            return
        await self.event_bus.publish(
            DeepDiveEvent(
                type=event_type,
                run_id=run_id,
                payload=payload or {},
            )
        )

    async def _emit_plans(self, run_id: str, investigators: list[InvestigatorPlan]) -> None:
        for investigator in investigators:
            await self._emit(
                run_id,
                DeepDiveEventType.INVESTIGATOR_PLANNED,
                {
                    "investigator_id": investigator.investigator_id,
                    "section_id": investigator.section_id,
                    "section_title": investigator.section_title,
                    "workspace_path": str(investigator.workspace_path),
                    "system_prompt_preview": investigator.system_prompt[:4000],
                    "subagent_ids": [sub.subagent_id for sub in investigator.subagents],
                },
            )
            for subagent in investigator.subagents:
                await self._emit(
                    run_id,
                    DeepDiveEventType.SUBAGENT_PLANNED,
                    {
                        "subagent_id": subagent.subagent_id,
                        "investigator_id": subagent.investigator_id,
                        "section_id": subagent.section_id,
                        "section_title": subagent.section_title,
                        "workspace_path": str(subagent.workspace_path),
                        "taste": subagent.taste.model_dump(),
                        "allowed_tools": subagent.allowed_tools,
                        "max_tool_calls": subagent.max_tool_calls,
                        "model_role": subagent.model_role.value,
                    },
                )

    async def _emit_subagent_completed(self, run_id: str, result: AgentRunResult) -> None:
        await self._emit(
            run_id,
            DeepDiveEventType.SUBAGENT_COMPLETED,
            {
                "subagent_id": result.agent_id,
                "exit_reason": result.exit_reason.value,
                "summary": result.summary,
                "error": result.error,
                "workspace_path": str(result.workspace_path),
                "model_provider": result.model_provider,
                "model_name": result.model_name,
                "budget": {
                    "research_used": result.research_tool_calls_used or result.tool_calls_used,
                    "workspace_used": result.workspace_tool_calls_used,
                    "llm_steps": result.llm_steps_used,
                },
                "artifacts": [str(path) for path in result.artifacts],
            },
        )

    async def _emit_investigator_synthesis(self, run_id: str, result: AgentRunResult) -> None:
        artifact = result.artifacts[0] if result.artifacts else None
        await self._emit(
            run_id,
            DeepDiveEventType.INVESTIGATOR_SYNTHESIZED,
            {
                "investigator_id": result.agent_id,
                "summary": result.summary,
                "exit_reason": result.exit_reason.value,
                "synthesis_path": str(artifact) if artifact else "",
                "synthesis_md": artifact.read_text(encoding="utf-8") if artifact and artifact.exists() else "",
            },
        )

    async def _emit_cross_completed(self, run_id: str, run_root: Path, paths: list[Path]) -> None:
        artifacts: dict[str, str] = {}
        for path in paths:
            if path.exists():
                artifacts[path.name.replace(".md", "")] = path.read_text(encoding="utf-8")
        for name in ("proposal_families.md", "global_evidence_map.md", "unresolved_conflicts.md"):
            path = run_root / "shared" / name
            if path.exists():
                artifacts[path.name.replace(".md", "")] = path.read_text(encoding="utf-8")
        await self._emit(
            run_id,
            DeepDiveEventType.CROSS_INVESTIGATOR_COMPLETED,
            {"artifacts": artifacts},
        )

    async def _emit_critique_completed(self, run_id: str, critique: CritiqueResult) -> None:
        await self._emit(
            run_id,
            DeepDiveEventType.CRITIQUE_COMPLETED,
            {
                "critic_id": critique.critic_id,
                "lens": critique.lens,
                "summary": critique.summary,
                "workspace_path": str(critique.workspace_path),
                "artifact_path": str(critique.artifact_path),
                "critique_md": (
                    critique.artifact_path.read_text(encoding="utf-8")
                    if critique.artifact_path.exists()
                    else ""
                ),
            },
        )

    async def run(self, request: DeepDiveRunRequest) -> DeepDiveRunResult:
        stages: list[ResearchStage] = []
        warnings: list[str] = []
        run_root = self.workspace.prepare_run(request.run_id)
        current_stage = ResearchStage.BOOTSTRAP

        try:
            await self._emit(
                request.run_id,
                DeepDiveEventType.RUN_STARTED,
                {
                    "run_id": request.run_id,
                    "arxiv_url": request.arxiv_url,
                    "paper_id": request.paper_id,
                    "objective": request.research_objective,
                    "mode": request.mode,
                    "workspace_path": str(run_root),
                    "config": {
                        "max_investigators": self.config.max_investigators,
                        "subagents_per_investigator": self.config.subagents_per_investigator,
                        "subagent_max_tool_calls": self.config.subagent_max_tool_calls,
                        "max_parallel_subagents": self.config.max_parallel_subagents,
                        "dynamic_roster_enabled": self.config.dynamic_roster_enabled,
                    },
                },
            )
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            stages.append(ResearchStage.BOOTSTRAP)
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            current_stage = ResearchStage.INVESTIGATOR_PLANNING
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            if request.mode == "live" and (
                self.config.dynamic_roster_enabled or not _clean_titles(request.section_titles)
            ):
                investigators = await self._plan_investigators_live(request, run_root, warnings)
            else:
                investigators = self._plan_investigators(request, run_root)
            stages.append(ResearchStage.INVESTIGATOR_PLANNING)
            await self._emit_plans(request.run_id, investigators)
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            current_stage = ResearchStage.SUBAGENT_RESEARCH
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            subagent_results = await self._run_all_subagents(investigators, request)
            stages.append(ResearchStage.SUBAGENT_RESEARCH)
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            current_stage = ResearchStage.INVESTIGATOR_SYNTHESIS
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            syntheses: list[AgentRunResult] = []
            if request.mode == "live":
                for plan in investigators:
                    result = await self._synthesize_investigator_live(plan, subagent_results, request)
                    syntheses.append(result)
                    await self._emit_investigator_synthesis(request.run_id, result)
            else:
                for plan in investigators:
                    result = self._synthesize_investigator(plan, subagent_results)
                    syntheses.append(result)
                    await self._emit_investigator_synthesis(request.run_id, result)
            stages.append(ResearchStage.INVESTIGATOR_SYNTHESIS)
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            current_stage = ResearchStage.CROSS_INVESTIGATOR_DEEP_DIVE
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            if request.mode == "live":
                cross_paths = await self._run_cross_investigator_deep_dive_live(
                    run_root,
                    investigators,
                    syntheses,
                    request,
                )
            else:
                cross_paths = [self._write_cross_investigator_deep_dive(run_root, syntheses, request)]
            stages.append(ResearchStage.CROSS_INVESTIGATOR_DEEP_DIVE)
            await self._emit_cross_completed(request.run_id, run_root, cross_paths)
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            current_stage = ResearchStage.CRITIQUE
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            if request.mode == "live":
                critiques = await self._run_critiques_live(run_root, syntheses, request)
            else:
                critiques = self._run_critiques(run_root, syntheses, request)
            stages.append(ResearchStage.CRITIQUE)
            for critique in critiques:
                await self._emit_critique_completed(request.run_id, critique)
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            current_stage = ResearchStage.FINALIZATION
            await self._emit(request.run_id, DeepDiveEventType.STAGE_ENTERED, {"stage": current_stage.value})
            if request.mode == "live":
                final_report = await self._finalize_live(run_root, request, investigators, syntheses, critiques)
            else:
                final_report = self._finalize(run_root, request, investigators, syntheses, critiques)
            stages.append(ResearchStage.FINALIZATION)
            await self._emit(
                request.run_id,
                DeepDiveEventType.RUN_FINALIZED,
                {
                    "run_id": request.run_id,
                    "final_report_path": str(final_report),
                    "final_report_md": final_report.read_text(encoding="utf-8") if final_report.exists() else "",
                },
            )
            await self._emit(request.run_id, DeepDiveEventType.STAGE_COMPLETED, {"stage": current_stage.value})

            return DeepDiveRunResult(
                run_id=request.run_id,
                status="success",
                workspace_path=run_root,
                stages_completed=stages,
                investigators=investigators,
                subagent_results=subagent_results,
                investigator_syntheses=syntheses,
                critiques=critiques,
                final_report_path=final_report,
                warnings=warnings,
            )
        except Exception as exc:
            await self._emit(
                request.run_id,
                DeepDiveEventType.RUN_ERROR,
                {
                    "run_id": request.run_id,
                    "stage": current_stage.value,
                    "error": str(exc),
                },
            )
            return DeepDiveRunResult(
                run_id=request.run_id,
                status="error",
                workspace_path=run_root,
                stages_completed=stages,
                investigators=[],
                subagent_results=[],
                investigator_syntheses=[],
                critiques=[],
                warnings=warnings,
                error=str(exc),
            )

    def _plan_investigators(
        self,
        request: DeepDiveRunRequest,
        run_root: Path,
        taste_rosters: dict[str, list[ResearchTaste]] | None = None,
        planner_notes: dict[str, dict[str, Any]] | None = None,
    ) -> list[InvestigatorPlan]:
        section_titles = _clean_titles(request.section_titles) or ["whole paper"]
        selected = section_titles[: self.config.max_investigators]
        tool_names = sorted(
            self.tool_runtime.executable_tool_names()
            if request.mode == "live"
            else self.tools.keys()
        )
        shared_tools = self._shared_tool_prompt(tool_names if request.mode == "live" else None)
        objective_directive = _objective_directive(request.research_objective)
        novelty_contract = _novelty_contract(self.prompt_book, request.research_objective)

        investigators: list[InvestigatorPlan] = []
        for idx, title in enumerate(selected, start=1):
            section_id = f"section_{idx:02d}_{slugify(title)}"
            investigator_id = f"investigator_{idx:02d}_{slugify(title)}"
            investigator_path = self.workspace.investigator_path(request.run_id, investigator_id)
            tastes = (
                taste_rosters.get(investigator_id)
                if taste_rosters and investigator_id in taste_rosters
                else generate_research_tastes(
                    title,
                    self.config.subagents_per_investigator,
                    min_count=self.config.min_personas_per_investigator,
                    max_count=self.config.max_personas_per_investigator,
                    require_diversity=self.config.require_persona_diversity,
                )
            )
            note = (planner_notes or {}).get(investigator_id)
            if note:
                self.workspace.write_json(investigator_path / "planner_roster.json", note)
                self.workspace.write_markdown(
                    investigator_path / "planner_rationale.md",
                    str(note.get("rationale") or note.get("status") or "Planner roster recorded."),
                )

            subagents: list[SubagentPlan] = []
            for sub_idx, taste in enumerate(tastes, start=1):
                subagent_id = f"{investigator_id}_subagent_{sub_idx:02d}"
                subagent_path = self.workspace.subagent_path(investigator_path, subagent_id)
                subagent_prompt = self.prompt_book.subagent_prompt(
                    arxiv_url=request.arxiv_url,
                    paper_id=request.paper_id or "unknown",
                    research_brief=request.research_brief or "(no extra brief)",
                    research_objective=request.research_objective,
                    objective_directive=objective_directive,
                    novelty_contract=novelty_contract,
                    investigator_id=investigator_id,
                    subagent_id=subagent_id,
                    section_title=title,
                    taste=taste.model_dump_json(indent=2),
                    shared_tool_spec=shared_tools,
                    memory_spec=self.prompt_book.memory_spec,
                    max_tool_calls=self.config.subagent_max_tool_calls,
                    workspace_path=subagent_path,
                )
                plan = SubagentPlan(
                    subagent_id=subagent_id,
                    investigator_id=investigator_id,
                    section_id=section_id,
                    section_title=title,
                    taste=taste,
                    workspace_path=subagent_path,
                    system_prompt=subagent_prompt,
                    allowed_tools=tool_names,
                    max_tool_calls=self.config.subagent_max_tool_calls,
                    model_role=AgentModelRole.SEARCH_SUBAGENT,
                )
                self.workspace.initialize_subagent(plan)
                subagents.append(plan)

            investigator_prompt = self.prompt_book.investigator_prompt(
                arxiv_url=request.arxiv_url,
                paper_id=request.paper_id or "unknown",
                research_brief=request.research_brief or "(no extra brief)",
                research_objective=request.research_objective,
                objective_directive=objective_directive,
                novelty_contract=novelty_contract,
                investigator_id=investigator_id,
                section_title=title,
                subagent_count=len(subagents),
                persona_min=self.config.min_personas_per_investigator,
                persona_max=self.config.max_personas_per_investigator,
                require_persona_diversity=self.config.require_persona_diversity,
                shared_tool_spec=shared_tools,
                memory_spec=self.prompt_book.memory_spec,
                workspace_path=investigator_path,
                subagent_tastes="\n\n".join(
                    f"## {plan.subagent_id}\n```json\n{plan.taste.model_dump_json(indent=2)}\n```"
                    for plan in subagents
                ),
            )
            investigator = InvestigatorPlan(
                investigator_id=investigator_id,
                section_id=section_id,
                section_title=title,
                workspace_path=investigator_path,
                system_prompt=investigator_prompt,
                subagents=subagents,
            )
            self.workspace.initialize_investigator(investigator)
            self.workspace.write_json(
                run_root / "shared" / f"{investigator_id}_plan.json",
                investigator.model_dump(),
            )
            investigators.append(investigator)

        return investigators

    async def _plan_investigators_live(
        self,
        request: DeepDiveRunRequest,
        run_root: Path,
        warnings: list[str],
    ) -> list[InvestigatorPlan]:
        section_titles, direction_note = await self._select_investigation_titles(request, run_root, warnings)
        selected = section_titles[: self.config.max_investigators]
        director_lines = [
            "# Director Plan",
            "",
            f"- Research objective: `{request.research_objective}`",
            f"- Direction source: `{direction_note.get('source', 'unknown')}`",
            f"- Dynamic roster enabled: `{self.config.dynamic_roster_enabled}`",
            f"- Requested investigators: `{len(selected)}`",
            f"- Subagents per investigator: `{self.config.subagents_per_investigator}`",
            "",
            "## Rationale",
            "",
            str(direction_note.get("rationale") or "No rationale recorded."),
            "",
            "## Investigation Directions",
            "",
        ]
        zones = []
        for idx, title in enumerate(selected, start=1):
            section_id = f"section_{idx:02d}_{slugify(title)}"
            investigator_id = f"investigator_{idx:02d}_{slugify(title)}"
            zones.append(
                {
                    "investigator_id": investigator_id,
                    "section_id": section_id,
                    "section_title": title,
                    "requested_subagents": self.config.subagents_per_investigator,
                }
            )
            director_lines.append(f"- `{investigator_id}`: {title}")
        self.workspace.write_markdown(run_root / "shared" / "director_plan.md", "\n".join(director_lines) + "\n")
        self.workspace.write_json(
            run_root / "shared" / "investigation_zones.json",
            {
                "source": direction_note.get("source", "unknown"),
                "rationale": direction_note.get("rationale", ""),
                "zones": zones,
                "raw_planner_output": direction_note.get("raw_planner_output"),
            },
        )

        rosters: dict[str, list[ResearchTaste]] = {}
        notes: dict[str, dict[str, Any]] = {}
        trace_lines = ["# Planning Trace", ""]
        for zone in zones:
            title = str(zone["section_title"])
            investigator_id = str(zone["investigator_id"])
            if self.config.dynamic_roster_enabled:
                roster, note = await self._plan_dynamic_roster_for_investigator(
                    request=request,
                    investigator_id=investigator_id,
                    section_title=title,
                )
                rosters[investigator_id] = roster
                notes[investigator_id] = note
            else:
                note = {
                    "status": "skipped",
                    "source": "deterministic",
                    "rationale": "Dynamic roster planning is disabled; deterministic tastes will be generated for this director-selected direction.",
                    "validation_errors": [],
                }
                notes[investigator_id] = note
            trace_lines.extend(
                [
                    f"## {investigator_id}",
                    "",
                    f"- Status: `{note.get('status', 'unknown')}`",
                    f"- Roster source: `{note.get('source', 'unknown')}`",
                    f"- Validation errors: {note.get('validation_errors', [])}",
                    "",
                ]
            )
            if note.get("fallback_reason"):
                warnings.append(f"{investigator_id}: {note['fallback_reason']}")
                trace_lines.append(f"- Fallback reason: {note['fallback_reason']}")
                trace_lines.append("")
        self.workspace.write_markdown(run_root / "shared" / "planning_trace.md", "\n".join(trace_lines))
        planned_request = request.model_copy(update={"section_titles": selected})
        return self._plan_investigators(
            planned_request,
            run_root,
            taste_rosters=rosters if rosters else None,
            planner_notes=notes,
        )

    async def _select_investigation_titles(
        self,
        request: DeepDiveRunRequest,
        run_root: Path,
        warnings: list[str],
    ) -> tuple[list[str], dict[str, Any]]:
        explicit_titles = _clean_titles(request.section_titles)
        if explicit_titles:
            return explicit_titles, {
                "status": "accepted",
                "source": "request",
                "rationale": "Caller supplied explicit investigation directions.",
            }

        metadata = await self._resolve_seed_metadata_for_director(request, run_root, warnings)
        fallback_titles = ["whole paper"]
        prompt = self._investigation_direction_prompt(request, metadata)
        try:
            response = await self.llm.chat_json(
                role=AgentModelRole.DIRECTOR,
                messages=[
                    {"role": "system", "content": "You are the PaperCourt research director. Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            titles, raw_items, rationale = self._parse_investigation_direction_response(response)
            if not titles:
                raise ValueError("director returned no investigation directions")
            return titles[: self.config.max_investigators], {
                "status": "accepted",
                "source": "director",
                "rationale": rationale,
                "raw_planner_output": raw_items,
            }
        except Exception as exc:
            warning = f"director investigation planning failed; using whole-paper fallback: {exc}"
            warnings.append(warning)
            return fallback_titles, {
                "status": "fallback",
                "source": "fallback",
                "rationale": warning,
                "validation_errors": [str(exc)],
            }

    async def _resolve_seed_metadata_for_director(
        self,
        request: DeepDiveRunRequest,
        run_root: Path,
        warnings: list[str],
    ) -> dict[str, Any]:
        try:
            metadata = await self.tool_runtime.execute(
                "resolve_arxiv_paper",
                {"arxiv_url": request.arxiv_url},
                run_root / "shared",
            )
        except Exception as exc:
            warnings.append(f"director metadata lookup failed: {exc}")
            return {}
        self.workspace.write_json(run_root / "shared" / "director_seed_metadata.json", metadata)
        return metadata if isinstance(metadata, dict) else {"metadata": metadata}

    def _investigation_direction_prompt(
        self,
        request: DeepDiveRunRequest,
        seed_metadata: dict[str, Any],
    ) -> str:
        metadata_text = json.dumps(seed_metadata, indent=2, default=str)[:12000]
        return (
            "Choose investigator directions for a PaperCourt research deep dive. These are not fixed paper "
            "sections. They should be the most promising literature or novelty search directions for this "
            "specific seed paper and objective. Prefer directions that can each support a squad of subagents "
            "with distinct evidence tastes.\n\n"
            f"- arXiv URL: `{request.arxiv_url}`\n"
            f"- Paper ID: `{request.paper_id or 'unknown'}`\n"
            f"- Research objective: `{request.research_objective}`\n"
            f"- Research brief: {request.research_brief or '(none)'}\n"
            f"- Maximum investigators: `{self.config.max_investigators}`\n"
            f"- Subagents per investigator: `{self.config.subagents_per_investigator}`\n\n"
            "Seed metadata, when available:\n"
            "```json\n"
            f"{metadata_text or '{}'}\n"
            "```\n\n"
            "Return JSON with this shape:\n"
            "{\n"
            '  "rationale": "why these directions are the best use of the investigator budget",\n'
            '  "directions": [\n'
            "    {\n"
            '      "title": "short investigator direction, not a generic section label",\n'
            '      "why_promising": "why this direction deserves an investigator",\n'
            '      "seed_hooks": ["specific seed-paper hooks or metadata clues"],\n'
            '      "research_questions": ["question this investigator should answer"],\n'
            '      "priority": 1\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Avoid generic paper-section buckets unless the seed metadata makes that exact direction "
            "unusually promising. Use fewer than the maximum investigators if the evidence does not "
            "justify more."
        )

    def _parse_investigation_direction_response(
        self,
        response: dict[str, Any] | list[Any],
    ) -> tuple[list[str], list[Any], str]:
        rationale = ""
        if isinstance(response, dict):
            raw_items = (
                response.get("directions")
                or response.get("investigators")
                or response.get("zones")
                or response.get("section_titles")
                or []
            )
            rationale = str(response.get("rationale") or response.get("planner_rationale") or "")
        elif isinstance(response, list):
            raw_items = response
            rationale = "Director returned a top-level direction list."
        else:
            raise ValueError("director response must be a JSON object or array")
        if not isinstance(raw_items, list):
            raise ValueError("director response must contain a direction list")

        titles: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            title = ""
            if isinstance(item, str):
                title = item
            elif isinstance(item, dict):
                title = str(
                    item.get("title")
                    or item.get("direction")
                    or item.get("investigation_title")
                    or item.get("section_title")
                    or item.get("name")
                    or ""
                )
            cleaned = _clean_direction_title(title)
            key = cleaned.casefold()
            if cleaned and key not in seen:
                titles.append(cleaned)
                seen.add(key)
        return titles, raw_items, rationale

    async def _plan_dynamic_roster_for_investigator(
        self,
        *,
        request: DeepDiveRunRequest,
        investigator_id: str,
        section_title: str,
    ) -> tuple[list[ResearchTaste], dict[str, Any]]:
        fallback = generate_research_tastes(
            section_title,
            self.config.subagents_per_investigator,
            min_count=self.config.min_personas_per_investigator,
            max_count=self.config.max_personas_per_investigator,
            require_diversity=self.config.require_persona_diversity,
        )
        role = self._dynamic_roster_model_role()
        prompt = self._dynamic_roster_prompt(request, investigator_id, section_title)
        try:
            response = await self.llm.chat_json(
                role=role,
                messages=[
                    {"role": "system", "content": "You are an investigator roster planner. Return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            roster, rationale = self._parse_dynamic_roster_response(response, investigator_id, section_title)
            errors = self._validate_dynamic_roster(roster)
            if errors:
                repair_response = await self.llm.chat_json(
                    role=role,
                    messages=[
                        {"role": "system", "content": "Repair the roster JSON. Return strict JSON only."},
                        {
                            "role": "user",
                            "content": (
                                prompt
                                + "\n\nValidation errors from the previous roster:\n"
                                + "\n".join(f"- {error}" for error in errors)
                                + "\n\nReturn a corrected roster."
                            ),
                        },
                    ],
                )
                roster, rationale = self._parse_dynamic_roster_response(
                    repair_response,
                    investigator_id,
                    section_title,
                )
                errors = self._validate_dynamic_roster(roster)
            if not errors:
                return roster, {
                    "status": "accepted",
                    "source": "dynamic",
                    "rationale": rationale,
                    "validation_errors": [],
                    "tastes": [taste.model_dump() for taste in roster],
                }
            if not self.config.dynamic_roster_fallback_to_deterministic:
                raise RuntimeError(f"dynamic roster validation failed: {errors}")
            return fallback, {
                "status": "fallback",
                "source": "deterministic",
                "fallback_reason": "dynamic roster validation failed",
                "rationale": rationale,
                "validation_errors": errors,
                "tastes": [taste.model_dump() for taste in fallback],
            }
        except Exception as exc:
            if not self.config.dynamic_roster_fallback_to_deterministic:
                raise
            return fallback, {
                "status": "fallback",
                "source": "deterministic",
                "fallback_reason": f"dynamic planner failed: {exc}",
                "validation_errors": [str(exc)],
                "tastes": [taste.model_dump() for taste in fallback],
            }

    def _dynamic_roster_prompt(
        self,
        request: DeepDiveRunRequest,
        investigator_id: str,
        section_title: str,
    ) -> str:
        return (
            "Plan complementary research tastes for one investigator. Diversity comes from priors, "
            "search instincts, skepticism/constructiveness, temporal orientation, evidence standards, "
            "and failure modes, not from different tool access. Every subagent will receive the same "
            "complete tool catalog.\n\n"
            f"- Investigator ID: `{investigator_id}`\n"
            f"- Section title: `{section_title}`\n"
            f"- Research objective: `{request.research_objective}`\n"
            f"- Research brief: {request.research_brief or '(none)'}\n"
            f"- Required subagents: `{self.config.subagents_per_investigator}`\n"
            f"- Min/max: `{self.config.min_personas_per_investigator}`/`{self.config.max_personas_per_investigator}`\n"
            f"- Required diversity minimums: constructive={self.config.min_constructive_archetypes}, "
            f"skeptical={self.config.min_skeptical_archetypes}, prior_work={self.config.min_prior_work_archetypes}, "
            f"recent_or_future_work={self.config.min_recent_future_archetypes}\n\n"
            "Return JSON with this shape:\n"
            "{\n"
            '  "rationale": "why these tastes are complementary",\n'
            '  "tastes": [\n'
            "    {\n"
            '      "taste_id": "short_unique_id",\n'
            '      "label": "Display Name",\n'
            '      "archetype_label": "Persona function",\n'
            '      "research_zone": "zone name",\n'
            '      "diversity_roles": ["constructive", "skeptical", "prior_work", "recent_or_future_work"],\n'
            '      "best_for": ["..."],\n'
            '      "worldview": "detailed operating worldview",\n'
            '      "search_biases": ["exact search instinct", "another search instinct"],\n'
            '      "typical_queries": ["query template"],\n'
            '      "evidence_preferences": ["references", "citations"],\n'
            '      "proposal_style": "how this taste generates or rejects novelty ideas",\n'
            '      "failure_modes_to_watch": ["blind spot"],\n'
            '      "must_not_do": ["guardrail"],\n'
            '      "required_counterbalance": "what sibling agents must counterbalance"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Use this concise persona library as substrate and hints, not a cage:\n\n"
            + persona_library_summary(section_title)
        )

    def _dynamic_roster_model_role(self) -> AgentModelRole:
        try:
            return AgentModelRole(self.config.dynamic_roster_model_role)
        except ValueError:
            return AgentModelRole.INVESTIGATOR

    def _parse_dynamic_roster_response(
        self,
        response: dict[str, Any] | list[Any],
        investigator_id: str,
        section_title: str,
    ) -> tuple[list[ResearchTaste], str]:
        if isinstance(response, list):
            if len(response) == 1 and isinstance(response[0], dict) and (
                isinstance(response[0].get("tastes"), list)
                or isinstance(response[0].get("subagents"), list)
            ):
                wrapper = response[0]
                raw_items = wrapper.get("tastes") or wrapper.get("subagents") or []
                rationale = str(
                    wrapper.get("rationale")
                    or wrapper.get("planner_rationale")
                    or "Planner returned a single wrapper object inside a top-level list."
                )
            else:
                raw_items = response
                rationale = "Planner returned a top-level roster list."
        elif isinstance(response, dict):
            raw_items = response.get("tastes") or response.get("subagents") or []
            rationale = str(response.get("rationale") or response.get("planner_rationale") or "")
        else:
            raise ValueError("dynamic roster response must be a JSON object or array")
        if not isinstance(raw_items, list):
            raise ValueError("dynamic roster response must contain a `tastes` or `subagents` list")
        tastes = [
            self._coerce_dynamic_taste(item, investigator_id, section_title, idx)
            for idx, item in enumerate(raw_items, start=1)
            if isinstance(item, dict)
        ]
        return tastes, rationale

    def _coerce_dynamic_taste(
        self,
        item: dict[str, Any],
        investigator_id: str,
        section_title: str,
        idx: int,
    ) -> ResearchTaste:
        if {"worldview", "search_biases", "evidence_preferences", "failure_modes_to_watch"}.issubset(item):
            data = {
                "taste_id": item.get("taste_id") or f"{investigator_id}_taste_{idx:02d}",
                "label": item.get("label") or item.get("display_name") or f"Dynamic Taste {idx}",
                "archetype_label": item.get("archetype_label") or item.get("archetype_id") or "",
                "research_zone": item.get("research_zone") or section_title,
                "diversity_roles": item.get("diversity_roles") or self._infer_dynamic_roles(item),
                "best_for": item.get("best_for") or [],
                "worldview": item["worldview"],
                "search_biases": item["search_biases"],
                "typical_queries": item.get("typical_queries") or item.get("required_search_threads") or [],
                "evidence_preferences": item["evidence_preferences"],
                "proposal_style": item.get("proposal_style") or "",
                "failure_modes_to_watch": item["failure_modes_to_watch"],
                "must_not_do": item.get("must_not_do") or [],
                "required_counterbalance": item.get("required_counterbalance") or "Counterbalance this taste with a sibling that searches a different evidence bucket.",
            }
            return ResearchTaste.model_validate(data)
        roles = self._infer_dynamic_roles(item)
        display_name = str(item.get("display_name") or item.get("label") or f"Dynamic Taste {idx}")
        research_taste = str(item.get("research_taste") or item.get("worldview") or display_name)
        search_threads = item.get("required_search_threads") or item.get("search_biases") or []
        evidence_preferences = item.get("primary_evidence_preferences") or item.get("evidence_preferences") or []
        blind_spots = item.get("blind_spots_to_counteract") or item.get("failure_modes_to_watch") or []
        return ResearchTaste(
            taste_id=str(item.get("taste_id") or item.get("subagent_id") or f"{investigator_id}_taste_{idx:02d}"),
            label=display_name,
            archetype_label=str(item.get("archetype_id") or display_name),
            research_zone=section_title,
            diversity_roles=roles,
            best_for=list(item.get("best_for") or search_threads),
            worldview=research_taste,
            search_biases=list(search_threads) or [research_taste],
            typical_queries=list(item.get("typical_queries") or search_threads),
            evidence_preferences=list(evidence_preferences) or ["papers with explicit relevance notes"],
            proposal_style=str(item.get("proposal_style") or "Generate or reject proposal seeds according to this taste."),
            failure_modes_to_watch=list(blind_spots) or ["overlapping another subagent's search pattern"],
            must_not_do=list(item.get("must_not_do") or []),
            required_counterbalance=str(
                item.get("required_counterbalance")
                or "Pair with a sibling taste that checks different literature buckets and assumptions."
            ),
        )

    def _infer_dynamic_roles(self, item: dict[str, Any]) -> list[str]:
        text = json.dumps(item, default=str).lower()
        roles: list[str] = []
        if any(term in text for term in ("constructive", "builder", "proposal", "spinoff", "mechanism")):
            roles.append("constructive")
        if any(term in text for term in ("skeptical", "skeptic", "critic", "risk", "blind spot", "failure")):
            roles.append("skeptical")
        if any(term in text for term in ("prior", "old", "reference", "ancestry", "historical")):
            roles.append("prior_work")
        if any(term in text for term in ("recent", "future", "citation", "descendant", "sota")):
            roles.append("recent_or_future_work")
        return roles or ["constructive"]

    def _validate_dynamic_roster(self, roster: list[ResearchTaste]) -> list[str]:
        return validate_research_taste_roster(
            roster,
            min_count=self.config.min_personas_per_investigator,
            max_count=self.config.max_personas_per_investigator,
            require_diversity=self.config.require_persona_diversity,
            min_constructive=self.config.min_constructive_archetypes,
            min_skeptical=self.config.min_skeptical_archetypes,
            min_prior_work=self.config.min_prior_work_archetypes,
            min_recent_or_future_work=self.config.min_recent_future_archetypes,
            max_duplicate_archetype_functions=self.config.max_duplicate_archetype_functions,
        )

    async def _run_all_subagents(
        self,
        investigators: list[InvestigatorPlan],
        request: DeepDiveRunRequest,
    ) -> list[AgentRunResult]:
        semaphore = asyncio.Semaphore(self.config.max_parallel_subagents)

        async def run_one(plan: SubagentPlan) -> AgentRunResult:
            async with semaphore:
                try:
                    if request.mode != "live":
                        await self._emit(
                            request.run_id,
                            DeepDiveEventType.SUBAGENT_STARTED,
                            {
                                "subagent_id": plan.subagent_id,
                                "model_provider": None,
                                "model_name": None,
                            },
                        )
                    if request.mode == "live":
                        try:
                            result = await self.live_runner.run_subagent(
                                plan,
                                ResearchStage.SUBAGENT_RESEARCH,
                                run_id=request.run_id,
                            )
                        except TypeError as exc:
                            if "run_id" not in str(exc):
                                raise
                            result = await self.live_runner.run_subagent(
                                plan,
                                ResearchStage.SUBAGENT_RESEARCH,
                            )
                    else:
                        result = await self._run_subagent_budget(plan, request.mode)
                except Exception as exc:
                    result = self._subagent_error_result(plan, exc)
                await self._emit_subagent_completed(request.run_id, result)
                return result

        tasks = [run_one(subagent) for inv in investigators for subagent in inv.subagents]
        return list(await asyncio.gather(*tasks))

    def _subagent_error_result(self, plan: SubagentPlan, exc: Exception) -> AgentRunResult:
        artifact = plan.workspace_path / "handoff.md"
        trace_path = plan.workspace_path / "tool_calls.jsonl"
        raw_trace_path = plan.workspace_path / "raw_tool_results.jsonl"
        error_text = str(exc) or exc.__class__.__name__
        body = (
            "# Error Handoff\n\n"
            f"- Agent: `{plan.subagent_id}`\n"
            f"- Exit reason: `{AgentExitReason.ERROR.value}`\n"
            f"- Error type: `{exc.__class__.__name__}`\n"
            f"- Error: `{error_text}`\n\n"
            "This subagent failed after the runtime's local recovery attempts. "
            "The orchestrator isolated the failure so sibling agents and later "
            "synthesis stages can continue. Treat this handoff as incomplete and "
            "inspect any existing markdown/tool traces in this folder before using it as evidence.\n"
        )
        self.workspace.write_markdown(artifact, body)
        if trace_path.exists():
            with trace_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "type": "agent_error",
                            "error_type": exc.__class__.__name__,
                            "error": error_text,
                        },
                        default=str,
                    )
                    + "\n"
                )
        return AgentRunResult(
            agent_id=plan.subagent_id,
            stage=ResearchStage.SUBAGENT_RESEARCH,
            exit_reason=AgentExitReason.ERROR,
            tool_calls_used=0,
            workspace_path=plan.workspace_path,
            artifacts=[
                path
                for path in (
                    artifact,
                    plan.workspace_path / "findings.md",
                    plan.workspace_path / "proposal_seeds.md",
                    plan.workspace_path / "papers.md",
                    plan.workspace_path / "queries.md",
                    plan.workspace_path / "memory.md",
                    trace_path,
                    raw_trace_path,
                )
                if path.exists()
            ],
            summary=f"{plan.subagent_id} failed but was isolated; error handoff written.",
            error=error_text,
            tool_trace_path=trace_path if trace_path.exists() else None,
        )

    async def _run_subagent_budget(self, plan: SubagentPlan, mode: str) -> AgentRunResult:
        artifact = plan.workspace_path / "handoff.md"
        content = (
            f"# Hand-Off: {plan.subagent_id}\n\n"
            f"## Exit Reason\n\n`{AgentExitReason.MAX_TOOL_CALLS_REACHED.value}`\n\n"
            "## Research Taste\n\n"
            f"{plan.taste.label}: {plan.taste.worldview}\n\n"
            "## Expected Live Behavior\n\n"
            "In live mode this agent keeps searching, reading, and writing memory "
            "until its configured tool-call budget is exhausted or it has a complete "
            "evidence-backed hand-off. The investigator is reinvoked only after all "
            "sibling subagents finish their budget boundary.\n\n"
            "## Dry-Run Note\n\n"
            f"Mode `{mode}` did not call external APIs.\n"
        )
        self.workspace.write_markdown(artifact, content)
        await asyncio.sleep(0)
        return AgentRunResult(
            agent_id=plan.subagent_id,
            stage=ResearchStage.SUBAGENT_RESEARCH,
            exit_reason=AgentExitReason.MAX_TOOL_CALLS_REACHED,
            tool_calls_used=plan.max_tool_calls,
            workspace_path=plan.workspace_path,
            artifacts=[artifact],
            summary=f"{plan.taste.label} reached the configured budget boundary.",
        )

    def _synthesize_investigator(
        self,
        plan: InvestigatorPlan,
        subagent_results: list[AgentRunResult],
    ) -> AgentRunResult:
        own_results = [result for result in subagent_results if result.agent_id.startswith(plan.investigator_id)]
        artifact = plan.workspace_path / "synthesis.md"
        lines = [
            f"# Investigator Synthesis: {plan.investigator_id}",
            "",
            f"- Section: `{plan.section_title}`",
            f"- Subagents completed: `{len(own_results)}`",
            "",
            "## Completion Rule",
            "",
            "The investigator is reinvoked after every spawned subagent reaches its configured completion boundary.",
            "",
            "## Subagent Hand-Offs",
            "",
        ]
        for result in own_results:
            lines.append(f"- `{result.agent_id}`: {result.exit_reason.value}; artifacts: {', '.join(str(p) for p in result.artifacts)}")
        self.workspace.write_markdown(artifact, "\n".join(lines) + "\n")
        return AgentRunResult(
            agent_id=plan.investigator_id,
            stage=ResearchStage.INVESTIGATOR_SYNTHESIS,
            exit_reason=AgentExitReason.DRY_RUN,
            tool_calls_used=0,
            workspace_path=plan.workspace_path,
            artifacts=[artifact],
            summary=f"Synthesized {len(own_results)} subagent hand-offs.",
        )

    async def _synthesize_investigator_live(
        self,
        plan: InvestigatorPlan,
        subagent_results: list[AgentRunResult],
        request: DeepDiveRunRequest,
    ) -> AgentRunResult:
        own_results = [result for result in subagent_results if result.agent_id.startswith(plan.investigator_id)]
        artifact = plan.workspace_path / "synthesis.md"
        context_packets = [
            build_subagent_context_packet(result.workspace_path)
            for result in own_results
        ]
        prompt = (
            "You are the thinking-model investigator. Synthesize only this section's subagent evidence packets. "
            "Preserve evidence IDs, separate prior work from recent/future work, identify missing buckets, "
            "and list concrete follow-up searches. Use `findings.md`, `papers.md`, `queries.md`, "
            "`proposal_seeds.md`, `memory.md`, and tool trace summaries when they contain more evidence than `handoff.md`. "
            + _objective_synthesis_instruction(request.research_objective)
            + " Return markdown only."
        )
        error: str | None = None
        try:
            content = await self.llm.chat_markdown(
                role=AgentModelRole.INVESTIGATOR,
                messages=[
                    {"role": "system", "content": plan.system_prompt},
                    {"role": "user", "content": prompt + "\n\n" + "\n\n---\n\n".join(context_packets)},
                ],
            )
            exit_reason = AgentExitReason.COMPLETED
        except Exception as exc:
            error = str(exc) or exc.__class__.__name__
            content = _fallback_stage_markdown(
                "Investigator Synthesis Failed",
                error=error,
                context="\n\n---\n\n".join(context_packets),
            )
            exit_reason = AgentExitReason.ERROR
        self.workspace.write_markdown(artifact, content)
        profile = self.llm.profile_for(AgentModelRole.INVESTIGATOR)
        return AgentRunResult(
            agent_id=plan.investigator_id,
            stage=ResearchStage.INVESTIGATOR_SYNTHESIS,
            exit_reason=exit_reason,
            tool_calls_used=0,
            workspace_path=plan.workspace_path,
            artifacts=[artifact],
            summary=f"Live investigator synthesis over {len(own_results)} subagent hand-offs.",
            error=error,
            model_provider=profile.provider,
            model_name=profile.model,
            llm_steps_used=1,
        )

    def _write_cross_investigator_deep_dive(
        self,
        run_root: Path,
        syntheses: list[AgentRunResult],
        request: DeepDiveRunRequest,
    ) -> Path:
        artifact = run_root / "shared" / "cross_investigator_deep_dive.md"
        body = ["# Cross-Investigator Deep Dive", ""]
        body.append(f"- Research objective: `{request.research_objective}`")
        body.append("")
        body.append("This stage compares investigator syntheses for duplicated claims, contradictory evidence, missing literature buckets, and unresolved novelty questions.")
        if request.research_objective == "novelty_ideation":
            body.append("It should also identify cross-section spinoff proposal families that deserve finalization.")
        body.append("")
        for synthesis in syntheses:
            body.append(f"- `{synthesis.agent_id}`: {synthesis.summary}")
        self.workspace.write_markdown(artifact, "\n".join(body) + "\n")
        placeholders = {
            "proposal_families.md": "# Proposal Families\n\nDry-run placeholder. Live mode groups spinoff proposal families across investigators.\n",
            "global_evidence_map.md": "# Global Evidence Map\n\nDry-run placeholder. Live mode maps papers, buckets, findings, and proposal support.\n",
            "unresolved_conflicts.md": "# Unresolved Conflicts\n\nDry-run placeholder. Live mode records contradictions, weak evidence, and missing searches.\n",
        }
        for filename, content in placeholders.items():
            self.workspace.write_markdown(run_root / "shared" / filename, content)
        return artifact

    async def _run_cross_investigator_deep_dive_live(
        self,
        run_root: Path,
        investigators: list[InvestigatorPlan],
        syntheses: list[AgentRunResult],
        request: DeepDiveRunRequest,
    ) -> list[Path]:
        prompt_path = run_root / "shared" / "cross_investigator_system_prompt.md"
        novelty_contract = _novelty_contract(self.prompt_book, request.research_objective)
        system_prompt = (
            "You are the PaperCourt cross-investigator synthesis agent. Compare investigator syntheses "
            "and subagent evidence packets across the full run. Preserve paper IDs, exact search buckets, "
            "contradictions, novelty risks, and missing searches. Do not invent papers or claims."
            + ("\n\n" + novelty_contract if novelty_contract else "")
        )
        self.workspace.write_markdown(prompt_path, system_prompt)
        context = self._cross_investigator_context_bundle(run_root, investigators, syntheses)
        deliverables = [
            (
                "cross_investigator_deep_dive.md",
                "Cross-Investigator Deep Dive",
                "Compare all investigators. Identify repeated papers, contradictory findings, overlapping gaps, weak proposal seeds, and global novelty-risk patterns.",
            ),
            (
                "proposal_families.md",
                "Proposal Families",
                "Group spinoff novelty proposal seeds into families. For each family include mechanism, evidence support, closest-prior/future-work collision risks, and validation path.",
            ),
            (
                "global_evidence_map.md",
                "Global Evidence Map",
                "Map important papers, IDs, years, search buckets, supporting findings, and which investigators/subagents surfaced them.",
            ),
            (
                "unresolved_conflicts.md",
                "Unresolved Conflicts",
                "List contradictions, weak evidence, missing literature buckets, failed searches, and exact follow-up searches needed before confident claims.",
            ),
        ]
        written: list[Path] = []
        for filename, title, instruction in deliverables:
            try:
                content = await self.llm.chat_markdown(
                    role=AgentModelRole.REVISION,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": (
                                f"Research objective: `{request.research_objective}`.\n"
                                + _objective_synthesis_instruction(request.research_objective)
                                + "\n\n"
                                f"Write only the `{title}` artifact in detailed markdown. "
                                f"{instruction}\n\n"
                                "Use only this evidence bundle:\n\n"
                                + context
                            ),
                        },
                    ],
                )
            except Exception as exc:
                content = _fallback_stage_markdown(
                    f"{title} Failed",
                    error=str(exc) or exc.__class__.__name__,
                    context=context,
                )
            written.append(self.workspace.write_markdown(run_root / "shared" / filename, content))
        return written

    def _run_critiques(
        self,
        run_root: Path,
        syntheses: list[AgentRunResult],
        request: DeepDiveRunRequest,
    ) -> list[CritiqueResult]:
        lenses = [
            ("coverage_critic", "coverage and search recall"),
            ("novelty_critic", "novelty and closest-prior-work pressure"),
            ("evidence_critic", "source grounding and citation quality"),
            ("skeptic_critic", "overclaiming, contradictions, and weak inference"),
        ]
        results: list[CritiqueResult] = []
        for critic_id, lens in lenses:
            path = run_root / "critique" / critic_id
            path.mkdir(parents=True, exist_ok=True)
            prompt = self.prompt_book.critique_prompt(
                critic_id=critic_id,
                lens=lens,
                workspace_path=path,
                research_objective=request.research_objective,
                objective_directive=_objective_directive(request.research_objective),
                novelty_contract=_novelty_contract(self.prompt_book, request.research_objective),
                critique_depth_spec=self._critique_depth_spec(),
                shared_tool_spec=self._shared_tool_prompt(),
                memory_spec=self.prompt_book.memory_spec,
            )
            self.workspace.write_markdown(path / "system_prompt.md", prompt)
            artifact = path / "critique.md"
            summary = f"Dry-run critique placeholder for {lens}; live mode reads syntheses and writes actionable gaps."
            self.workspace.write_markdown(artifact, f"# {critic_id}\n\n{summary}\n")
            results.append(
                CritiqueResult(
                    critic_id=critic_id,
                    lens=lens,
                    workspace_path=path,
                    artifact_path=artifact,
                    summary=summary,
                )
            )
        return results

    async def _run_critiques_live(
        self,
        run_root: Path,
        syntheses: list[AgentRunResult],
        request: DeepDiveRunRequest,
    ) -> list[CritiqueResult]:
        lenses = [
            ("coverage_critic", "coverage and search recall"),
            ("novelty_critic", "novelty and closest-prior-work pressure"),
            ("evidence_critic", "source grounding and citation quality"),
            ("skeptic_critic", "overclaiming, contradictions, and weak inference"),
        ]
        synthesis_text = "\n\n---\n\n".join(
            path.read_text(encoding="utf-8")
            for synthesis in syntheses
            for path in synthesis.artifacts
            if path.exists()
        )
        results: list[CritiqueResult] = []
        for critic_id, lens in lenses:
            path = run_root / "critique" / critic_id
            path.mkdir(parents=True, exist_ok=True)
            prompt = self.prompt_book.critique_prompt(
                critic_id=critic_id,
                lens=lens,
                workspace_path=path,
                research_objective=request.research_objective,
                objective_directive=_objective_directive(request.research_objective),
                novelty_contract=_novelty_contract(self.prompt_book, request.research_objective),
                critique_depth_spec=self._critique_depth_spec(),
                shared_tool_spec=self._shared_tool_prompt(sorted(self.tool_runtime.executable_tool_names())),
                memory_spec=self.prompt_book.memory_spec,
            )
            self.workspace.write_markdown(path / "system_prompt.md", prompt)
            error: str | None = None
            try:
                content = await self.llm.chat_markdown(
                    role=AgentModelRole.CRITIQUE,
                    messages=[
                        {"role": "system", "content": prompt},
                        {
                            "role": "user",
                            "content": (
                                "Critique these investigator syntheses. Return markdown using the required critique sections. "
                                + _objective_critique_instruction(request.research_objective)
                                + "\n\n"
                                + synthesis_text
                            ),
                        },
                    ],
                )
            except Exception as exc:
                error = str(exc) or exc.__class__.__name__
                content = _fallback_stage_markdown(
                    f"{critic_id} Failed",
                    error=error,
                    context=synthesis_text,
                )
            artifact = path / "critique.md"
            self.workspace.write_markdown(artifact, content)
            results.append(
                CritiqueResult(
                    critic_id=critic_id,
                    lens=lens,
                    workspace_path=path,
                    artifact_path=artifact,
                    summary=(
                        f"Live critique failed for {lens}; fallback artifact written."
                        if error
                        else f"Live critique completed for {lens}."
                    ),
                )
            )
        return results

    def _finalize(
        self,
        run_root: Path,
        request: DeepDiveRunRequest,
        investigators: list[InvestigatorPlan],
        syntheses: list[AgentRunResult],
        critiques: list[CritiqueResult],
    ) -> Path:
        path = run_root / "final" / "research_deep_dive_report.md"
        prompt = self.prompt_book.finalizer_prompt(
            arxiv_url=request.arxiv_url,
            paper_id=request.paper_id or "unknown",
            workspace_path=run_root / "final",
            research_objective=request.research_objective,
            objective_directive=_objective_directive(request.research_objective),
            novelty_contract=_novelty_contract(self.prompt_book, request.research_objective),
            final_report_sections=_final_report_sections(request.research_objective),
            final_report_depth_spec=self._final_report_depth_spec(request.research_objective),
            shared_tool_spec=self._shared_tool_prompt(),
            memory_spec=self.prompt_book.memory_spec,
        )
        self.workspace.write_markdown(run_root / "final" / "system_prompt.md", prompt)
        body = [
            "# Research Deep-Dive Report",
            "",
            f"- arXiv URL: `{request.arxiv_url}`",
            f"- Paper ID: `{request.paper_id or 'unknown'}`",
            f"- Research objective: `{request.research_objective}`",
            f"- Investigators: `{len(investigators)}`",
            f"- Investigator syntheses: `{len(syntheses)}`",
            f"- Critiques: `{len(critiques)}`",
            "",
            "Dry-run report. Live finalization should merge syntheses, critique findings, literature buckets, novelty comparisons, unresolved questions, and objective-specific deliverables.",
            "",
        ]
        return self.workspace.write_markdown(path, "\n".join(body))

    async def _finalize_live(
        self,
        run_root: Path,
        request: DeepDiveRunRequest,
        investigators: list[InvestigatorPlan],
        syntheses: list[AgentRunResult],
        critiques: list[CritiqueResult],
    ) -> Path:
        path = run_root / "final" / "research_deep_dive_report.md"
        prompt = self.prompt_book.finalizer_prompt(
            arxiv_url=request.arxiv_url,
            paper_id=request.paper_id or "unknown",
            workspace_path=run_root / "final",
            research_objective=request.research_objective,
            objective_directive=_objective_directive(request.research_objective),
            novelty_contract=_novelty_contract(self.prompt_book, request.research_objective),
            final_report_sections=_final_report_sections(request.research_objective),
            final_report_depth_spec=self._final_report_depth_spec(request.research_objective),
            shared_tool_spec=self._shared_tool_prompt(sorted(self.tool_runtime.executable_tool_names())),
            memory_spec=self.prompt_book.memory_spec,
        )
        self.workspace.write_markdown(run_root / "final" / "system_prompt.md", prompt)
        artifact_text = self._finalizer_artifact_bundle(run_root, investigators, syntheses, critiques)
        try:
            content = await self.llm.chat_markdown(
                role=AgentModelRole.FINALIZATION,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Create the final research deep-dive report for {request.arxiv_url}. "
                            f"There are {len(investigators)} investigators. "
                            f"The research objective is `{request.research_objective}`. "
                            "Use only the artifacts below.\n\n"
                            + artifact_text
                        ),
                    },
                ],
            )
        except Exception as exc:
            content = _fallback_stage_markdown(
                "Finalization Failed",
                error=str(exc) or exc.__class__.__name__,
                context=artifact_text,
            )
        else:
            content = await self._repair_final_report_if_needed(
                prompt=prompt,
                artifact_text=artifact_text,
                content=content,
                objective=request.research_objective,
            )
        return self.workspace.write_markdown(path, content)

    async def _repair_final_report_if_needed(
        self,
        *,
        prompt: str,
        artifact_text: str,
        content: str,
        objective: str,
    ) -> str:
        current = content
        issues = self._final_report_quality_issues(current, objective)
        for attempt in range(1, 4):
            if not issues:
                return current
            repair_request = (
                "The final report failed runtime quality gates. Return a complete "
                "replacement markdown report, not a patch. Preserve the existing "
                "valid analysis, but expand or restructure it so every gate passes.\n\n"
                f"Repair attempt: {attempt}/3\n\n"
                "Failed gates:\n"
                + "\n".join(f"- {issue}" for issue in issues)
                + "\n\nCurrent final report:\n\n"
                + current
                + "\n\nEvidence bundle to use for the replacement report:\n\n"
                + artifact_text
            )
            try:
                current = await self.llm.chat_markdown(
                    role=AgentModelRole.FINALIZATION,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": repair_request},
                    ],
                )
            except Exception as exc:
                return (
                    current
                    + "\n\n## Final Report Quality Gate Warning\n\n"
                    + f"The runtime attempted repair pass {attempt} but the repair call failed.\n\n"
                    + f"- Error: {str(exc) or exc.__class__.__name__}\n"
                    + "\n".join(f"- Unresolved gate: {issue}" for issue in issues)
                    + "\n"
                )
            issues = self._final_report_quality_issues(current, objective)
        if issues:
            current += (
                "\n\n## Final Report Quality Gate Warning\n\n"
                "The report was repaired three times but still missed some runtime gates. "
                "Treat the missing items as known quality debt.\n\n"
                + "\n".join(f"- Unresolved gate: {issue}" for issue in issues)
                + "\n"
            )
        return current

    def _final_report_quality_issues(self, content: str, objective: str) -> list[str]:
        if objective != "novelty_ideation":
            return []
        issues: list[str] = []
        min_proposals = self.config.final_report_min_spinoff_proposals
        proposal_count = len(
            re.findall(r"^#{2,4}\s+Spinoff Proposal:\s+.+$", content, flags=re.MULTILINE)
        )
        if proposal_count < min_proposals:
            issues.append(
                f"expected at least {min_proposals} detailed `Spinoff Proposal:` sections; found {proposal_count}"
            )
        required_global_markers = (
            "High-Confidence Spinoff Proposals",
            "Speculative or Needs-More-Search Proposals",
            "Proposal Triage Matrix",
        )
        for marker in required_global_markers:
            if marker not in content:
                issues.append(f"missing required final report section `{marker}`")
        per_proposal_markers = (
            "One-sentence idea",
            "Core novelty claim",
            "Seed-paper connection",
            "Evidence basis",
            "Closest prior-work collision",
            "Future-work/SOTA collision",
            "Technical mechanism",
            "Minimum viable validation",
            "Falsification criteria",
            "Research plan",
            "Confidence",
        )
        for marker in per_proposal_markers:
            count = len(
                re.findall(rf"^#{{3,5}}\s+{re.escape(marker)}\s*$", content, flags=re.MULTILINE)
            )
            if count < min_proposals:
                issues.append(
                    f"expected `{marker}` subsection in each detailed proposal; found {count}/{min_proposals}"
                )
        return issues

    def _cross_investigator_context_bundle(
        self,
        run_root: Path,
        investigators: list[InvestigatorPlan],
        syntheses: list[AgentRunResult],
    ) -> str:
        parts = ["# Cross-Investigator Context Bundle", ""]
        for synthesis in syntheses:
            for artifact in synthesis.artifacts:
                parts.append(_format_artifact(artifact, heading="Investigator Synthesis"))
        parts.append("# Subagent Evidence Packets")
        for investigator in investigators:
            parts.append(f"\n## Investigator: {investigator.investigator_id}\n")
            for subagent in investigator.subagents:
                parts.append(build_subagent_context_packet(subagent.workspace_path))
        for filename in ("seed_metadata.json", "paper_brief.md"):
            path = run_root / "shared" / filename
            if path.exists():
                parts.append(_format_artifact(path, heading="Seed Context"))
        return "\n\n---\n\n".join(part for part in parts if part.strip())

    def _finalizer_artifact_bundle(
        self,
        run_root: Path,
        investigators: list[InvestigatorPlan],
        syntheses: list[AgentRunResult],
        critiques: list[CritiqueResult],
    ) -> str:
        parts = ["# Finalizer Evidence Bundle", ""]
        for filename in (
            "seed_metadata.json",
            "paper_brief.md",
            "cross_investigator_deep_dive.md",
            "proposal_families.md",
            "global_evidence_map.md",
            "unresolved_conflicts.md",
        ):
            path = run_root / "shared" / filename
            if path.exists():
                parts.append(_format_artifact(path, heading="Shared Artifact"))
        for synthesis in syntheses:
            for artifact in synthesis.artifacts:
                parts.append(_format_artifact(artifact, heading="Investigator Synthesis"))
        for critique in critiques:
            parts.append(_format_artifact(critique.artifact_path, heading="Critique Artifact"))
        parts.append("# Subagent Evidence Packets")
        for investigator in investigators:
            parts.append(f"\n## Investigator: {investigator.investigator_id}\n")
            for subagent in investigator.subagents:
                parts.append(build_subagent_context_packet(subagent.workspace_path))
        return "\n\n---\n\n".join(part for part in parts if part.strip())

    def _shared_tool_prompt(self, tool_names: list[str] | None = None) -> str:
        specs = self.tools
        if tool_names is not None:
            allowed = set(tool_names)
            specs = {name: spec for name, spec in self.tools.items() if name in allowed}
        return (
            self.prompt_book.shared_tool_spec
            + "\n\n"
            + _format_tool_specs(specs)
        )

    def _critique_depth_spec(self) -> str:
        return (
            f"Detail level: `{self.config.report_detail_level}`. "
            f"Each critique lens should produce at least {self.config.critique_min_points_per_lens} "
            "substantive issue/findings across blocking, major, minor, targeted searches, and proposal pressure tests when applicable. "
            "A substantive point must include: affected artifact or claim, failure mode, evidence weakness, and concrete repair action."
        )

    def _final_report_depth_spec(self, objective: str) -> str:
        base = (
            f"Detail level: `{self.config.report_detail_level}`. "
            "Write an extensive integrated report that preserves the richness of the subagent handoffs, investigator syntheses, and critique objections. "
            f"Include at least {self.config.final_report_min_open_questions} open questions or next-search items unless the artifacts contain fewer defensible ones. "
            "Prefer dense tables and structured subsections over vague prose."
        )
        if objective == "novelty_ideation":
            return (
                base
                + " "
                f"Include at least {self.config.final_report_min_spinoff_proposals} spinoff novelty proposals when enough evidence exists. "
                f"Each proposal should cite or name at least {self.config.final_report_min_evidence_items_per_proposal} supporting evidence items when available. "
                "Separate high-confidence proposals from speculative/needs-more-search proposals, include the proposal triage matrix with numeric scores, and preserve rejected weak ideas. "
                "If fewer proposals or evidence items are defensible, explicitly explain the evidence bottleneck instead of padding."
            )
        return (
            base
            + " Do not replace literature-review depth with proposal ideation. Expand evidence coverage, bucket comparisons, contradictions, and missing-search plans."
        )


def build_subagent_context_packet(path: Path, file_char_limit: int = 12000) -> str:
    sections = [
        f"# Subagent: {path.name}",
        "",
        "## Handoff",
        _read_context_file(path / "handoff.md", file_char_limit),
        "",
        "## Findings",
        _read_context_file(path / "findings.md", file_char_limit),
        "",
        "## Proposal Seeds",
        _read_context_file(path / "proposal_seeds.md", file_char_limit),
        "",
        "## Papers",
        _read_context_file(path / "papers.md", file_char_limit),
        "",
        "## Queries",
        _read_context_file(path / "queries.md", file_char_limit),
        "",
        "## Memory",
        _read_context_file(path / "memory.md", file_char_limit),
        "",
        "## Tool Trace Summary",
        summarize_tool_calls(path / "tool_calls.jsonl"),
    ]
    return "\n".join(sections).strip() + "\n"


def _fallback_stage_markdown(title: str, *, error: str, context: str, limit: int = 12000) -> str:
    excerpt = context[:limit]
    omitted = len(context) - len(excerpt)
    suffix = f"\n\n... omitted {omitted} characters from the evidence bundle.\n" if omitted > 0 else ""
    return (
        f"# {title}\n\n"
        "The live model call for this stage failed after configured provider retries. "
        "The orchestrator wrote this fallback artifact so the run can continue and "
        "the available evidence remains inspectable.\n\n"
        f"- Error: `{error}`\n\n"
        "## Available Evidence Excerpt\n\n"
        + excerpt
        + suffix
    )


def summarize_tool_calls(path: Path, max_items: int = 40) -> str:
    if not path.exists():
        return "(missing tool trace)"
    counts: Counter[str] = Counter()
    errors: list[str] = []
    rejected: list[str] = []
    queries: list[str] = []
    paper_ids: list[str] = []
    workspace_updates: list[str] = []
    research_used = 0
    workspace_used = 0
    lines_read = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        lines_read += 1
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            errors.append("malformed trace line")
            continue
        entry_type = entry.get("type")
        if entry_type == "tool_result":
            tool_name = str(entry.get("tool_name", "unknown"))
            counts[tool_name] += 1
            arguments = entry.get("arguments") or {}
            if isinstance(arguments, dict):
                query = arguments.get("query")
                if query and len(queries) < max_items:
                    queries.append(f"{tool_name}: {query}")
                if tool_name.startswith(("write_workspace", "append_workspace", "patch_workspace")):
                    rel = arguments.get("path")
                    if rel and len(workspace_updates) < max_items:
                        workspace_updates.append(f"{tool_name}: {rel}")
            paper_ids.extend(_extract_paper_ids(entry.get("result"), max_items - len(paper_ids)))
            research_used = max(research_used, int(entry.get("research_tool_calls_used") or 0))
            workspace_used = max(workspace_used, int(entry.get("workspace_tool_calls_used") or 0))
        elif entry_type == "tool_error":
            errors.append(f"{entry.get('tool_name', 'unknown')}: {entry.get('error', 'error')}")
        elif entry_type == "rejected_action":
            rejected.append(str(entry.get("reason", "rejected")))
            research_used = max(research_used, int(entry.get("research_tool_calls_used") or 0))
            workspace_used = max(workspace_used, int(entry.get("workspace_tool_calls_used") or 0))
    rows = [
        f"- Trace lines read: `{lines_read}`",
        f"- Research/API calls used: `{research_used}`",
        f"- Workspace calls used: `{workspace_used}`",
        "- Tool counts: " + (", ".join(f"`{name}`={count}" for name, count in sorted(counts.items())) or "(none)"),
        "- Search queries: " + ("; ".join(_dedupe_keep_order(queries)[:max_items]) or "(none recorded)"),
        "- Paper IDs surfaced: " + (", ".join(_dedupe_keep_order(paper_ids)[:max_items]) or "(none extracted)"),
        "- Workspace updates: " + ("; ".join(_dedupe_keep_order(workspace_updates)[:max_items]) or "(none recorded)"),
        "- Rejected actions: " + ("; ".join(_dedupe_keep_order(rejected)[:max_items]) or "(none)"),
        "- Tool errors: " + ("; ".join(_dedupe_keep_order(errors)[:max_items]) or "(none)"),
    ]
    return "\n".join(rows)


def _format_artifact(path: Path, heading: str, char_limit: int = 20000) -> str:
    return f"# {heading}: {path}\n\n{_read_context_file(path, char_limit)}"


def _read_context_file(path: Path, char_limit: int) -> str:
    if not path.exists():
        return "(missing)"
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return "(empty)"
    if len(text) <= char_limit:
        return text
    return text[:char_limit].rstrip() + f"\n\n[truncated to {char_limit} chars]"


def _extract_paper_ids(value: Any, limit: int) -> list[str]:
    if limit <= 0:
        return []
    found: list[str] = []

    def visit(item: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(item, dict):
            paper_id = item.get("paperId") or item.get("paper_id") or item.get("canonical_paper_id")
            if isinstance(paper_id, str) and paper_id:
                found.append(paper_id)
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return found


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _format_tool_specs(tools: dict[str, object]) -> str:
    lines: list[str] = []
    for name in sorted(tools):
        spec = tools[name]
        lines.extend(
            [
                f"## {spec.name}",
                f"- Category: `{spec.category}`",
                f"- Purpose: {spec.purpose}",
                f"- Endpoint/implementation: {spec.endpoint or '(derived or local tool)'}",
                f"- Reads: {', '.join(spec.reads) if spec.reads else '(none declared)'}",
                f"- Writes: {', '.join(spec.writes) if spec.writes else '(none declared)'}",
                f"- Input schema: `{spec.input_schema}`",
                f"- Output schema: `{spec.output_schema}`",
            ]
        )
        if spec.input_example:
            lines.append(f"- Example input: `{spec.input_example}`")
        if spec.output_example:
            lines.append(f"- Example output: `{spec.output_example}`")
        if spec.fallback_tools:
            lines.append(f"- Fallback tools: {', '.join(spec.fallback_tools)}")
        if spec.notes:
            lines.append(f"- Notes: {' '.join(spec.notes)}")
        lines.append("")
    return "\n".join(lines)


def _objective_directive(objective: str) -> str:
    if objective == "literature_review":
        return (
            "Objective is `literature_review`: perform an extremely deep, conservative literature review. "
            "The final product is coverage, evidence quality, bucket completeness, closest-prior-work analysis, "
            "and recommended next searches. Do not generate new research proposals except as clearly labeled "
            "open questions or search directions."
        )
    if objective == "novelty_ideation":
        return (
            "Objective is `novelty_ideation`: use the literature review as the evidence base for generating "
            "actual spinoff novelty proposals, not generic future-work bullets. Novelty generation does not mean "
            "free invention; it means turning supported gaps, contradictions, failures, missing mechanisms, and "
            "modern follow-up pressure into concrete research directions. Subagents should write raw ideas to "
            "`proposal_seeds.md`; investigators should merge them into proposal candidates; critics should try "
            "to kill or downgrade them; the finalizer should separate high-confidence proposals from speculative "
            "ones. Each proposal must name the new idea, why it may be novel relative to closest prior/future work, "
            "the technical mechanism or hypothesis, minimum validation experiment, falsification risk, and "
            "supporting paper evidence. Mark weak proposals as speculative."
        )
    raise ValueError(f"unknown research objective: {objective}")


def _clean_titles(titles: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for title in titles:
        normalized = _clean_direction_title(title)
        key = normalized.casefold()
        if normalized and key not in seen:
            cleaned.append(normalized)
            seen.add(key)
    return cleaned


def _clean_direction_title(title: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(title or "")).strip(" -:\t\r\n")
    return cleaned[:120]


def _novelty_contract(prompt_book: PromptBook, objective: str) -> str:
    if objective == "novelty_ideation":
        return prompt_book.novelty_ideation_contract
    return ""


def _objective_synthesis_instruction(objective: str) -> str:
    if objective == "literature_review":
        return (
            "Do not invent spinoff projects; instead deepen coverage and identify what evidence is still missing."
        )
    if objective == "novelty_ideation":
        return (
            "Convert `proposal_seeds.md` plus evidence-backed gaps into concrete spinoff proposal candidates with mechanisms, closest-prior-work risk, collision-search status, validation tests, falsification criteria, and confidence."
        )
    raise ValueError(f"unknown research objective: {objective}")


def _objective_critique_instruction(objective: str) -> str:
    if objective == "literature_review":
        return "Pressure-test evidence coverage and avoid proposal invention."
    if objective == "novelty_ideation":
        return "Pressure-test whether each spinoff proposal is actually novel, feasible, and evidence-supported."
    raise ValueError(f"unknown research objective: {objective}")


def _final_report_sections(objective: str) -> str:
    shared = [
        "1. Executive summary.",
        "2. Seed paper metadata.",
        "3. Literature map by bucket.",
        "4. Closest prior work.",
        "5. Direct follow-ups and recent state of field.",
        "6. Critiques, limitations, reproductions, and benchmark evidence.",
        "7. Novelty comparison table.",
        "8. Research-gap candidates.",
    ]
    if objective == "literature_review":
        sections = shared + [
            "9. Evidence quality assessment.",
            "10. Coverage gaps and recommended next searches.",
            "11. Open questions.",
        ]
    elif objective == "novelty_ideation":
        sections = shared + [
            "9. Proposal seed inventory and rejected weak ideas.",
            "10. High-confidence spinoff proposals.",
            "11. Speculative or needs-more-search proposals.",
            "12. Proposal triage matrix.",
            "13. Evidence quality and novelty-risk assessment.",
            "14. Open questions and recommended next searches.",
        ]
    else:
        raise ValueError(f"unknown research objective: {objective}")
    return "\n".join(sections)
