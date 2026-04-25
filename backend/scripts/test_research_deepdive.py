#!/usr/bin/env python3
"""Offline smoke test for the research deep-dive scaffold."""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from research_deepdive import (  # noqa: E402
    AgentModelRole,
    DeepDiveConfig,
    DeepDiveLLMProvider,
    DeepDiveOrchestrator,
    DeepDiveRunRequest,
    ModelProfile,
    PromptBook,
    build_default_tool_registry,
    generate_research_tastes,
    missing_diversity_roles,
    persona_library_summary,
    validate_research_taste_roster,
)
from research_deepdive.agent_runner import LiveAgentRunner, action_instructions  # noqa: E402
from research_deepdive.llm import (  # noqa: E402
    LLMJSONParseError,
    normalize_model_content,
    parse_model_json,
    parse_model_json_object,
)
from research_deepdive.models import (  # noqa: E402
    AgentExitReason,
    AgentRunResult,
    CritiqueResult,
    ResearchStage,
    ResearchTaste,
    SubagentPlan,
)
from research_deepdive.orchestrator import build_subagent_context_packet  # noqa: E402
from research_deepdive.workspace import WorkspaceManager  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeActionLLM:
    def __init__(self, actions: list[dict | Exception]) -> None:
        self.actions = list(actions)
        self.messages: list[list[dict[str, str]]] = []

    async def chat_json(self, *, role: AgentModelRole, messages: list[dict[str, str]], require_json: bool = True) -> dict:
        self.messages.append(messages)
        if not self.actions:
            raise AssertionError("fake LLM action queue exhausted")
        action = self.actions.pop(0)
        if isinstance(action, Exception):
            raise action
        return action

    async def chat_markdown(self, *, role: AgentModelRole, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        return "# Forced Hand-Off\n\nFake forced handoff."

    def profile_for(self, role: AgentModelRole) -> ModelProfile:
        return ModelProfile(provider="fake", model="fake-model", api_key_env="FAKE_API_KEY")


class FakeMarkdownFailLLM(FakeActionLLM):
    async def chat_markdown(self, *, role: AgentModelRole, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        raise RuntimeError("synthetic markdown failure")


class FakeFinalizerRepairLLM(FakeActionLLM):
    async def chat_markdown(self, *, role: AgentModelRole, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        if len(self.messages) == 1:
            return "# Thin Report\n\n## Proposal Triage Matrix\n\n| Proposal | Action |\n|---|---|\n"
        if len(self.messages) == 2:
            return _valid_final_report_fixture(1)
        return _valid_final_report_fixture(2)


class FakeToolRuntime:
    def __init__(self, workspace: WorkspaceManager) -> None:
        self.workspace = workspace
        self.calls: list[tuple[str, dict]] = []

    async def execute(self, tool_name: str, arguments: dict, workspace_path: Path) -> dict:
        self.calls.append((tool_name, dict(arguments)))
        if tool_name == "read_workspace_markdown":
            content, line_count = self.workspace.read_owned_text(
                workspace_path,
                arguments["path"],
                start_line=arguments.get("start_line", 1),
                end_line=arguments.get("end_line"),
            )
            return {"content": content, "line_count": line_count}
        if tool_name == "append_workspace_markdown":
            path = self.workspace.append_owned_markdown(
                workspace_path,
                arguments["path"],
                arguments["content"],
                heading=arguments.get("heading", ""),
            )
            return {"path": path.name}
        if tool_name == "patch_workspace_file":
            path = self.workspace.resolve_owned_path(workspace_path, arguments["path"])
            lines = path.read_text(encoding="utf-8").splitlines()
            start = max(1, int(arguments["start_line"]))
            end = max(start, int(arguments["end_line"]))
            replacement = str(arguments["replacement"]).splitlines()
            new_lines = lines[: start - 1] + replacement + lines[end:]
            path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
            return {"path": path.name, "changed": new_lines != lines}
        if tool_name == "write_workspace_markdown":
            path = self.workspace.write_owned_markdown(
                workspace_path,
                arguments["path"],
                arguments["content"],
            )
            return {"path": path.name}
        if tool_name == "paper_bulk_search":
            if arguments.get("query") == "transient tool failure":
                raise RuntimeError("synthetic transient paper lookup failure")
            return {
                "papers": [
                    {"paperId": "TEST1", "title": "Test Paper One", "year": 2020},
                    {"paperId": "TEST2", "title": "Test Paper Two", "year": 2021},
                    {"paperId": "TEST3", "title": "Test Paper Three", "year": 2022},
                ],
                "total": 3,
                "warnings": [],
            }
        raise AssertionError(f"unexpected fake tool call: {tool_name}")


class FakeLiveRunnerWithOneFailure:
    def __init__(self) -> None:
        self.calls = 0

    async def run_subagent(self, plan: SubagentPlan, stage: ResearchStage) -> AgentRunResult:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("synthetic subagent failure")
        artifact = plan.workspace_path / "handoff.md"
        artifact.write_text("# Hand-Off\n\nSynthetic sibling success.\n", encoding="utf-8")
        return AgentRunResult(
            agent_id=plan.subagent_id,
            stage=stage,
            exit_reason=AgentExitReason.COMPLETED,
            tool_calls_used=0,
            workspace_path=plan.workspace_path,
            artifacts=[artifact],
            summary="synthetic sibling success",
        )


async def _exercise_live_runner_budget_contract(root: Path) -> None:
    workspace = WorkspaceManager(root)
    subagent_path = root / "run" / "investigators" / "investigator_01" / "subagents" / "subagent_01"
    taste = ResearchTaste(
        taste_id="test_taste",
        label="Test Taste",
        worldview="Probe exact runtime accounting.",
        search_biases=["budget edge cases"],
        evidence_preferences=["trace evidence"],
        failure_modes_to_watch=["silent budget spending"],
        required_counterbalance="strict validation",
    )
    plan = SubagentPlan(
        subagent_id="subagent_01",
        investigator_id="investigator_01",
        section_id="section_01",
        section_title="Runtime",
        taste=taste,
        workspace_path=subagent_path,
        system_prompt="You are a test subagent.",
        allowed_tools=["append_workspace_markdown", "paper_bulk_search", "read_workspace_markdown"],
        max_tool_calls=1,
        model_role=AgentModelRole.SEARCH_SUBAGENT,
    )
    workspace.initialize_subagent(plan)
    fake_tools = FakeToolRuntime(workspace)
    actions = [
        {"action": "read_workspace_markdown", "arguments": {"path": "memory.md"}},
        {"action": "paper_bulk_search", "arguments": {"query": "transient tool failure", "limit": 1}},
        {"action": "paper_bulk_search", "query": "attention ablation", "limit": 20},
        {"action": "append_workspace_markdown", "arguments": {"heading": "No path", "content": "missing path"}},
        {"action": "paper_bulk_search", "arguments": {"query": "attention ablation", "limit": 1}},
        LLMJSONParseError(
            provider="fake",
            model="fake-model",
            content=(
                '{"action":"append_workspace_markdown","arguments":{"path":"proposal_seeds.md",'
                '"content":"## Proposal Seed: malformed literal\n\n- Status: raw"}}'
            ),
        ),
        [{"action": "append_workspace_markdown", "arguments": {"path": "memory.md", "content": "bad list"}}],
        {"action": "paper_bulk_search", "arguments": {"query": "should not execute", "limit": 1}},
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "queries.md",
                "heading": "Query: manual budget check",
                "content": (
                    "- Tool: `paper_bulk_search`\n"
                    "- Arguments: `{\"query\":\"attention ablation\",\"limit\":1}`\n"
                    "- Result count: `3`\n"
                    "- Top result IDs: TEST1, TEST2, TEST3\n"
                    "- Why this query was run: verify runtime budget accounting after invalid actions.\n"
                    "- Follow-up: inspect whether rejected actions preserved tool budget counters.\n"
                ),
            },
        },
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "papers.md",
                "heading": "## Paper: TEST1",
                "content": (
                    "- Paper ID: TEST1\n"
                    "- Year: 2020\n"
                    "- Source bucket: Semantic Scholar fixture\n"
                    "- Found by: paper_bulk_search attention ablation\n"
                    "- Relation to seed: runtime accounting fixture\n"
                    "- Why it matters: verifies one promoted paper record survives final validation.\n"
                    "- Caveat: synthetic offline record.\n\n"
                    "## Paper: TEST2\n\n"
                    "- Paper ID: TEST2\n"
                    "- Year: 2021\n"
                    "- Source bucket: Semantic Scholar fixture\n"
                    "- Found by: paper_bulk_search attention ablation\n"
                    "- Relation to seed: runtime accounting fixture\n"
                    "- Why it matters: verifies multiple candidate papers trigger finding validation.\n"
                    "- Caveat: synthetic offline record.\n\n"
                    "## Paper: TEST3\n\n"
                    "- Paper ID: TEST3\n"
                    "- Year: 2022\n"
                    "- Source bucket: Semantic Scholar fixture\n"
                    "- Found by: paper_bulk_search attention ablation\n"
                    "- Relation to seed: runtime accounting fixture\n"
                    "- Why it matters: verifies final validation requires structured paper records.\n"
                    "- Caveat: synthetic offline record.\n"
                ),
            },
        },
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "findings.md",
                "heading": "Finding: Budget accounting traceability",
                "content": (
                    "- Claim: budget accounting is traceable because malformed top-level query actions, "
                    "workspace calls missing paths, and post-budget research attempts are rejected without executing tools.\n"
                    "- Confidence: high\n"
                    "- Evidence: TEST1, TEST2, TEST3 and rejected_action trace entries.\n"
                    "- Why it matters: protects scarce research/API budget while allowing documentation repair.\n"
                    "- Caveat: offline fixture, not a real literature claim.\n\n"
                    "## Finding: Workspace repair remains available\n\n"
                    "- Claim: valid workspace calls can still update artifacts after research budget exhaustion.\n"
                    "- Confidence: medium\n"
                    "- Evidence: trace counters and final handoff after the valid search budget was exhausted.\n"
                    "- Why it matters: prevents forced handoff from skipping documentation.\n"
                    "- Caveat: full live model behavior still needs E2E validation.\n"
                ),
            },
        },
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "memory.md",
                "heading": "Runtime state",
                "content": (
                    "Stable fact: one valid research call executed and invalid actions did not spend "
                    "research or workspace budgets. Open question: real live runs should keep memory "
                    "updated after every important query so final synthesis can recover intent even when "
                    "handoff text is thin."
                ),
            },
        },
        {
            "action": "final",
            "summary": "done",
            "handoff_markdown": "# Hand-Off\n\nSearched attention ablation. Promoted TEST1. Finding recorded.",
        },
    ]
    runner = LiveAgentRunner(
        llm=FakeActionLLM(actions),
        tools=fake_tools,
        workspace=workspace,
        max_steps=20,
        workspace_write_char_budget=1200,
        max_workspace_tool_calls=100,
    )
    result = await runner.run_subagent(plan, ResearchStage.SUBAGENT_RESEARCH)

    _assert(result.research_tool_calls_used == 1, "only valid search should spend research budget")
    _assert(result.workspace_tool_calls_used == 5, "valid workspace tools should spend only workspace budget")
    _assert(result.llm_steps_used == 13, "rejected actions and tool errors should consume LLM steps, not tool budgets")
    executed = [name for name, _ in fake_tools.calls]
    _assert(executed == [
        "read_workspace_markdown",
        "paper_bulk_search",
        "paper_bulk_search",
        "append_workspace_markdown",
        "append_workspace_markdown",
        "append_workspace_markdown",
        "append_workspace_markdown",
    ], f"unexpected executed tools: {executed}")
    _assert("should not execute" not in str(fake_tools.calls), "research call after budget exhaustion executed")

    trace_lines = [
        json.loads(line)
        for line in (subagent_path / "tool_calls.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rejections = [entry for entry in trace_lines if entry.get("type") == "rejected_action"]
    _assert(len(rejections) == 5, f"expected five rejected actions, saw {len(rejections)}")
    reasons = " ".join(entry["reason"] for entry in rejections)
    _assert("top level" in reasons, "top-level query rejection missing from trace")
    _assert("arguments.path" in reasons, "workspace missing path rejection missing from trace")
    _assert("not parseable" in reasons, "malformed JSON rejection missing from trace")
    _assert("not an object action" in reasons, "non-object JSON rejection missing from trace")
    _assert("budget is exhausted" in reasons, "research budget rejection missing from trace")
    for entry in rejections:
        _assert(entry["research_tool_calls_used"] <= 1, "rejection trace has invalid research counter")
        _assert(entry["workspace_tool_calls_used"] <= 1, "invalid actions should not spend workspace budget")
    tool_errors = [entry for entry in trace_lines if entry.get("type") == "tool_error"]
    _assert(len(tool_errors) == 1, f"expected one recoverable tool error, saw {len(tool_errors)}")
    _assert(
        tool_errors[0]["error_type"] == "RuntimeError",
        "tool error trace should preserve exception type",
    )

    raw_lines = [
        json.loads(line)
        for line in (subagent_path / "raw_tool_results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _assert(len(raw_lines) == 2, "raw research tool results and errors should be logged automatically")
    _assert(raw_lines[0]["result"]["error"], "raw log should capture failed research tool calls")
    _assert(raw_lines[1]["paper_ids"][:3] == ["TEST1", "TEST2", "TEST3"], "raw log should extract paper IDs")
    queries_text = (subagent_path / "queries.md").read_text(encoding="utf-8")
    _assert("failed (RuntimeError)" in queries_text, "auto query entry should record tool failures")
    _assert("## Query: paper_bulk_search 1" in queries_text, "runtime should auto-append structured query entry")
    _assert("- Arguments:" in queries_text and "- Top result IDs:" in queries_text, "auto query entry missing fields")
    papers_text = (subagent_path / "papers.md").read_text(encoding="utf-8")
    _assert("## Paper: TEST1" in papers_text, "append helper should normalize markdown headings")
    _assert("## ## Paper:" not in papers_text, "append helper should not duplicate heading markers")


async def _exercise_artifact_bundle_contract(root: Path) -> None:
    fake_llm = FakeActionLLM([])
    config = DeepDiveConfig(
        workspace_root=root,
        max_investigators=1,
        subagents_per_investigator=1,
        min_personas_per_investigator=1,
        max_personas_per_investigator=1,
        require_persona_diversity=False,
        max_parallel_subagents=1,
        thinking_profile=ModelProfile(provider="fake", model="thinking", api_key_env="FAKE"),
        light_profile=ModelProfile(provider="fake", model="light", api_key_env="FAKE"),
    )
    orchestrator = DeepDiveOrchestrator(config=config, llm_provider=fake_llm)
    request = DeepDiveRunRequest(
        run_id="bundle run",
        arxiv_url="https://arxiv.org/abs/1706.03762",
        paper_id="ARXIV:1706.03762",
        section_titles=["Novelty"],
        research_brief="Bundle contract fixture.",
        research_objective="novelty_ideation",
        mode="live",
    )
    run_root = orchestrator.workspace.prepare_run(request.run_id)
    investigators = orchestrator._plan_investigators(request, run_root)
    investigator = investigators[0]
    subagent = investigator.subagents[0]

    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "handoff.md",
        "# Hand-Off\n\nPACKET-HANDOFF mentions PACKET-PAPER.",
    )
    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "queries.md",
        "# Queries\n\nQuery: packet query; params limit=3; result count=1.",
    )
    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "papers.md",
        "# Papers\n\n- PACKET-PAPER. Packet Paper. 2024. Relevance: bundle fixture.",
    )
    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "findings.md",
        "# Findings\n\nPACKET-FINDING: packet evidence supports a novelty gap.",
    )
    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "proposal_seeds.md",
        "# Proposal Seeds\n\n## Proposal Seed: Packet seed\n\n- Candidate novelty: PACKET-SEED.\n",
    )
    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "memory.md",
        "# Memory\n\nOpen question: does PACKET-PAPER collide with the seed?",
    )
    orchestrator.workspace.write_markdown(
        subagent.workspace_path / "tool_calls.jsonl",
        json.dumps(
            {
                "type": "tool_result",
                "tool_name": "paper_bulk_search",
                "arguments": {"query": "packet query", "limit": 3},
                "result": {"papers": [{"paperId": "PACKET-PAPER"}]},
                "research_tool_calls_used": 1,
                "workspace_tool_calls_used": 2,
            }
        )
        + "\n",
    )

    packet = build_subagent_context_packet(subagent.workspace_path)
    _assert("## Findings" in packet and "PACKET-FINDING" in packet, "packet should include findings")
    _assert("## Proposal Seeds" in packet and "PACKET-SEED" in packet, "packet should include proposal seeds")
    _assert("## Papers" in packet and "PACKET-PAPER" in packet, "packet should include papers")
    _assert("Query: packet query" in packet, "packet should include queries")
    _assert("Tool Trace Summary" in packet and "paper_bulk_search" in packet, "packet should include trace summary")

    synthesis_path = investigator.workspace_path / "synthesis.md"
    orchestrator.workspace.write_markdown(
        synthesis_path,
        "# Synthesis\n\nSYNTHESIS-PAPER integrates PACKET-PAPER and PACKET-FINDING.",
    )
    syntheses = [
        AgentRunResult(
            agent_id=investigator.investigator_id,
            stage=ResearchStage.INVESTIGATOR_SYNTHESIS,
            exit_reason=AgentExitReason.COMPLETED,
            tool_calls_used=0,
            workspace_path=investigator.workspace_path,
            artifacts=[synthesis_path],
        )
    ]
    cross_paths = await orchestrator._run_cross_investigator_deep_dive_live(
        run_root,
        investigators,
        syntheses,
        request,
    )
    _assert(len(cross_paths) == 4, "live cross-investigator stage should write four artifacts")
    for path in cross_paths:
        _assert(path.exists(), f"missing cross-investigator artifact: {path.name}")
    cross_prompt_text = "\n\n".join(message["content"] for message in fake_llm.messages[0])
    _assert("PACKET-PAPER" in cross_prompt_text, "cross-investigator prompt should include subagent papers")
    _assert("PACKET-FINDING" in cross_prompt_text, "cross-investigator prompt should include subagent findings")

    critique_path = run_root / "critique" / "coverage_critic" / "critique.md"
    orchestrator.workspace.write_markdown(
        critique_path,
        "# Critique\n\nCRITIQUE-FINDING asks for stronger closest-prior-work checks.",
    )
    critiques = [
        CritiqueResult(
            critic_id="coverage_critic",
            lens="coverage",
            workspace_path=critique_path.parent,
            artifact_path=critique_path,
            summary="fixture critique",
        )
    ]
    await orchestrator._finalize_live(run_root, request, investigators, syntheses, critiques)
    final_prompt_text = "\n\n".join(message["content"] for message in fake_llm.messages[-1])
    _assert("cross_investigator_deep_dive.md" in final_prompt_text, "finalizer should receive cross deep dive")
    _assert("proposal_families.md" in final_prompt_text, "finalizer should receive proposal families")
    _assert("global_evidence_map.md" in final_prompt_text, "finalizer should receive global evidence map")
    _assert("unresolved_conflicts.md" in final_prompt_text, "finalizer should receive unresolved conflicts")
    _assert("PACKET-PAPER" in final_prompt_text, "finalizer should receive subagent papers")
    _assert("PACKET-FINDING" in final_prompt_text, "finalizer should receive subagent findings")
    _assert("PACKET-SEED" in final_prompt_text, "finalizer should receive subagent proposal seeds")
    _assert("Query: packet query" in final_prompt_text, "finalizer should receive subagent queries")
    _assert("CRITIQUE-FINDING" in final_prompt_text, "finalizer should receive critique artifacts")


