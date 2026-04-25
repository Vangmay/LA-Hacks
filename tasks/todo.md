# PaperCourt v0.4 Revamp Resume Plan

## Goal
Finish the move from the legacy `ClaimUnit` pipeline to one centralized,
source-grounded `ResearchAtom` review pipeline:

`arXiv e-print source -> TeX assembly -> ParsedPaper -> ResearchAtom extraction -> ResearchGraph -> checks -> challenges -> rebuttals -> verdict cascade -> ReviewReport`

## Constraints From User
- TeX-first only for the implemented review path; no PDF/html fallback path.
- Remove legacy duplicate code instead of keeping fallback compatibility layers.
- Keep SymPy/SciPy concepts and current naming where already present, but wire
  them to `ResearchAtom`/`CheckResult`.
- Do not build out stubbed Reader/PoC/Research behavior except where imports
  must be kept healthy.
- Update `CLAUDE.md`, create/update `AGENTS.md`, and update README/design docs.
- Run thorough tests, including live end-to-end tests on the papers in
  `good_papers.txt`, and compare extracted atoms against actually reading the
  papers.

## Current Status Snapshot
- [x] New model surface exists: source, atoms, graph, evidence, checks, verdict,
  report, events, jobs.
- [x] arXiv ingestion moved to `backend/ingestion/arxiv.py`.
- [x] Deterministic parser moved to `backend/ingestion/tex_parser.py`.
- [x] New atom extractor, linkers, graph builder, checks, challenge/defense,
  verdict, cascade, and report modules are present.
- [ ] API/scripts/tests still contain stale imports from deleted legacy modules.
- [ ] Documentation still describes the legacy claim pipeline.
- [ ] End-to-end validation on `1706.03762` and `1312.6114` is not complete.

## Execution Plan
- [x] Fix import/model/API breakages from the `ClaimUnit` -> `ResearchAtom`
  migration.
- [x] Rewrite `backend/scripts/test_pipeline.py` as the live atom-pipeline E2E
  runner.
- [x] Rewrite `backend/scripts/test_review_tex_flow.py` as a no-network,
  no-OpenAI flow test for the new review orchestrator.
- [x] Run compile/import smoke checks and deterministic script tests.
- [x] Run live E2E on every paper in `good_papers.txt` with the configured
  OpenAI API key.
- [x] Inspect generated pipeline JSON for both papers and compare extracted
  atoms against the paper abstracts/main sections.
- [x] Update `CLAUDE.md`, `AGENTS.md`, README, and add `backend/REVAMP_NOTES.md`
  to describe the actual v0.4 design.
- [ ] Re-run verification after docs and record final results here.

## Review

### Commands run
- `PYTHONPATH=backend python -c "import main; import api.review; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; print('imports ok')"`
- `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `python backend/scripts/test_tex_ingestion.py`
- `python backend/scripts/test_tex_parser.py`
- `python backend/scripts/test_numeric.py`
- `python backend/scripts/test_dag_builder.py`
- `python backend/scripts/test_defender.py`
- `python backend/scripts/test_prompt_2_agents.py`
- `python backend/scripts/test_review_tex_flow.py`
- `python backend/scripts/test_pipeline.py --papers-file good_papers.txt`

### Live E2E outputs
- `backend/outputs/1312_6114_e7cf57effe2e2166_pipeline.json`
  - Parsed title: `Auto-Encoding Variational Bayes`
  - Parsed structure: 24 sections, 182 equations, 1 external bibliography command.
  - Extracted 23 atoms across algorithm/assertion/definition/example/limitation/proposition/related-work/technique.
  - Reviewed 9 reviewable atoms; summary: 8 contested, 1 likely flawed, 0 refuted.
  - Source grounding after linker fix: 3 atoms have equations, 12 atoms have citations/placeholders.
- `backend/outputs/1706_03762_24702db2b38f61e7_pipeline.json`
  - Parsed title: `Attention Is All You Need`
  - Parsed structure: 29 sections, 100 equations, 40 bibliography entries.
  - Extracted 23 atoms across assertion/construction/definition/open-problem/technique.
  - Reviewed 14 reviewable atoms; summary: 2 no-objection, 12 contested, 0 refuted.

### 1312.6114 comparison against paper
- Read the ar5iv HTML rendering of arXiv 1312.6114 and compared against the JSON output.
- Coverage is good for the core paper structure: introduction contributions,
  AEVB algorithm, problem scenario, variational bound, SGVB estimator,
  reparameterization trick, VAE example, related work, experimental lower-bound
  and marginal-likelihood claims, conclusion/future-work themes, and appendix
  Full VB / marginal-likelihood-estimator / Gaussian-estimator content.
- The paper is equation-heavy. The parser sees 182 equations, but atom-equation
  linking remains intentionally conservative. This avoids attaching unrelated
  equations to broad LLM atoms, but it means some mathematically central atoms
  still need better formula-level anchoring in a future pass.
- Bibliography parsing for 1312.6114 is limited because the TeX source uses an
  external bibliography command; citation keys are still captured as atom-level
  placeholders where section TeX contains cite commands.

### Remaining risks
- LLM atom extraction is nondeterministic; counts/types can vary between live runs.
- Formula-level extraction is now usable but not complete for math-heavy papers.
  A future improvement should extract equation-numbered propositions directly
  from nearby prose/equation blocks, especially for AEVB equations (1)-(10) and
  appendix equations (13)-(24).
- Live E2E depends on arXiv availability and the configured OpenAI model/key.
