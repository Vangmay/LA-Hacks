"""End-to-end pipeline test: paper -> Parser -> ClaimExtractor -> DAGBuilder -> SymbolicVerifier -> Attacker.

Usage (from backend/):
    .venv/bin/python scripts/test_pipeline.py [path/to/paper.pdf | arxiv-url-or-id]

Examples:
    .venv/bin/python scripts/test_pipeline.py tests/fixtures/test_paper.pdf
    .venv/bin/python scripts/test_pipeline.py https://arxiv.org/abs/1706.03762
    .venv/bin/python scripts/test_pipeline.py 1706.03762

Defaults to tests/fixtures/test_paper.pdf. Requires OPENAI_API_KEY in
backend/.env. Makes real API calls (typically $0.05-$0.20).

Output JSON saved to outputs/{paper_hash}_pipeline.json.
"""
import asyncio
import hashlib
import json
import os
import sys
import tempfile
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
from agents.html_parser import HtmlParserAgent
from agents.symbolic_verifier import SymbolicVerifierAgent
from agents.attacker import AttackerAgent
from models import ClaimUnit
from config import settings
from utils.arxiv import fetch_paper, parse_arxiv_url


def _resolve_input(arg: str):
    """Returns ('pdf', path) or ('html', html_text) or raises."""
    ref = parse_arxiv_url(arg)
    if ref is not None:
        print(f"=== Fetching arXiv {ref.canonical} ===")
        with tempfile.TemporaryDirectory() as tmp:
            fetched = asyncio.run(fetch_paper(ref, tmp))
            if fetched.html_text:
                print(f"  html source: {fetched.html_source_url}")
                return ("html", fetched.html_text)
            if fetched.pdf_path:
                # html unavailable — copy the PDF out of the tempdir so the
                # caller can still read it after the with-block exits.
                dest = Path(tempfile.mkdtemp()) / Path(fetched.pdf_path).name
                Path(fetched.pdf_path).rename(dest)
                print(f"  no HTML; using PDF at {dest}")
                return ("pdf", str(dest))
        raise RuntimeError("arxiv fetch produced neither html nor pdf")
    if os.path.isfile(arg):
        return ("pdf", arg)
    raise FileNotFoundError(f"not a PDF and not an arXiv URL: {arg}")


def _paper_hash(kind: str, source: str) -> str:
    if kind == "pdf":
        with open(source, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:12]
    return hashlib.md5(source.encode("utf-8")).hexdigest()[:12]


async def run(kind: str, source: str) -> int:
    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set. Add it to backend/.env and re-run.")
        return 1

    paper_hash = _paper_hash(kind, source)
    pipeline_output: dict = {"paper_hash": paper_hash}

    # ── Step 1: Parser ────────────────────────────────────────────────────────
    if kind == "html":
        print("\n=== HtmlParserAgent ===")
        parser_ctx = AgentContext(job_id="manual-test", extra={"html_text": source})
        parser_result = await HtmlParserAgent().run(parser_ctx)
    else:
        print(f"\n=== ParserAgent ({source}) ===")
        parser_ctx = AgentContext(job_id="manual-test", extra={"pdf_path": source})
        parser_result = await ParserAgent().run(parser_ctx)

    if parser_result.status != "success":
        print(f"  parser status={parser_result.status} error={parser_result.error}")
        return 1
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

    # ── Equation matching (link parser equations to claims by proximity) ───────
    eq_list = parsed.get("equations", [])  # [{"id", "latex", "section"}]
    raw_text = parsed.get("raw_text", "")
    if eq_list:
        for claim in claims:
            claim_pos = raw_text.find(claim["text"][:50])
            matched_latex = []
            for eq in eq_list:
                eq_pos = raw_text.find(eq["latex"][:30])
                if eq_pos != -1 and claim_pos != -1 and abs(eq_pos - claim_pos) < 600:
                    matched_latex.append(eq["latex"])
            if matched_latex:
                claim["equations"] = matched_latex

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

    # ── Step 4: Symbolic verifier (per claim, in parallel) ───────────────────
    print("\n=== SymbolicVerifierAgent ===")
    verifier = SymbolicVerifierAgent()
    sym_tasks = []
    for c in claims:
        claim_unit = ClaimUnit.model_validate(c)
        sym_ctx = AgentContext(job_id="manual-test", claim=claim_unit)
        sym_tasks.append(verifier.run(sym_ctx))

    sym_results = await asyncio.gather(*sym_tasks, return_exceptions=True)

    sym_output = {}
    for c, result in zip(claims, sym_results):
        cid = c["claim_id"]
        if isinstance(result, Exception):
            print(f"  WARNING: {cid} raised exception — {result}")
            sym_output[cid] = {"status": "error", "evidence": str(result)}
            continue
        if result.status == "inconclusive":
            print(f"  WARNING: {cid} returned inconclusive — {result.output.get('evidence')}")
        o = result.output
        sym_output[cid] = o
        badge = {"passed": "✓", "failed": "✗", "inconclusive": "?"}.get(o["status"], "?")
        print(f"  {badge} {cid}: {o['status']} (conf={o['confidence']}) — {o['evidence'][:80]}")

    pipeline_output["symbolic_verifier"] = sym_output

    # ── Step 5: Attacker (per claim, in parallel) ────────────────────────────
    print("\n=== AttackerAgent ===")
    attacker = AttackerAgent()
    atk_tasks = []
    for c, sym_res in zip(claims, sym_results):
        claim_unit = ClaimUnit.model_validate(c)
        sym_out = sym_res.output if not isinstance(sym_res, Exception) else {}
        atk_ctx = AgentContext(
            job_id="manual-test",
            claim=claim_unit,
            extra={"verification_results": [sym_out] if sym_out else []},
        )
        atk_tasks.append(attacker.run(atk_ctx))

    atk_results = await asyncio.gather(*atk_tasks, return_exceptions=True)

    atk_output = {}
    for c, result in zip(claims, atk_results):
        cid = c["claim_id"]
        if isinstance(result, Exception):
            print(f"  WARNING: {cid} raised exception — {result}")
            atk_output[cid] = {"challenges": []}
            continue
        challenges = result.output.get("challenges", [])
        atk_output[cid] = {"challenges": challenges}
        print(f"  {cid}: {len(challenges)} challenge(s)")
        for ch in challenges:
            print(f"    [{ch['attacker_agent']}] {ch['challenge_text'][:100]}")

    pipeline_output["attacker"] = atk_output

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
    arg = sys.argv[1] if len(sys.argv) > 1 else str(
        BACKEND / "tests" / "fixtures" / "test_paper.pdf"
    )
    try:
        kind, source = _resolve_input(arg)
    except Exception as e:
        print(f"Could not resolve input: {e}")
        print("Download the test paper with:")
        print("  wget -q https://arxiv.org/pdf/1706.03762 -O backend/tests/fixtures/test_paper.pdf")
        return 1
    return asyncio.run(run(kind, source))


if __name__ == "__main__":
    sys.exit(main())