async def _exercise_subagent_failure_isolation(root: Path) -> None:
    config = DeepDiveConfig(
        workspace_root=root,
        max_investigators=1,
        subagents_per_investigator=2,
        min_personas_per_investigator=2,
        max_personas_per_investigator=2,
        require_persona_diversity=False,
        max_parallel_subagents=1,
        thinking_profile=ModelProfile(provider="fake", model="thinking", api_key_env="FAKE"),
        light_profile=ModelProfile(provider="fake", model="light", api_key_env="FAKE"),
    )
    orchestrator = DeepDiveOrchestrator(config=config, llm_provider=FakeActionLLM([]))
    request = DeepDiveRunRequest(
        run_id="failure isolation",
        arxiv_url="https://arxiv.org/abs/1706.03762",
        paper_id="ARXIV:1706.03762",
        section_titles=["Method"],
        research_brief="Failure isolation fixture.",
        research_objective="novelty_ideation",
        mode="live",
    )
    run_root = orchestrator.workspace.prepare_run(request.run_id)
    investigators = orchestrator._plan_investigators(request, run_root)
    orchestrator.live_runner = FakeLiveRunnerWithOneFailure()  # type: ignore[assignment]
    results = await orchestrator._run_all_subagents(investigators, request)
    _assert(len(results) == 2, "all subagent results should be returned despite one failure")
    failed = [result for result in results if result.exit_reason == AgentExitReason.ERROR]
    completed = [result for result in results if result.exit_reason == AgentExitReason.COMPLETED]
    _assert(len(failed) == 1, "one subagent should be marked as an isolated error")
    _assert(len(completed) == 1, "sibling subagent should still complete")
    _assert(failed[0].error == "synthetic subagent failure", "isolated error should be recorded")
    handoff = (failed[0].workspace_path / "handoff.md").read_text(encoding="utf-8")
    _assert("# Error Handoff" in handoff, "failed subagent should get an explicit error handoff")
    _assert("sibling agents and later synthesis stages can continue" in handoff, "handoff should explain continuation")


