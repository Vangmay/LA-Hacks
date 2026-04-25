"""Config-driven orchestration for deep literature research runs."""
from __future__ import annotations

import asyncio
from pathlib import Path

from .config import DeepDiveConfig
from .models import (
    AgentExitReason,
    AgentRunResult,
    CritiqueResult,
    DeepDiveRunRequest,
    DeepDiveRunResult,
    InvestigatorPlan,
    ResearchStage,
    SubagentPlan,
)
from .personas import generate_research_tastes
from .prompts import PromptBook
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
    ) -> None:
        self.config = (config or DeepDiveConfig()).normalized()
        self.prompt_book = prompt_book or PromptBook()
        self.tools = build_default_tool_registry()
        self.workspace = WorkspaceManager(self.config.workspace_root)

    async def run(self, request: DeepDiveRunRequest) -> DeepDiveRunResult:
        stages: list[ResearchStage] = []
        warnings: list[str] = []
        run_root = self.workspace.prepare_run(request.run_id)

        try:
            stages.append(ResearchStage.BOOTSTRAP)
            investigators = self._plan_investigators(request, run_root)
            stages.append(ResearchStage.INVESTIGATOR_PLANNING)

            subagent_results = await self._run_all_subagents(investigators, request)
            stages.append(ResearchStage.SUBAGENT_RESEARCH)

            syntheses = [self._synthesize_investigator(plan, subagent_results) for plan in investigators]
            stages.append(ResearchStage.INVESTIGATOR_SYNTHESIS)

            self._write_cross_investigator_deep_dive(run_root, syntheses)
            stages.append(ResearchStage.CROSS_INVESTIGATOR_DEEP_DIVE)

            critiques = self._run_critiques(run_root, syntheses)
            stages.append(ResearchStage.CRITIQUE)

            final_report = self._finalize(run_root, request, investigators, syntheses, critiques)
            stages.append(ResearchStage.FINALIZATION)

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
    ) -> list[InvestigatorPlan]:
        section_titles = request.section_titles or ["whole paper"]
        selected = section_titles[: self.config.max_investigators]
        tool_names = sorted(self.tools)
        shared_tools = self._shared_tool_prompt()

        investigators: list[InvestigatorPlan] = []
        for idx, title in enumerate(selected, start=1):
            section_id = f"section_{idx:02d}_{slugify(title)}"
            investigator_id = f"investigator_{idx:02d}_{slugify(title)}"
            investigator_path = self.workspace.investigator_path(request.run_id, investigator_id)
            tastes = generate_research_tastes(
                title,
                self.config.subagents_per_investigator,
                min_count=self.config.min_personas_per_investigator,
                max_count=self.config.max_personas_per_investigator,
                require_diversity=self.config.require_persona_diversity,
            )

            subagents: list[SubagentPlan] = []
            for sub_idx, taste in enumerate(tastes, start=1):
                subagent_id = f"{investigator_id}_subagent_{sub_idx:02d}"
                subagent_path = self.workspace.subagent_path(investigator_path, subagent_id)
                subagent_prompt = self.prompt_book.subagent_prompt(
                    arxiv_url=request.arxiv_url,
                    paper_id=request.paper_id or "unknown",
                    research_brief=request.research_brief or "(no extra brief)",
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
                )
                self.workspace.initialize_subagent(plan)
                subagents.append(plan)

            investigator_prompt = self.prompt_book.investigator_prompt(
                arxiv_url=request.arxiv_url,
                paper_id=request.paper_id or "unknown",
                research_brief=request.research_brief or "(no extra brief)",
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

    async def _run_all_subagents(
        self,
        investigators: list[InvestigatorPlan],
        request: DeepDiveRunRequest,
    ) -> list[AgentRunResult]:
        semaphore = asyncio.Semaphore(self.config.max_parallel_subagents)

        async def run_one(plan: SubagentPlan) -> AgentRunResult:
            async with semaphore:
                return await self._run_subagent_budget(plan, request.mode)

        tasks = [run_one(subagent) for inv in investigators for subagent in inv.subagents]
        return list(await asyncio.gather(*tasks))

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

    def _write_cross_investigator_deep_dive(
        self,
        run_root: Path,
        syntheses: list[AgentRunResult],
    ) -> Path:
        artifact = run_root / "shared" / "cross_investigator_deep_dive.md"
        body = ["# Cross-Investigator Deep Dive", ""]
        body.append("This stage compares investigator syntheses for duplicated claims, contradictory evidence, missing literature buckets, and unresolved novelty questions.")
        body.append("")
        for synthesis in syntheses:
            body.append(f"- `{synthesis.agent_id}`: {synthesis.summary}")
        return self.workspace.write_markdown(artifact, "\n".join(body) + "\n")

    def _run_critiques(
        self,
        run_root: Path,
        syntheses: list[AgentRunResult],
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
            shared_tool_spec=self._shared_tool_prompt(),
            memory_spec=self.prompt_book.memory_spec,
        )
        self.workspace.write_markdown(run_root / "final" / "system_prompt.md", prompt)
        body = [
            "# Research Deep-Dive Report",
            "",
            f"- arXiv URL: `{request.arxiv_url}`",
            f"- Paper ID: `{request.paper_id or 'unknown'}`",
            f"- Investigators: `{len(investigators)}`",
            f"- Investigator syntheses: `{len(syntheses)}`",
            f"- Critiques: `{len(critiques)}`",
            "",
            "Dry-run report. Live finalization should merge syntheses, critique findings, literature buckets, novelty comparisons, and unresolved questions.",
            "",
        ]
        return self.workspace.write_markdown(path, "\n".join(body))

    def _shared_tool_prompt(self) -> str:
        return (
            self.prompt_book.shared_tool_spec
            + "\n\n"
            + _format_tool_specs(self.tools)
        )


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
