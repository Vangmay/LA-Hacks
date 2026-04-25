#!/usr/bin/env python3
"""Offline smoke test for the research deep-dive scaffold."""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from research_deepdive import (  # noqa: E402
    DeepDiveConfig,
    DeepDiveOrchestrator,
    DeepDiveRunRequest,
    PromptBook,
    build_default_tool_registry,
    generate_research_tastes,
)
from research_deepdive.models import ResearchStage  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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

    with tempfile.TemporaryDirectory() as tmp:
        config = DeepDiveConfig(
            workspace_root=Path(tmp),
            max_investigators=2,
            subagents_per_investigator=3,
            min_personas_per_investigator=3,
            max_personas_per_investigator=7,
            subagent_max_tool_calls=7,
            max_parallel_subagents=2,
        )
        orchestrator = DeepDiveOrchestrator(config=config)
        result = await orchestrator.run(
            DeepDiveRunRequest(
                run_id="smoke run",
                arxiv_url="https://arxiv.org/abs/1706.03762",
                paper_id="ARXIV:1706.03762",
                section_titles=["Architecture", "Experiments"],
                research_brief="Verify prompt/workspace orchestration only.",
            )
        )

        _assert(result.status == "success", f"run failed: {result.error}")
        _assert(ResearchStage.FINALIZATION in result.stages_completed, "finalization stage missing")
        _assert(len(result.investigators) == 2, "expected two investigators")
        _assert(len(result.subagent_results) == 6, "expected six subagent results")
        _assert(len(result.critiques) == 4, "expected four critiques")
        _assert(result.final_report_path is not None, "final report path missing")
        _assert(result.final_report_path.exists(), "final report was not written")

        for investigator in result.investigators:
            _assert(investigator.workspace_path.exists(), "investigator workspace missing")
            _assert((investigator.workspace_path / "system_prompt.md").exists(), "investigator prompt missing")
            labels = [subagent.taste.label for subagent in investigator.subagents]
            _assert(len(labels) == len(set(labels)), "subagent tastes must be unique per investigator")
            for subagent in investigator.subagents:
                _assert(subagent.max_tool_calls == 7, "tool-call budget should come from config")
                _assert((subagent.workspace_path / "memory.md").exists(), "subagent memory missing")
                _assert((subagent.workspace_path / "handoff.md").exists(), "subagent handoff missing")
                prompt = (subagent.workspace_path / "system_prompt.md").read_text(encoding="utf-8")
                _assert("Shared Tool Surface" in prompt, "subagent prompt missing tool spec")
                _assert("Concrete Tool Registry" in prompt, "subagent prompt missing concrete tool registry")
                _assert("Example input" in prompt, "subagent prompt missing tool examples")
                _assert("paper_bulk_search" in prompt, "subagent prompt missing Semantic Scholar search tool")
                _assert("google_scholar_search" in prompt, "subagent prompt missing SerpApi tool")
                _assert("Research Taste" in prompt, "subagent prompt missing taste")

    print("research deep-dive smoke ok")


if __name__ == "__main__":
    asyncio.run(main_async())