async def _exercise_stage_failure_fallbacks(root: Path) -> None:
    config = DeepDiveConfig(
        workspace_root=root,
        max_investigators=1,
        subagents_per_investigator=1,
        min_personas_per_investigator=1,
        max_personas_per_investigator=1,
        require_persona_diversity=False,
        max_parallel_subagents=1,
        thinking_profile=ModelProfile(provider="fake", model="thinking", api_key_env="FAKE"),
        light_profile=ModelProfile(provider="fake", model="light", api_key_env="FAKE"),
    )
    orchestrator = DeepDiveOrchestrator(config=config, llm_provider=FakeMarkdownFailLLM([]))
    request = DeepDiveRunRequest(
        run_id="stage fallback",
        arxiv_url="https://arxiv.org/abs/1706.03762",
        paper_id="ARXIV:1706.03762",
        section_titles=["Novelty"],
        research_brief="Stage fallback fixture.",
        research_objective="novelty_ideation",
        mode="live",
    )
    run_root = orchestrator.workspace.prepare_run(request.run_id)
    investigators = orchestrator._plan_investigators(request, run_root)
    subagent = investigators[0].subagents[0]
    orchestrator.workspace.write_markdown(subagent.workspace_path / "handoff.md", "# Hand-Off\n\nFixture evidence.")
    subagent_results = [
        AgentRunResult(
            agent_id=subagent.subagent_id,
            stage=ResearchStage.SUBAGENT_RESEARCH,
            exit_reason=AgentExitReason.COMPLETED,
            tool_calls_used=0,
            workspace_path=subagent.workspace_path,
            artifacts=[subagent.workspace_path / "handoff.md"],
        )
    ]

    synthesis = await orchestrator._synthesize_investigator_live(investigators[0], subagent_results, request)
    _assert(synthesis.exit_reason == AgentExitReason.ERROR, "failed synthesis should be isolated")
    _assert("Investigator Synthesis Failed" in synthesis.artifacts[0].read_text(encoding="utf-8"), "synthesis fallback missing")

    cross_paths = await orchestrator._run_cross_investigator_deep_dive_live(
        run_root,
        investigators,
        [synthesis],
        request,
    )
    _assert(len(cross_paths) == 4, "cross-investigator fallback should still write all artifacts")
    _assert(
        all("Failed" in path.read_text(encoding="utf-8").splitlines()[0] for path in cross_paths),
        "cross-investigator fallback artifact missing failure header",
    )

    critiques = await orchestrator._run_critiques_live(run_root, [synthesis], request)
    _assert(len(critiques) == 4, "critique fallback should still write all critique artifacts")
    _assert(
        all("failed" in critique.summary for critique in critiques),
        "critique fallback summaries should report failures",
    )

    final_path = await orchestrator._finalize_live(run_root, request, investigators, [synthesis], critiques)
    _assert(final_path.exists(), "finalization fallback should still write final report path")
    _assert("Finalization Failed" in final_path.read_text(encoding="utf-8"), "finalization fallback missing")


