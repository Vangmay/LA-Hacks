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

---

# UI Demo Track

Goal: a working `/review/:jobId` page that demos the v0.4 atom pipeline end to
end. Backend is complete; the demo bottleneck is the frontend.

## Done

- Submit flow on Home: real input + "Review" button, calls
  `api.review.submit(arxivUrl)`, navigates to `/review/${job_id}` on success,
  renders inline error on failure. See `frontend/src/pages/Home.jsx`.
- Skeleton review page at `frontend/src/pages/Review.jsx`:
  - Header with job id, `status`, and `completed_atoms / total_atoms`.
  - Left pane: atom list from `GET /review/{id}/dag`, with status dot + type
    badge + importance + section. Click selects.
  - Center pane: placeholder showing atom/edge counts (DAG viz pending).
  - Right pane: detail view with type, status, label, section, source excerpt.
  - One-shot load via `Promise.all([api.review.status, api.review.dag])`.
- `App.jsx` routes `/review/:jobId` → `<Review />`.
- Vite proxy already forwards `/api` → `localhost:8000` (see
  `frontend/vite.config.js`); both routes return 200 in dev.

## Broken right now

- **`daisyui` is in `frontend/package.json` but missing from `node_modules`.**
  PostCSS errors at runtime: `Cannot find module 'daisyui'`. `tailwind.config.js`
  loads it via `require("daisyui")`. Fix is `npm install` inside `frontend/`
  (a fresh install picks it up from package.json) or remove daisyui from the
  config if we don't actually use any daisy classes. **Decide before next dev
  run.**

## Up next (in build order)

1. **Resolve daisyui.** Either install or strip from tailwind.config.js. We are
   not currently using any `daisy-*` classnames in `Home.jsx` or `Review.jsx`.
2. **SSE consumer in `Review.jsx`.** Open `api.review.stream(jobId)` in a
   `useEffect`, dispatch events into a reducer, update atom status in place.
   Event types to handle:
   - `ATOM_CREATED`, `EDGE_CREATED` — populate the graph live (currently we
     only see what `/dag` returned at mount).
   - `CHECK_STARTED` / `CHECK_COMPLETE` — flip atom status to `checking`, then
     show check kind + status + summary in the detail pane.
   - `CHALLENGE_ISSUED`, `REBUTTAL_ISSUED` — append to detail pane lists.
   - `VERDICT_EMITTED` — set final atom status; recolor list dot + node.
   - `CASCADE_TRIGGERED` — mark cascade-risk atoms with a distinct color.
   - `REPORT_READY` — enable a "View Report" affordance.
   - `JOB_COMPLETE`, `JOB_ERROR` — terminal UI states; close `EventSource`.
   Use `Last-Event-Id` for resume on reconnect (server already supports it,
   ported in d200762).
3. **DAG visualization in the center pane.** React Flow is in
   `CLAUDE.md`'s stated stack but **not yet in `package.json`** — `npm i
   reactflow` first. Map `dag.nodes` → React Flow nodes (color by verdict
   status from the SSE state), `dag.edges` → edges. Click a node ⇒ select it
   in the right pane (already wired by `selectedId`).
4. **Report drawer.** On `REPORT_READY`, fetch
   `api.review.reportMarkdown(jobId)` and render in a slide-over. A small
   markdown lib (`marked` or `react-markdown`) is fine; keep it minimal.
5. **Pre-warm for demo day.** Run both papers from `good_papers.txt` against
   the demo backend before going live, bookmark those `job_id`s as a fallback
   if a fresh run fails mid-talk.

## Explicitly skipping for the demo

- Source-grounding back into TeX (highlight `SourceSpan` in a TeX/PDF view).
  High effort, low marginal wow given the live DAG already tells the story.
- Persistence (`job_store` is in-process). A demo run survives a single
  process; that's enough.
- Idempotency on `/review/arxiv` (resubmits re-run the LLMs). Don't resubmit.
- Multi-variable numeric probe support.
- Reader / PoC / Research mode UIs. Stubs stay stubs.

## Files of interest

- `frontend/src/pages/Home.jsx` — submit flow (done).
- `frontend/src/pages/Review.jsx` — three-pane page (skeleton done, needs SSE +
  DAG + report drawer).
- `frontend/src/App.jsx` — routes.
- `frontend/src/api/client.js` — already has `review.stream`,
  `review.report`, `review.reportMarkdown` ready to use.
- `backend/core/orchestrators/review.py` — authoritative list of `DAGEvent`
  types the SSE consumer must handle; mirror it in the reducer.
- `backend/api/review.py` — SSE endpoint with `Last-Event-Id` replay + heartbeat.
