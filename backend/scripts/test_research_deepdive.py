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
from research_deepdive.llm import normalize_model_content  # noqa: E402
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
    def __init__(self, actions: list[dict]) -> None:
        self.actions = list(actions)
        self.messages: list[list[dict[str, str]]] = []

    async def chat_json(self, *, role: AgentModelRole, messages: list[dict[str, str]], require_json: bool = True) -> dict:
        self.messages.append(messages)
        if not self.actions:
            raise AssertionError("fake LLM action queue exhausted")
        return self.actions.pop(0)

    async def chat_markdown(self, *, role: AgentModelRole, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        return "# Forced Hand-Off\n\nFake forced handoff."

    def profile_for(self, role: AgentModelRole) -> ModelProfile:
        return ModelProfile(provider="fake", model="fake-model", api_key_env="FAKE_API_KEY")


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
        if tool_name == "write_workspace_markdown":
            path = self.workspace.write_owned_markdown(
                workspace_path,
                arguments["path"],
                arguments["content"],
            )
            return {"path": path.name}
        if tool_name == "paper_bulk_search":
            return {
                "papers": [{"paperId": "TEST1", "title": "Test Paper", "year": 2020}],
                "total": 1,
                "warnings": [],
            }
        raise AssertionError(f"unexpected fake tool call: {tool_name}")


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
        {"action": "paper_bulk_search", "query": "attention ablation", "limit": 20},
        {"action": "append_workspace_markdown", "arguments": {"heading": "No path", "content": "missing path"}},
        {"action": "paper_bulk_search", "arguments": {"query": "attention ablation", "limit": 1}},
        {"action": "paper_bulk_search", "arguments": {"query": "should not execute", "limit": 1}},
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "queries.md",
                "heading": "Query log",
                "content": (
                    "Query: attention ablation; params limit=1; result count=1. "
                    "Purpose: verify runtime budget accounting after invalid actions. "
                    "Follow-up: inspect whether rejected actions preserved tool budget counters."
                ),
            },
        },
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "papers.md",
                "heading": "Paper TEST1",
                "content": (
                    "- Paper ID: TEST1. Title: Test Paper. Year: 2020. Source: Semantic Scholar. "
                    "Relevance: runtime fixture for budget accounting and finalization behavior. "
                    "Evidence note: this synthetic record is promoted after one valid search so the "
                    "agent has a traceable paper item before writing findings and handoff."
                ),
            },
        },
        {
            "action": "append_workspace_markdown",
            "arguments": {
                "path": "findings.md",
                "heading": "Finding",
                "content": (
                    "Finding: budget accounting is traceable because malformed top-level query actions, "
                    "workspace calls missing paths, and post-budget research attempts are rejected without "
                    "executing tools. Evidence: TEST1 and the rejected_action trace entries. "
                    "Uncertainty: this is an offline fixture, not a real literature claim."
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
    _assert(result.llm_steps_used == 10, "rejected actions should consume LLM steps, not tool budgets")
    executed = [name for name, _ in fake_tools.calls]
    _assert(executed == [
        "read_workspace_markdown",
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
    _assert(len(rejections) == 3, f"expected three rejected actions, saw {len(rejections)}")
    reasons = " ".join(entry["reason"] for entry in rejections)
    _assert("top level" in reasons, "top-level query rejection missing from trace")
    _assert("arguments.path" in reasons, "workspace missing path rejection missing from trace")
    _assert("budget is exhausted" in reasons, "research budget rejection missing from trace")
    for entry in rejections:
        _assert(entry["research_tool_calls_used"] <= 1, "rejection trace has invalid research counter")
        _assert(entry["workspace_tool_calls_used"] <= 1, "invalid actions should not spend workspace budget")


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
    _assert("Query: packet query" in final_prompt_text, "finalizer should receive subagent queries")
    _assert("CRITIQUE-FINDING" in final_prompt_text, "finalizer should receive critique artifacts")


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
    fake_llm = FakeActionLLM([valid_response["tastes"]])
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

        orchestrator = DeepDiveOrchestrator(config=config)
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
                _assert((subagent.workspace_path / "tool_calls.jsonl").exists(), "subagent tool trace missing")
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

        assert result.final_report_path is not None
        final_prompt = (result.final_report_path.parent / "system_prompt.md").read_text(encoding="utf-8")
        _assert("Research objective: `novelty_ideation`" in final_prompt, "finalizer prompt missing objective")
        _assert("Spinoff novelty proposals" in final_prompt, "finalizer prompt missing proposal section")
        _assert("Proposal triage matrix" in final_prompt, "finalizer prompt missing proposal triage")
        _assert("Report Depth Contract" in final_prompt, "finalizer prompt missing depth contract")
        _assert("at least 8 spinoff novelty proposals" in final_prompt, "finalizer prompt missing proposal count")
        _assert("at least 3 supporting evidence items" in final_prompt, "finalizer prompt missing evidence depth")

        for critique in result.critiques:
            critique_prompt = (critique.workspace_path / "system_prompt.md").read_text(encoding="utf-8")
            _assert("Critique Depth Contract" in critique_prompt, "critique prompt missing depth contract")
            _assert("at least 6" in critique_prompt, "critique prompt missing point minimum")

        literature_prompt = prompt_book.finalizer_prompt(
            arxiv_url="https://arxiv.org/abs/1706.03762",
            paper_id="ARXIV:1706.03762",
            workspace_path=Path(tmp) / "lit-final",
            research_objective="literature_review",
            objective_directive="Objective is `literature_review`: test directive.",
            final_report_depth_spec="Detail level: `extensive`. Do not replace literature-review depth with proposal ideation.",
            final_report_sections="10. Coverage gaps and recommended next searches.",
            shared_tool_spec=prompt_book.shared_tool_spec,
            memory_spec=prompt_book.memory_spec,
        )
        _assert("Research objective: `literature_review`" in literature_prompt, "literature prompt missing objective")
        _assert("Coverage gaps and recommended next searches" in literature_prompt, "literature prompt missing review section")
        _assert("do not invent proposals" in literature_prompt.lower(), "literature prompt should suppress proposals")

    print("research deep-dive smoke ok")


if __name__ == "__main__":
    asyncio.run(main_async())