def _valid_final_report_fixture(count: int) -> str:
    sections = [
        "# Research Deep-Dive Report",
        "",
        "## High-Confidence Spinoff Proposals",
        "",
    ]
    for index in range(1, count + 1):
        sections.extend(
            [
                f"### Spinoff Proposal: Fixture Proposal {index}",
                "",
                "#### One-sentence idea",
                "",
                "A concrete fixture proposal.",
                "",
                "#### Core novelty claim",
                "",
                "The proposal is different from the seed and closest prior work.",
                "",
                "#### Seed-paper connection",
                "",
                "- Seed mechanism/claim: fixture seed mechanism.",
                "- What the seed paper does: fixture seed behavior.",
                "- What this proposal changes: fixture technical change.",
                "",
                "#### Evidence basis",
                "",
                "| Evidence | Paper/artifact | Why it matters |",
                "|---|---|---|",
                "| Fixture evidence | TEST | Supports the fixture proposal. |",
                "",
                "#### Closest prior-work collision",
                "",
                "| Collision risk | Paper | Relationship | Why proposal may still survive |",
                "|---|---|---|---|",
                "| Prior collision | PRIOR | Adjacent | The mechanism differs. |",
                "",
                "#### Future-work/SOTA collision",
                "",
                "Future-work collision is explicitly named.",
                "",
                "#### Technical mechanism",
                "",
                "A concrete algorithmic mechanism.",
                "",
                "#### Minimum viable validation",
                "",
                "- First experiment/proof/implementation: fixture experiment.",
                "- Required dataset/tool/formalism: fixture dataset.",
                "- Success criterion: fixture success criterion.",
                "",
                "#### Falsification criteria",
                "",
                "The idea fails if the prior collision already implements the mechanism.",
                "",
                "#### Research plan",
                "",
                "- Week 1: reproduce the relevant baseline.",
                "- Week 2-3: implement the proposed mechanism.",
                "- First deliverable: an ablation table.",
                "",
                "#### Confidence",
                "",
                "- Confidence: medium",
                "- What would raise confidence: stronger collision search.",
                "- What would lower confidence: prior work match.",
                "",
            ]
        )
    sections.extend(
        [
            "## Speculative or Needs-More-Search Proposals",
            "",
            "Speculative proposals are tracked separately.",
            "",
            "## Proposal Triage Matrix",
            "",
            "| Proposal | Type | Novelty score | Specificity score | Evidence score | Feasibility score | Research-value score | Biggest collision risk | Recommended action |",
            "|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for index in range(1, count + 1):
        sections.append(f"| Fixture Proposal {index} | system | 4 | 4 | 4 | 4 | 4 | PRIOR | promote |")
    return "\n".join(sections) + "\n"


async def _exercise_final_report_repair_contract(root: Path) -> None:
    config = DeepDiveConfig(
        workspace_root=root,
        max_investigators=1,
        subagents_per_investigator=1,
        min_personas_per_investigator=1,
        max_personas_per_investigator=1,
        require_persona_diversity=False,
        final_report_min_spinoff_proposals=2,
        thinking_profile=ModelProfile(provider="fake", model="thinking", api_key_env="FAKE"),
        light_profile=ModelProfile(provider="fake", model="light", api_key_env="FAKE"),
    )
    fake_llm = FakeFinalizerRepairLLM([])
    orchestrator = DeepDiveOrchestrator(config=config, llm_provider=fake_llm)
    request = DeepDiveRunRequest(
        run_id="final repair",
        arxiv_url="https://arxiv.org/abs/1706.03762",
        paper_id="ARXIV:1706.03762",
        section_titles=["Novelty"],
        research_brief="Final repair fixture.",
        research_objective="novelty_ideation",
        mode="live",
    )
    run_root = orchestrator.workspace.prepare_run(request.run_id)
    final_path = await orchestrator._finalize_live(run_root, request, [], [], [])
    final_text = final_path.read_text(encoding="utf-8")
    _assert(len(fake_llm.messages) == 3, "thin final report should trigger repeated repair calls")
    _assert("Thin Report" not in final_text, "repair should replace the thin report")
    _assert(
        not orchestrator._final_report_quality_issues(final_text, "novelty_ideation"),
        "repaired final report should satisfy novelty quality gates",
    )


def _dynamic_taste(idx: int, roles: list[str], archetype: str) -> dict:
    return {
        "taste_id": f"dynamic_taste_{idx}",
        "label": f"Dynamic Taste {idx}",
        "archetype_label": archetype,
        "research_zone": "novelty",
        "diversity_roles": roles,
        "best_for": [f"bucket {idx}"],
        "worldview": f"Dynamic worldview {idx}",
        "search_biases": [f"search thread {idx}"],
        "typical_queries": [f"query template {idx}"],
        "evidence_preferences": [f"evidence bucket {idx}"],
        "proposal_style": f"proposal style {idx}",
        "failure_modes_to_watch": [f"failure mode {idx}"],
        "must_not_do": [f"do not duplicate taste {idx}"],
        "required_counterbalance": f"counterbalance {idx}",
    }


async def _exercise_dynamic_roster_contract(root: Path) -> None:
    valid_response = {
        "rationale": "Use complementary live-planned tastes.",
        "tastes": [
            _dynamic_taste(1, ["constructive", "recent_or_future_work"], "Builder"),
            _dynamic_taste(2, ["skeptical"], "Skeptic"),
            _dynamic_taste(3, ["prior_work"], "Prior Work Mapper"),
        ],
    }
    fake_llm = FakeActionLLM([[valid_response]])
    config = DeepDiveConfig(
        workspace_root=root / "accepted",
        max_investigators=1,
        subagents_per_investigator=3,
        min_personas_per_investigator=3,
        max_personas_per_investigator=3,
        require_persona_diversity=True,
        dynamic_roster_enabled=True,
        max_parallel_subagents=1,
        thinking_profile=ModelProfile(provider="fake", model="thinking", api_key_env="FAKE"),
        light_profile=ModelProfile(provider="fake", model="light", api_key_env="FAKE"),
    )
    orchestrator = DeepDiveOrchestrator(config=config, llm_provider=fake_llm)
    request = DeepDiveRunRequest(
        run_id="dynamic accepted",
        arxiv_url="https://arxiv.org/abs/1706.03762",
        paper_id="ARXIV:1706.03762",
        section_titles=["Related work and novelty"],
        research_objective="novelty_ideation",
        mode="live",
    )
    run_root = orchestrator.workspace.prepare_run(request.run_id)
    warnings: list[str] = []
    investigators = await orchestrator._plan_investigators_live(request, run_root, warnings)
    _assert(not warnings, f"valid dynamic roster should not warn: {warnings}")
    labels = [subagent.taste.label for subagent in investigators[0].subagents]
    _assert(labels == ["Dynamic Taste 1", "Dynamic Taste 2", "Dynamic Taste 3"], "dynamic roster was not accepted")
    tool_sets = {tuple(subagent.allowed_tools) for subagent in investigators[0].subagents}
    _assert(len(tool_sets) == 1, "dynamic subagents should share the same tool surface")
    planner_roster = json.loads(
        (investigators[0].workspace_path / "planner_roster.json").read_text(encoding="utf-8")
    )
    _assert(planner_roster["status"] == "accepted", "accepted roster status not recorded")
    prompt = (investigators[0].subagents[0].workspace_path / "system_prompt.md").read_text(encoding="utf-8")
    _assert("Dynamic worldview 1" in prompt, "subagent prompt should reflect dynamic taste")
    _assert((run_root / "shared" / "planning_trace.md").exists(), "planning trace should be written")

    invalid = {
        "rationale": "Bad duplicate roster.",
        "tastes": [
            _dynamic_taste(1, ["constructive"], "Duplicate"),
            _dynamic_taste(1, ["constructive"], "Duplicate"),
            _dynamic_taste(1, ["constructive"], "Duplicate"),
        ],
    }
    fallback_llm = FakeActionLLM([invalid, invalid])
    fallback_config = config.model_copy(update={"workspace_root": root / "fallback"})
    fallback_orchestrator = DeepDiveOrchestrator(config=fallback_config, llm_provider=fallback_llm)
    fallback_roster, note = await fallback_orchestrator._plan_dynamic_roster_for_investigator(
        request=request,
        investigator_id="investigator_01_related_work_and_novelty",
        section_title="Related work and novelty",
    )
    _assert(note["status"] == "fallback", "invalid dynamic roster should fall back explicitly")
    _assert(note["validation_errors"], "fallback should record validation errors")
    _assert(len({taste.label for taste in fallback_roster}) == 3, "fallback roster should be deterministic and unique")


async def main_async() -> None:
    prompt_book = PromptBook()
    _assert("Shared Tool Specification" in prompt_book.shared_tool_spec, "shared tool spec loads")
    _assert("Memory And Workspace" in prompt_book.memory_spec, "memory spec loads")

    tools = build_default_tool_registry()
    for required in (
        "resolve_arxiv_paper",
        "get_paper_metadata",
        "get_references",
        "get_high_impact_references",
        "get_citations",
        "get_recent_citations",
        "paper_bulk_search",
        "paper_relevance_search",
        "snippet_search",
        "claim_snippet_search",
        "batch_get_papers",
        "batch_get_authors",
        "survey_search",
        "critique_limitation_search",
        "reproducibility_search",
        "same_author_prior_work",
        "same_author_followup_work",
        "rank_candidates_by_specter2_similarity",
        "novelty_neighbor_search",
        "build_literature_context_pack",
        "novelty_comparison_table",
        "google_scholar_search",
        "google_scholar_cited_by_search",
        "list_dataset_releases",
        "write_workspace_markdown",
        "patch_workspace_file",
    ):
        _assert(required in tools, f"missing tool: {required}")
        _assert(tools[required].input_example or required.startswith("list_dataset"), f"missing input example: {required}")

    tastes = generate_research_tastes("Method", 5)
    _assert(len(tastes) == 5, "expected five tastes")
    _assert(len({taste.label for taste in tastes}) == 5, "taste labels should be unique")
    roles = {role for taste in tastes for role in taste.diversity_roles}
    for role in ("constructive", "skeptical", "prior_work", "recent_or_future_work"):
        _assert(role in roles, f"missing persona diversity role: {role}")
    _assert(not validate_research_taste_roster(tastes, min_count=5, max_count=5), "deterministic roster should validate")
    _assert("Persona Library Summary" in persona_library_summary("Novelty"), "persona library summary should render")
    duplicate_roster = [tastes[0], tastes[0].model_copy(update={"label": tastes[1].label})]
    _assert(validate_research_taste_roster(duplicate_roster, require_diversity=False), "duplicate roster should be rejected")
    underdiverse = [tastes[0].model_copy(update={"diversity_roles": ["constructive"]})]
    _assert(
        "skeptical" in missing_diversity_roles(underdiverse),
        "missing diversity helper should report absent roles",
    )

    normalized = normalize_model_content('<thought>hidden</thought>```json\n{"action":"final"}\n```')
    _assert(normalized == '{"action":"final"}', "model content normalization should strip thoughts and JSON fences")
    parsed = parse_model_json_object(
        'prefix {"action":"append_workspace_markdown","arguments":{"path":"proposal_seeds.md","content":"line one\nline two"}} suffix'
    )
    _assert(parsed["arguments"]["content"] == "line one\nline two", "JSON parser should tolerate embedded action objects and literal newlines")
    roster = parse_model_json('[{"taste_id":"dynamic"}]')
    _assert(isinstance(roster, list) and roster[0]["taste_id"] == "dynamic", "provider JSON parser should allow roster arrays")

    instructions = action_instructions(1200)
    _assert("Invalid search" in instructions, "action prompt should show invalid top-level query example")
    _assert("arguments.path" in instructions, "action prompt should require workspace paths")
    _assert("separate high budget" in instructions, "action prompt should explain split budgets")

    default_config = DeepDiveConfig()
    _assert(
        default_config.thinking_profile.model == "gemma-4-26b-a4b-it",
        "thinking profile should default to Gemma",
    )
    _assert(
        default_config.thinking_profile.reasoning_effort == "high",
        "thinking profile should use high reasoning by default",
    )
    _assert(
        default_config.thinking_profile.api_key_env == "GEMMA_API_KEY",
        "thinking profile should default to the Gemma key env var",
    )
    _assert(
        default_config.light_profile.model == "gemma-4-26b-a4b-it",
        "light profile should default to Gemma",
    )
    _assert(
        default_config.light_profile.reasoning_effort == "high",
        "light profile should use high reasoning by default",
    )
    _assert(
        default_config.light_profile.api_key_env == "GEMMA_API_KEY",
        "light profile should default to the Gemma key env var",
    )
    _assert(default_config.dynamic_roster_enabled, "dynamic roster should be enabled by default")
    _assert(
        default_config.thinking_profile.max_output_tokens >= 32768,
        "thinking Gemma output budget should be high by default",
    )
    _assert(
        default_config.light_profile.max_output_tokens >= 32768,
        "light Gemma output budget should be high by default",
    )
    _assert(
        default_config.thinking_profile.min_interval_seconds <= 0.25,
        "thinking Gemma interval should not throttle unnecessarily",
    )
    _assert(
        default_config.light_profile.min_interval_seconds <= 0.25,
        "light Gemma interval should not throttle unnecessarily",
    )
    _assert(
        default_config.subagent_max_workspace_tool_calls >= 10000,
        "workspace tool budget should be high enough for detailed markdown repair",
    )
    _assert(
        default_config.subagent_max_steps >= 3000,
        "Gemma-backed subagent step budget should not starve documentation",
    )
    _assert(
        default_config.workspace_write_char_budget >= 20000,
        "workspace write char budget should allow large markdown chunks",
    )

    with tempfile.TemporaryDirectory() as tmp:
        config = DeepDiveConfig(
            workspace_root=Path(tmp),
            max_investigators=2,
            subagents_per_investigator=3,
            min_personas_per_investigator=3,
            max_personas_per_investigator=7,
            subagent_max_tool_calls=7,
            max_parallel_subagents=2,
            report_detail_level="extensive",
            final_report_min_spinoff_proposals=8,
            final_report_min_evidence_items_per_proposal=3,
            final_report_min_open_questions=10,
            critique_min_points_per_lens=6,
            thinking_profile=ModelProfile(
                provider="openai",
                model="thinking-test-model",
                api_key_env="OPENAI_API_KEY",
            ),
            light_profile=ModelProfile(
                provider="gemini_openai",
                model="light-test-model",
                api_key_env="GEMMA_API_KEY",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                reasoning_effort="high",
            ),
        )
        provider = DeepDiveLLMProvider(config)
        _assert(
            provider.profile_for(AgentModelRole.INVESTIGATOR).model == "thinking-test-model",
            "investigator should use thinking model profile",
        )
        _assert(
            provider.profile_for(AgentModelRole.SEARCH_SUBAGENT).model == "light-test-model",
            "search subagent should use light model profile",
        )

        await _exercise_live_runner_budget_contract(Path(tmp) / "runner")
        await _exercise_artifact_bundle_contract(Path(tmp) / "bundles")
        await _exercise_dynamic_roster_contract(Path(tmp) / "dynamic")
        await _exercise_subagent_failure_isolation(Path(tmp) / "failure-isolation")
        await _exercise_stage_failure_fallbacks(Path(tmp) / "stage-fallbacks")
        await _exercise_final_report_repair_contract(Path(tmp) / "final-repair")

        orchestrator = DeepDiveOrchestrator(config=config)
        _assert(
            "patch_workspace_file" in orchestrator.tool_runtime.executable_tool_names(),
            "patch_workspace_file should be executable in live runtime",
        )
        result = await orchestrator.run(
            DeepDiveRunRequest(
                run_id="smoke run",
                arxiv_url="https://arxiv.org/abs/1706.03762",
                paper_id="ARXIV:1706.03762",
                section_titles=["Architecture", "Experiments"],
                research_brief="Verify prompt/workspace orchestration only.",
                research_objective="novelty_ideation",
            )
        )

        _assert(result.status == "success", f"run failed: {result.error}")
        _assert(ResearchStage.FINALIZATION in result.stages_completed, "finalization stage missing")
        _assert(len(result.investigators) == 2, "expected two investigators")
        _assert(len(result.subagent_results) == 6, "expected six subagent results")
        _assert(len(result.critiques) == 4, "expected four critiques")
        _assert(result.final_report_path is not None, "final report path missing")
        _assert(result.final_report_path.exists(), "final report was not written")
        for filename in (
            "cross_investigator_deep_dive.md",
            "proposal_families.md",
            "global_evidence_map.md",
            "unresolved_conflicts.md",
        ):
            _assert((result.workspace_path / "shared" / filename).exists(), f"missing shared artifact: {filename}")

        for investigator in result.investigators:
            _assert(investigator.workspace_path.exists(), "investigator workspace missing")
            _assert((investigator.workspace_path / "system_prompt.md").exists(), "investigator prompt missing")
            labels = [subagent.taste.label for subagent in investigator.subagents]
            _assert(len(labels) == len(set(labels)), "subagent tastes must be unique per investigator")
            for subagent in investigator.subagents:
                _assert(subagent.max_tool_calls == 7, "tool-call budget should come from config")
                _assert((subagent.workspace_path / "memory.md").exists(), "subagent memory missing")
                _assert((subagent.workspace_path / "queries.md").exists(), "subagent queries memory missing")
                _assert((subagent.workspace_path / "papers.md").exists(), "subagent papers memory missing")
                _assert((subagent.workspace_path / "findings.md").exists(), "subagent findings memory missing")
                _assert((subagent.workspace_path / "proposal_seeds.md").exists(), "subagent proposal seeds missing")
                _assert((subagent.workspace_path / "tool_calls.jsonl").exists(), "subagent tool trace missing")
                _assert((subagent.workspace_path / "raw_tool_results.jsonl").exists(), "subagent raw tool trace missing")
                _assert((subagent.workspace_path / "handoff.md").exists(), "subagent handoff missing")
                _assert(subagent.model_role == AgentModelRole.SEARCH_SUBAGENT, "subagent should use light model role")
                prompt = (subagent.workspace_path / "system_prompt.md").read_text(encoding="utf-8")
                _assert("Shared Tool Surface" in prompt, "subagent prompt missing tool spec")
                _assert("Concrete Tool Registry" in prompt, "subagent prompt missing concrete tool registry")
                _assert("Example input" in prompt, "subagent prompt missing tool examples")
                _assert("paper_bulk_search" in prompt, "subagent prompt missing Semantic Scholar search tool")
                _assert("google_scholar_search" in prompt, "subagent prompt missing SerpApi tool")
                _assert("Research Taste" in prompt, "subagent prompt missing taste")
                _assert("Research objective: `novelty_ideation`" in prompt, "subagent prompt missing objective")
                _assert("spinoff novelty proposals" in prompt, "subagent prompt missing novelty objective guidance")
                _assert("Novelty Ideation Contract" in prompt, "subagent prompt missing novelty contract")
                _assert("proposal_seeds.md" in prompt, "subagent prompt missing proposal seed artifact")

        assert result.final_report_path is not None
        final_prompt = (result.final_report_path.parent / "system_prompt.md").read_text(encoding="utf-8")
        _assert("Research objective: `novelty_ideation`" in final_prompt, "finalizer prompt missing objective")
        _assert("spinoff novelty proposals" in final_prompt.lower(), "finalizer prompt missing proposal section")
        _assert("Proposal triage matrix" in final_prompt, "finalizer prompt missing proposal triage")
        _assert("High-Confidence Spinoff Proposals" in final_prompt, "finalizer prompt missing high-confidence proposal split")
        _assert("Speculative or Needs-More-Search Proposals" in final_prompt, "finalizer prompt missing speculative proposal split")
        _assert("Novelty Score Rubric" in final_prompt, "finalizer prompt missing novelty score rubric")
        _assert("Report Depth Contract" in final_prompt, "finalizer prompt missing depth contract")
        _assert("at least 8 spinoff novelty proposals" in final_prompt, "finalizer prompt missing proposal count")
        _assert("at least 3 supporting evidence items" in final_prompt, "finalizer prompt missing evidence depth")

        for critique in result.critiques:
            critique_prompt = (critique.workspace_path / "system_prompt.md").read_text(encoding="utf-8")
            _assert("Critique Depth Contract" in critique_prompt, "critique prompt missing depth contract")
            _assert("at least 6" in critique_prompt, "critique prompt missing point minimum")
            _assert("Novelty Critique Rules" in critique_prompt, "critique prompt missing novelty critique rules")

        literature_prompt = prompt_book.finalizer_prompt(
            arxiv_url="https://arxiv.org/abs/1706.03762",
            paper_id="ARXIV:1706.03762",
            workspace_path=Path(tmp) / "lit-final",
            research_objective="literature_review",
            objective_directive="Objective is `literature_review`: test directive.",
            novelty_contract="",
            final_report_depth_spec="Detail level: `extensive`. Do not replace literature-review depth with proposal ideation.",
            final_report_sections="10. Coverage gaps and recommended next searches.",
            shared_tool_spec=prompt_book.shared_tool_spec,
            memory_spec=prompt_book.memory_spec,
        )
        _assert("Research objective: `literature_review`" in literature_prompt, "literature prompt missing objective")
        _assert("Coverage gaps and recommended next searches" in literature_prompt, "literature prompt missing review section")
        _assert("do not invent proposals" in literature_prompt.lower(), "literature prompt should suppress proposals")
        _assert("Novelty Ideation Contract" not in literature_prompt, "literature prompt should not include novelty contract")

    print("research deep-dive smoke ok")


if __name__ == "__main__":
    asyncio.run(main_async())
