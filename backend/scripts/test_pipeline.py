"""End-to-end live pipeline test for arXiv URL -> TeX -> Prompt 2.4.

Usage (from repo root):
    python backend/scripts/test_pipeline.py https://arxiv.org/pdf/1706.03762

This script makes real OpenAI calls. Use ``--max-claims`` while developing if
you want to validate the full path without reviewing every extracted claim.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import dotenv

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

dotenv.load_dotenv(BACKEND / ".env")

from agents.attacker import AttackerAgent  # noqa: E402
from agents.base import AgentContext  # noqa: E402
from agents.claim_extractor import ClaimExtractorAgent  # noqa: E402
from agents.dag_builder import DAGBuilderAgent  # noqa: E402
from agents.defender import DefenderAgent  # noqa: E402
from agents.numeric_adversary import NumericAdversaryAgent  # noqa: E402
from agents.symbolic_verifier import SymbolicVerifierAgent  # noqa: E402
from agents.tex_parser import TexParserAgent  # noqa: E402
from config import settings  # noqa: E402
from models import ClaimUnit  # noqa: E402
from utils.arxiv import fetch_arxiv_source, parse_arxiv_url  # noqa: E402


async def run(arxiv_value: str, max_claims: int | None) -> int:
    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set. Add it to backend/.env and re-run.")
        return 1

    ref = parse_arxiv_url(arxiv_value)
    if not ref:
        print(f"Could not parse arXiv URL/id: {arxiv_value!r}")
        return 1

    pipeline_output: Dict[str, Any] = {
        "arxiv_id": ref.canonical,
        "source_url": ref.source_url,
    }

    with tempfile.TemporaryDirectory() as tmp:
        print(f"=== Fetching TeX source for {ref.canonical} ===")
        source = await fetch_arxiv_source(ref, tmp)
        tex_hash = hashlib.md5(source.tex_text.encode("utf-8")).hexdigest()[:12]
        pipeline_output["paper_hash"] = tex_hash
        pipeline_output["source"] = {
            "archive_path": source.archive_path,
            "main_tex_path": source.main_tex_path,
            "tex_files": len(source.tex_paths),
            "chars": len(source.tex_text),
        }
        print(f"  main_tex:  {Path(source.main_tex_path).name}")
        print(f"  tex_files: {len(source.tex_paths)}")
        print(f"  chars:     {len(source.tex_text)}")

        print("\n=== TexParserAgent ===")
        parser_result = await TexParserAgent().run(
            AgentContext(job_id="manual-test", extra={"tex_text": source.tex_text})
        )
        if parser_result.status != "success":
            print(f"  parser status={parser_result.status} error={parser_result.error}")
            return 1
        parsed = parser_result.output
        print(f"  title:        {parsed['title'][:100]!r}")
        print(f"  sections:     {len(parsed['sections'])}")
        print(f"  equations:    {len(parsed['equations'])}")
        print(f"  bibliography: {len(parsed['bibliography'])}")
        print(f"  raw_text:     {len(parsed['raw_text'])} chars")

        pipeline_output["parser"] = {
            "title": parsed["title"],
            "sections": len(parsed["sections"]),
            "equations": len(parsed["equations"]),
            "bibliography": len(parsed["bibliography"]),
        }

        print("\n=== ClaimExtractorAgent ===")
        ext_result = await ClaimExtractorAgent().run(
            AgentContext(job_id="manual-test", extra={"parser_output": parsed})
        )
        claims: List[dict] = ext_result.output.get("claims", [])
        print(f"  status:     {ext_result.status}")
        print(f"  confidence: {ext_result.confidence}")
        print(f"  claims:     {len(claims)}")
        if ext_result.error:
            print(f"  warning:    {ext_result.error}")
        if not claims:
            pipeline_output["extractor"] = {
                "status": ext_result.status,
                "total_claims": 0,
                "claims": [],
            }
            _save(pipeline_output, tex_hash)
            return 1

        by_type: Dict[str, int] = {}
        for claim in claims:
            by_type[claim["claim_type"]] = by_type.get(claim["claim_type"], 0) + 1
        for claim_type, count in sorted(by_type.items()):
            print(f"    {claim_type}: {count}")
        pipeline_output["extractor"] = {
            "status": ext_result.status,
            "total_claims": len(claims),
            "by_type": by_type,
            "claims": claims,
        }

        print("\n=== DAGBuilderAgent ===")
        dag_result = await DAGBuilderAgent().run(
            AgentContext(job_id="manual-test", extra={"claims": claims})
        )
        dag_out = dag_result.output
        print(f"  status:     {dag_result.status}")
        print(f"  confidence: {dag_result.confidence}")
        print(f"  edges:      {len(dag_out.get('edges', []))}")
        print(f"  roots:      {dag_out.get('roots', [])}")
        print(f"  topo order: {dag_out.get('topological_order', [])}")
        pipeline_output["dag"] = {
            "status": dag_result.status,
            "edges": dag_out.get("edges", []),
            "adjacency": dag_out.get("adjacency", {}),
            "roots": dag_out.get("roots", []),
            "topological_order": dag_out.get("topological_order", []),
        }

        ordered_claims = _claims_in_order(claims, dag_out.get("topological_order", []))
        if max_claims is not None:
            ordered_claims = ordered_claims[:max_claims]
            print(f"\n=== Prompt 2.1-2.4 on first {len(ordered_claims)} claim(s) ===")
        else:
            print(f"\n=== Prompt 2.1-2.4 on all {len(ordered_claims)} claim(s) ===")

        review_results = await _run_prompt_2_1_to_2_4(ordered_claims)
        pipeline_output["review_results"] = review_results

    _save(pipeline_output, pipeline_output["paper_hash"])
    return 0


async def _run_prompt_2_1_to_2_4(claims: List[dict]) -> Dict[str, dict]:
    symbolic = SymbolicVerifierAgent()
    numeric = NumericAdversaryAgent()
    attacker = AttackerAgent()
    defender = DefenderAgent()
    output: Dict[str, dict] = {}

    for claim_dict in claims:
        claim = ClaimUnit.model_validate(claim_dict)
        snippet = claim.text[:100].replace("\n", " ")
        print(f"\n  {claim.claim_id} ({claim.claim_type}): {snippet}...")

        verification_results = []
        verifier_results = await asyncio.gather(
            symbolic.run(AgentContext(job_id="manual-test", claim=claim)),
            numeric.run(AgentContext(job_id="manual-test", claim=claim)),
            return_exceptions=True,
        )
        for result in verifier_results:
            if isinstance(result, Exception):
                verification_results.append(
                    {
                        "tier": "unknown",
                        "status": "inconclusive",
                        "evidence": str(result),
                        "confidence": 0.0,
                    }
                )
                continue
            verification_results.append(result.output)
            print(
                f"    {result.output.get('tier')}: {result.output.get('status')} "
                f"(conf={result.output.get('confidence')})"
            )

        attacker_result = await attacker.run(
            AgentContext(
                job_id="manual-test",
                claim=claim,
                extra={"verification_results": verification_results},
            )
        )
        challenges = attacker_result.output.get("challenges", [])
        print(f"    challenges: {len(challenges)}")

        defender_result = await defender.run(
            AgentContext(
                job_id="manual-test",
                claim=claim,
                extra={"challenges": challenges},
            )
        )
        rebuttals = defender_result.output.get("rebuttals", [])
        print(f"    rebuttals:  {len(rebuttals)}")

        output[claim.claim_id] = {
            "claim": claim.model_dump(),
            "verification_results": verification_results,
            "challenges": challenges,
            "rebuttals": rebuttals,
        }

    return output


def _claims_in_order(claims: List[dict], topological_order: List[str]) -> List[dict]:
    claim_map = {claim["claim_id"]: claim for claim in claims}
    ordered = [claim_map[cid] for cid in topological_order if cid in claim_map]
    if len(ordered) == len(claims):
        return ordered
    seen = {claim["claim_id"] for claim in ordered}
    ordered.extend(claim for claim in claims if claim["claim_id"] not in seen)
    return ordered


def _save(data: dict, paper_hash: str) -> None:
    out_dir = BACKEND / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{paper_hash}_pipeline.json"
    safe = json.loads(json.dumps(data, default=str))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)
    print(f"\nPipeline output saved to {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arxiv_url", help="arXiv URL or bare arXiv id")
    parser.add_argument(
        "--max-claims",
        type=int,
        default=None,
        help="Optional cap for Prompt 2.1-2.4 live agent work.",
    )
    args = parser.parse_args()
    return asyncio.run(run(args.arxiv_url, args.max_claims))


if __name__ == "__main__":
    raise SystemExit(main())
