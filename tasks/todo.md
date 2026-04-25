# TeX-First arXiv Backend Pipeline

## Plan

- [x] Read repo instructions, build prompts, PRD, current task notes, and latest non-scaffold commits.
- [x] Narrow scope to backend only after user correction; do not change frontend.
- [x] Chunk 1: replace arXiv ingestion utility with source archive fetch/extract/TeX bundle logic.
- [x] Verify chunk 1 with offline unit-style script tests and at least one real arXiv e-print fetch.
- [x] Commit chunk 1.
- [x] Chunk 2: add TeX parser agent that emits the existing parser contract.
- [x] Verify chunk 2 with local TeX fixtures and import checks.
- [x] Commit chunk 2.
- [x] Chunk 3: rewire review API and pipeline script to use arXiv URL/id -> TeX only.
- [x] Verify chunk 3 with mocked end-to-end pipeline and backend route checks.
- [ ] Commit chunk 3.
- [ ] Chunk 4: strengthen Prompt 2.1-2.4 agent tests around the new TeX path.
- [ ] Run full backend verification suite, including real arXiv URL smoke cases where network permits.
- [ ] Commit chunk 4.

## Specification

- User input is an arXiv URL or bare arXiv id. PDF upload and HTML fallback are not part of the new backend path.
- Accept common arXiv URL forms (`/abs/`, `/pdf/`, `/html/`) only to extract the arXiv id; always fetch `https://arxiv.org/e-print/{id}`.
- Save the downloaded source archive under the job directory, extract it safely, find the main `.tex`, and recursively inline local `\input{}` / `\include{}` files.
- Parser output must keep the existing shape: `title`, `abstract`, `sections`, `equations`, `bibliography`, `raw_text`, `is_scanned`.
- ClaimExtractorAgent and DAGBuilderAgent should continue consuming `parser_output` and `claims` unchanged.
- Prompt 2.1 through 2.4 agents should be tested with ClaimUnits produced from TeX parser output using mocked OpenAI clients; no tests should require real LLM calls.

## Review

- Chunk 1 verified with `python backend/scripts/test_tex_ingestion.py`.
- Chunk 1 live source fetch verified with `python backend/scripts/test_tex_ingestion.py --live https://arxiv.org/pdf/1706.03762 https://arxiv.org/abs/2103.00020`.
- Chunk 2 verified with `python backend/scripts/test_tex_parser.py`.
- Chunk 2 live parse verified with `python backend/scripts/test_tex_parser.py --live https://arxiv.org/pdf/1706.03762 https://arxiv.org/abs/2103.00020` and title fallback rechecked with `python backend/scripts/test_tex_parser.py --live https://arxiv.org/abs/2103.00020`.
- Chunk 3 verified with `backend/.venv/bin/python backend/scripts/test_review_tex_flow.py`.
- Chunk 3 syntax/import check verified with `backend/.venv/bin/python -m py_compile backend/api/review.py backend/core/orchestrators/review.py backend/scripts/test_pipeline.py backend/scripts/test_review_tex_flow.py backend/agents/dag_builder.py backend/agents/attacker.py backend/agents/counterexample_search.py backend/agents/citation_gap.py`.
