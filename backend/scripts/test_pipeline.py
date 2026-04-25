"""End-to-end pipeline test: PDF -> ParserAgent -> ClaimExtractorAgent -> DAGBuilderAgent.

Usage (from backend/):
    python scripts/test_pipeline.py path/to/paper.pdf

Defaults to tests/fixtures/test_paper.pdf. Requires OPENAI_API_KEY in
backend/.env. Makes real API calls (typically $0.05-$0.20).

Output JSON saved to outputs/{paper_hash}_pipeline.json.
"""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
import dotenv

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

dotenv.load_dotenv(BACKEND / ".env")

from agents.base import AgentContext
from agents.claim_extractor import ClaimExtractorAgent
from agents.dag_builder import DAGBuilderAgent
from agents.parser import ParserAgent
from config import settings


def _paper_hash(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:12]


async def run(pdf_path: str) -> int:
    if not os.path.isfile(pdf_path):
        print(f"PDF not found: {pdf_path}")
        print("Download the test paper with:")
        print("  wget -q https://arxiv.org/pdf/1706.03762 -O backend/tests/fixtures/test_paper.pdf")
        return 1

    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set. Add it to backend/.env and re-run.")
        return 1

    paper_hash = _paper_hash(pdf_path)
    pipeline_output: dict = {"paper_hash": paper_hash}

    # ── Step 1: Parser ────────────────────────────────────────────────────────
    print(f"\n=== ParserAgent ({pdf_path}) ===")
    parser_ctx = AgentContext(job_id="manual-test", extra={"pdf_path": pdf_path})
    parser_result = await ParserAgent().run(parser_ctx)
    parsed = parser_result.output
    print(f"  title:        {parsed['title'][:80]!r}")
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

    if parsed.get("is_scanned") or not parsed["raw_text"].strip():
        print("  WARNING: Parser produced no usable text — aborting.")
        return 1

    # ── Step 2: Claim extractor ───────────────────────────────────────────────
    print("\n=== ClaimExtractorAgent ===")
    ctx = AgentContext(job_id="manual-test", extra={"parser_output": parsed})
    ext_result = await ClaimExtractorAgent().run(ctx)
    claims = ext_result.output.get("claims", [])

    if ext_result.status == "inconclusive":
        print(f"  WARNING: ClaimExtractorAgent returned inconclusive — {ext_result.error}")
    print(f"  status:     {ext_result.status}")
    print(f"  confidence: {ext_result.confidence}")
    print(f"  claims:     {len(claims)}")

    by_type: dict = {}
    for c in claims:
        by_type.setdefault(c["claim_type"], 0)
        by_type[c["claim_type"]] += 1
    for t, n in sorted(by_type.items()):
        print(f"    {t}: {n}")

    pipeline_output["extractor"] = {
        "status": ext_result.status,
        "total_claims": len(claims),
        "by_type": by_type,
        "claims": claims,
    }

    if not claims:
        print("  No claims extracted — aborting.")
        _save(pipeline_output, paper_hash)
        return 1

    # ── Step 3: DAG builder ───────────────────────────────────────────────────
    print("\n=== DAGBuilderAgent ===")
    dag_ctx = AgentContext(job_id="manual-test", extra={"claims": claims})
    dag_result = await DAGBuilderAgent().run(dag_ctx)

    if dag_result.status == "inconclusive":
        print(f"  WARNING: DAGBuilderAgent returned inconclusive — {dag_result.error}")
    print(f"  status:     {dag_result.status}")
    print(f"  confidence: {dag_result.confidence}")

    out = dag_result.output
    print(f"  edges:      {len(out['edges'])}")
    print(f"  roots:      {len(out['roots'])} — {out['roots']}")
    print(f"  topo order: {out['topological_order']}")

    pipeline_output["dag"] = {
        "status": dag_result.status,
        "edges": out["edges"],
        "adjacency": out["adjacency"],
        "roots": out["roots"],
        "topological_order": out["topological_order"],
    }

    # ── Claims in topological order (spec format) ─────────────────────────────
    print("\n=== Claims (topological order) ===")
    claim_map = {c["claim_id"]: c for c in claims}
    for cid in out["topological_order"]:
        c = claim_map.get(cid)
        if not c:
            continue
        snippet = c["text"][:80].replace("\n", " ")
        print(f"  {cid} ({c['claim_type']}): {snippet}...")

    # ── Save JSON output ──────────────────────────────────────────────────────
    _save(pipeline_output, paper_hash)

    ok = dag_result.status == "success" and ext_result.status in ("success", "inconclusive")
    return 0 if ok else 1


def _save(data: dict, paper_hash: str) -> None:
    out_dir = BACKEND / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{paper_hash}_pipeline.json"

    # Strip the live DAG object — not JSON-serialisable
    safe = json.loads(json.dumps(data, default=str))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2, ensure_ascii=False)
    print(f"\nPipeline output saved to {out_path}")


def main() -> int:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else str(BACKEND / "tests" / "fixtures" / "test_paper.pdf")
    return asyncio.run(run(pdf_path))


if __name__ == "__main__":
    sys.exit(main())
