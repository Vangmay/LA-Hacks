#!/usr/bin/env python3
"""Run a monitored live research deep-dive."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from config import settings  # noqa: E402
from research_deepdive import DeepDiveConfig, DeepDiveOrchestrator, DeepDiveRunRequest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arxiv-url", default="https://arxiv.org/abs/1706.03762")
    parser.add_argument("--section", action="append", dest="sections")
    parser.add_argument(
        "--objective",
        choices=["novelty_ideation", "literature_review"],
        default="novelty_ideation",
    )
    parser.add_argument("--run-id", default="")
    parser.add_argument("--max-investigators", type=int, default=3)
    parser.add_argument("--subagents-per-investigator", type=int, default=3)
    parser.add_argument("--subagent-tool-calls", type=int, default=18)
    parser.add_argument("--subagent-steps", type=int, default=24)
    parser.add_argument("--parallel-subagents", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--semantic-scholar-interval", type=float, default=1.2)
    parser.add_argument("--semantic-scholar-retries", type=int, default=4)
    parser.add_argument("--serpapi-max-requests", type=int, default=50)
    parser.add_argument("--thinking-provider", default=settings.deepdive_thinking_provider)
    parser.add_argument("--thinking-model", default=settings.deepdive_thinking_model)
    parser.add_argument("--thinking-api-key-env", default=settings.deepdive_thinking_api_key_env)
    parser.add_argument("--thinking-base-url", default=settings.deepdive_thinking_base_url)
    parser.add_argument(
        "--thinking-reasoning-effort",
        default=settings.deepdive_thinking_reasoning_effort,
    )
    parser.add_argument(
        "--thinking-min-interval",
        type=float,
        default=settings.deepdive_thinking_min_interval_seconds,
    )
    parser.add_argument("--light-provider", default=settings.deepdive_light_provider)
    parser.add_argument("--light-model", default=settings.deepdive_light_model)
    parser.add_argument("--light-api-key-env", default=settings.deepdive_light_api_key_env)
    parser.add_argument("--light-base-url", default=settings.deepdive_light_base_url)
    parser.add_argument("--light-reasoning-effort", default=settings.deepdive_light_reasoning_effort)
    parser.add_argument(
        "--light-min-interval",
        type=float,
        default=settings.deepdive_light_min_interval_seconds,
    )
    parser.add_argument("--report-detail-level", default=settings.deepdive_report_detail_level)
    parser.add_argument(
        "--min-spinoff-proposals",
        type=int,
        default=settings.deepdive_final_report_min_spinoff_proposals,
    )
    parser.add_argument(
        "--min-evidence-items-per-proposal",
        type=int,
        default=settings.deepdive_final_report_min_evidence_items_per_proposal,
    )
    parser.add_argument(
        "--min-open-questions",
        type=int,
        default=settings.deepdive_final_report_min_open_questions,
    )
    parser.add_argument(
        "--critique-min-points",
        type=int,
        default=settings.deepdive_critique_min_points_per_lens,
    )
    return parser.parse_args()


def has_key(name: str) -> bool:
    if os.getenv(name) or getattr(settings, name.lower(), ""):
        return True
    return False


def require_key(name: str) -> None:
    if has_key(name):
        return
    raise SystemExit(f"Missing required environment variable: {name}")


async def main_async() -> None:
    args = parse_args()

    sections = args.sections or ["Core method", "Experiments", "Related work and novelty"]
    run_id = args.run_id or "live_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_config = DeepDiveConfig()
    thinking_profile = base_config.thinking_profile.model_copy(
        update={
            "provider": args.thinking_provider,
            "model": args.thinking_model,
            "api_key_env": args.thinking_api_key_env,
            "base_url": args.thinking_base_url,
            "reasoning_effort": args.thinking_reasoning_effort,
            "min_interval_seconds": args.thinking_min_interval,
        }
    )
    light_profile = base_config.light_profile.model_copy(
        update={
            "provider": args.light_provider,
            "model": args.light_model,
            "api_key_env": args.light_api_key_env,
            "base_url": args.light_base_url,
            "reasoning_effort": args.light_reasoning_effort,
            "min_interval_seconds": args.light_min_interval,
        }
    )
    config = DeepDiveConfig(
        max_investigators=args.max_investigators,
        subagents_per_investigator=args.subagents_per_investigator,
        min_personas_per_investigator=args.subagents_per_investigator,
        max_personas_per_investigator=max(args.subagents_per_investigator, 7),
        subagent_max_tool_calls=args.subagent_tool_calls,
        subagent_max_steps=args.subagent_steps,
        max_parallel_subagents=args.parallel_subagents,
        stage_timeout_seconds=args.timeout_seconds,
        semantic_scholar_min_interval_seconds=args.semantic_scholar_interval,
        semantic_scholar_max_retries=args.semantic_scholar_retries,
        serpapi_max_requests=args.serpapi_max_requests,
        report_detail_level=args.report_detail_level,
        final_report_min_spinoff_proposals=args.min_spinoff_proposals,
        final_report_min_evidence_items_per_proposal=args.min_evidence_items_per_proposal,
        final_report_min_open_questions=args.min_open_questions,
        critique_min_points_per_lens=args.critique_min_points,
        thinking_profile=thinking_profile,
        light_profile=light_profile,
    )
    require_key(config.thinking_profile.api_key_env)
    require_key(config.light_profile.api_key_env)
    orchestrator = DeepDiveOrchestrator(config=config)
    result = await orchestrator.run(
        DeepDiveRunRequest(
            run_id=run_id,
            arxiv_url=args.arxiv_url,
            paper_id=args.arxiv_url,
            section_titles=sections,
            research_brief=(
                "Run a live monitored literature deep dive. Search references, citations, "
                "recent work, old/prior work, critiques, and novelty-relevant neighboring papers. "
                "Write durable markdown memory before handoff."
            ),
            research_objective=args.objective,
            mode="live",
        )
    )
    print(f"status={result.status}")
    print(f"workspace={result.workspace_path}")
    print(f"final_report={result.final_report_path}")
    if result.error:
        print(f"error={result.error}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main_async())
