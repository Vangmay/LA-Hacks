"""End-to-end smoke test: PDF -> ParserAgent -> ClaimExtractorAgent.

Usage (from backend/):
    .venv/bin/python scripts/test_pipeline.py [path/to/paper.pdf]

Defaults to tests/fixtures/test_paper.pdf. Requires OPENAI_API_KEY in
backend/.env. Makes a real API call (typically $0.05-$0.15).
"""
import asyncio
import os
import sys
from pathlib import Path

# Allow running as `python scripts/test_pipeline.py` from backend/.
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext
from agents.claim_extractor import ClaimExtractorAgent
from agents.parser import parse_pdf
from config import settings


def main() -> int:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else str(BACKEND / "tests" / "fixtures" / "test_paper.pdf")

    if not os.path.isfile(pdf_path):
        print(f"PDF not found: {pdf_path}")
        print("Download the test paper with:")
        print("  wget -q https://arxiv.org/pdf/1706.03762 -O backend/tests/fixtures/test_paper.pdf")
        return 1

    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set. Add it to backend/.env and re-run.")
        return 1

    print(f"=== ParserAgent ({pdf_path}) ===")
    parsed = parse_pdf(pdf_path)
    print(f"  title:        {parsed['title'][:80]!r}")
    print(f"  sections:     {len(parsed['sections'])}")
    print(f"  equations:    {len(parsed['equations'])}")
    print(f"  bibliography: {len(parsed['bibliography'])}")
    print(f"  raw_text:     {len(parsed['raw_text'])} chars")
    print(f"  is_scanned:   {parsed['is_scanned']}")

    if parsed["is_scanned"] or not parsed["raw_text"].strip():
        print("\nParser produced no usable text — skipping extractor.")
        return 1

    print("\n=== ClaimExtractorAgent ===")
    ctx = AgentContext(job_id="manual-test", extra={"parser_output": parsed})
    result = asyncio.run(ClaimExtractorAgent().run(ctx))
    print(f"  status:       {result.status}")
    print(f"  confidence:   {result.confidence}")
    print(f"  claims:       {len(result.output['claims'])}")
    if result.error:
        print(f"  error:        {result.error}")

    print("\n=== Claims ===")
    for c in result.output["claims"]:
        print(
            f"  [{c['claim_id']}] type={c['claim_type']:<11} "
            f"sec={(c['section'] or '-')[:25]:<25} "
            f"eqs={c['equations']} cites={c['citations']}"
        )
        print(f"      {c['text'][:140]}")

    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
