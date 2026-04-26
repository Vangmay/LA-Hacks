# Branch Commit And Main Sync

## Goal
Commit the completed autoformalization/AXLE work on `vrathi101_axle` in small,
reviewable chunks, then merge the latest `main` and verify the branch still
works.

## Checklist
- [x] Inspect current branch changes and separate source, UI, docs, and
  generated artifacts.
- [x] Commit backend autoformalization service/API changes.
- [x] Commit frontend formalization UI changes.
- [x] Commit project documentation/task notes for the autoformalization work.
- [x] Fetch and merge latest `main`.
- [x] Resolve any merge conflicts with the smallest correct edits.
- [x] Run targeted backend/frontend verification after merge.
- [x] Commit merge/conflict-resolution follow-up if needed.
- [x] Record final commit IDs, verification, and residual notes.

## Review
- Chunk commits created before merging `main`:
  - `385e6da` Add AXLE formalization backend
  - `89d29f1` Add formalization panel UI
  - `5cd81ef` Document AXLE formalization workflow
- Merged `origin/main` into `vrathi101_axle`.
- Resolved conflicts by keeping both AXLE/formalization env settings and
  `main`'s deep-dive env settings, and by unioning additive task/lesson notes.
- Verification after merge:
  - `PYTHONPATH=backend python -c "import main; import api.review; import api.research; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; from formalization.api import router as _formalization_router; from research_deepdive.events import DeepDiveEvent; print('imports ok')"`
  - `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_formalization_api_offline.py`
  - `npm install` in `frontend/` to hydrate `main`'s merged `remark-gfm`
    dependency locally.
  - `npm run build` in `frontend/`
- Residual note: frontend build passes with Vite's existing large-chunk warning.

---

# AXLE Formalization Integration

## Goal
Implement the plan in `tasks/axle_integration_plan.md`: add an isolated
Formalize mode that reads completed review jobs, runs an OpenAI + AXLE
agentic loop per selected atom, streams progress over SSE, persists in-memory
run state, writes Lean artifacts, and mounts a frontend panel on the review
page.

## Implementation Checklist
- [x] Scaffold isolated backend package under `backend/formalization/`.
- [x] Add env-driven AXLE/formalization settings without changing review flow.
- [x] Add formalization models, event bus, store, and artifact outputs.
- [x] Add AXLE client wrapper and unit-testable toolbox dispatch.
- [x] Add context builder from `ParsedPaper`, `ResearchAtom`, and `ResearchGraph`.
- [x] Add prompts and OpenAI tool-call agent loop with capped iterations.
- [x] Add orchestrator and FastAPI router with run, atom, stream, and Lean endpoints.
- [x] Wire router in `backend/main.py` and append AXLE keys to `backend/.env.example`.
- [x] Add offline backend tests and live smoke/E2E scripts.
- [x] Scaffold frontend formalization feature folder.
- [x] Add frontend API, reducer, SSE hook, and focused UI components.
- [x] Mount `FormalizationPanel` in `frontend/src/pages/Review.jsx` with minimal conflict surface.
- [x] Run backend import/compile and formalization offline tests.
- [x] Run existing deterministic review tests.
- [x] Run frontend build.
- [x] Attempt live AXLE/OpenAI testing against arXiv `1312.6114` when keys/services permit.
- [x] Update documentation for the new Formalize mode.

## Review
- Implemented isolated backend Formalize mode in `backend/formalization/`:
  settings, AXLE wrapper, tool schemas/dispatch, models, store, SSE event bus,
  context builder, prompts, OpenAI tool-call agent loop, orchestrator, artifact
  output helpers, API router, and offline/live scripts.
- Implemented isolated frontend feature in `frontend/src/features/formalization/`
  and mounted `FormalizationPanel` inside the existing Review atom inspector.
- Added `core/sse.py` with a loop-safe SSE response and switched review/formalize
  streams to it after existing API tests exposed the `sse-starlette` global event
  loop issue.
- Pinned `httpx<0.28` because the installed Starlette `TestClient` is
  incompatible with `httpx 0.28+`.

### Commands run
- `python -m pip install axiom-axle`
- `python -m pip install 'httpx<0.28'`
- `PYTHONPATH=backend python -c "import main; import api.review; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; from formalization.api import router as _; print('imports ok')"`
- `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_formalization_api_offline.py`
- `python backend/scripts/test_tex_ingestion.py`
- `python backend/scripts/test_tex_parser.py`
- `python backend/scripts/test_numeric.py`
- `python backend/scripts/test_dag_builder.py`
- `python backend/scripts/test_defender.py`
- `python backend/scripts/test_prompt_2_agents.py`
- `python backend/scripts/test_review_tex_flow.py`
- `python backend/scripts/test_reader_agents.py`
- `python backend/scripts/test_reader_api.py`
- `python backend/scripts/test_review_api.py`
- `npm install` in `frontend/` to restore Rollup optional native deps.
- `npm run build` in `frontend/`
- `PYTHONPATH=backend python backend/formalization/scripts/test_axle_smoke.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_formalize_e2e.py --paper-id 1312.6114 --max-iterations 4 --max-axle-calls 4`
- `python backend/scripts/test_pipeline.py https://arxiv.org/pdf/1312.6114 --max-review-atoms 1`

### Live results
- AXLE smoke check passed on a tiny Lean `1 + 1 = 2` theorem.
- Formalization E2E on arXiv `1312.6114` built a VAE/ELBO atom, used OpenAI and
  AXLE, completed with label `formalized_only`, 4 tool calls, and 1 artifact.
  AXLE surfaced import/formal-statement issues during proof verification; the
  final verdict stayed conservative rather than claiming full verification.
- Capped review-pipeline run on `1312.6114` parsed `Auto-Encoding Variational
  Bayes`: 24 sections, 182 equations, 26 atoms, 11 graph edges; reviewed one
  reviewable atom and produced `CONTESTED`. Output JSON:
  `backend/outputs/1312_6114_e7cf57effe2e2166_pipeline.json`.

### Residual risks
- The formalization loop is intentionally capped for demos/tests; full paper
  verification can be slow and may end in `formalized_only` or `gave_up`.
- The merged Lean endpoint concatenates recorded artifacts for v1 instead of
  making an extra AXLE merge call on every download.

---

## Full-Paper Formalization E2E (post-integration)

### Goal
Run the formalization loop end-to-end on the *whole* VAE paper (every
formalization-eligible atom, not a single hand-built atom) and tighten the
agent + prompts based on the real failure modes.

### What we added
- New script `backend/formalization/scripts/test_formalize_full_paper.py`:
  fetches arXiv source → parse → run real `AtomExtractorAgent` and
  `GraphBuilderAgent` → stuff job into `job_store` → create a
  `FormalizationRun` over every theorem-/def-/assumption-/algorithm-shaped
  atom → subscribe to the formalization event bus → log live progress and
  save a per-atom JSON report under `backend/outputs/formalizations/_reports/`.
- Stronger anti-cheat rules in `backend/formalization/prompts.py`: the model
  is now forbidden from encoding atoms as `∃ x : Type, True`,
  `def isFoo := False; theorem ¬ isFoo`, `axiom + trivial`, and the
  `def x = expr; theorem x = expr := by rfl` rfl-tautology pattern that
  passed AXLE in early runs.
- Sturdier OpenAI rate-limit handling in `backend/formalization/agent.py`:
  retry budget bumped from 8 to 20 attempts, jittered backoff, and visible
  retry events on the SSE stream.

### Live runs on arXiv 1312.6114 (Auto-Encoding Variational Bayes)

Run 1 — parallelism=3, old prompt: 14 atoms in ~18m. 5 fully_verified,
4 formalized_only, 3 not_a_theorem, 2 formalization_failed (both pure OpenAI
429s, not Lean failures). Confirmed parallelism=3 collapses under the 30k TPM
cap.

Run 2 — parallelism=2, old prompt: 12 atoms in ~12m. 2 fully_verified,
1 formalized_only, 1 formalization_failed (Lean syntax cap, not 429),
8 not_a_theorem, 0 gave_up. **No rate-limit failures** — confirmed the
parallelism=2 + retry patch fixed the throughput problem. One of the
fully_verified atoms encoded the claim as `def x = expr; theorem x = expr := by rfl`,
which prompted the anti-cheat prompt rewrite.

Run 3 — parallelism=2, anti-cheat prompt: 8 atoms in ~10m. Final summary:
`{fully_verified: 1, formalized_only: 1, formalization_failed: 2,
not_a_theorem: 4, gave_up: 0}`. The lone fully_verified is atom_024 with a
real proof: defines `kl_divergence` as an integral and proves
`kl_divergence p q = 0 → elbo log_likelihood (kl_divergence p q) = log_likelihood`
via `unfold elbo; rw [h]; simp`. Crucially, atom_012 hit "isotropic
multivariate Gaussian not in current Mathlib" and *honestly* emitted
`not_a_theorem` instead of fabricating — exactly the desired behavior. Reports
under `backend/outputs/formalizations/_reports/1312_6114_*_full_paper.json`.

### Verification
- `PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_formalization_api_offline.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_axle_smoke.py`
- `PYTHONPATH=backend python backend/formalization/scripts/test_formalize_full_paper.py --paper-id 1312.6114 --parallelism 2`
  (×3, all completed without hanging or rate-limit kills)

### Residual notes
- AXLE verifies syntax, not semantic faithfulness. The anti-cheat prompt
  blocks the obvious cheats but cannot prevent every shallow encoding.
- LLM atom extraction is stochastic — count and types of reviewable atoms
  vary between runs (we saw 8/12/14 reviewable atoms across three runs of
  the same paper). Aggregate verdict numbers are noisy; per-atom Lean
  artifacts under `backend/outputs/formalizations/{run_id}/` are the
  authoritative output for a given run.

---

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

---

# Research Deep-Dive UI Plan

## Goal

Add a dedicated frontend research section, isolated under research-specific
folders, with two modes:

- Open existing end-to-end deep-dive runs from `backend/outputs/research_deepdives`.
- Start and watch a live visual research pipeline with reactive agent graph,
  persona details, tool-call trace, markdown artifacts, shared synthesis,
  critiques, and final report.

## Current Findings

- Backend research API is still stubbed in `backend/api/research.py`.
- Research orchestration exists in `backend/research_deepdive/`.
- Old run folders already contain enough structured artifacts for a rich UI:
  `README.md`, shared investigator plans, investigator/subagent folders,
  `taste.json`, markdown artifacts, `tool_calls.jsonl`, critique artifacts,
  and final reports.
- Frontend already uses React 18, Vite, Tailwind, React Flow, Dagre, and
  ReactMarkdown in review mode, so the research UI can reuse the same stack
  without adding new dependencies unless verification exposes a gap.

## Implementation Checklist

- [x] Re-ground old plan against current repo layout and lessons.
- [x] Add backend deep-dive event models and an in-process replaying event bus.
- [x] Instrument `DeepDiveOrchestrator` and `LiveAgentRunner` with optional
  event publication while keeping no-bus behavior unchanged.
- [x] Replace research API stubs with endpoints for run listing, old-run
  snapshots, run start, live status, SSE stream, artifact fetches, shared
  artifacts, critiques, and final report.
- [x] Add focused backend tests for snapshot extraction and event streaming
  without real model/API calls.
- [x] Add frontend research API client methods.
- [x] Build `/research` landing in `frontend/src/pages/research/` with clear
  mode selection: open old run or start live run.
- [x] Build `/research/:runId` under `frontend/src/pages/research/` and
  `frontend/src/components/research/` with graph, inspector, timeline,
  persona card, artifacts, papers/tool trace, shared artifacts, critiques, and
  final markdown report.
- [x] Integrate the research route into `App.jsx` and Home navigation without
  disturbing existing review/reader pages.
- [x] Verify with backend import/compile checks, research script tests, frontend
  build, and browser-level smoke tests against an old run and a live dry run.

## Design Constraints

- Keep frontend additions in research-specific subfolders to avoid conflicts.
- Prefer existing visual language: dark operational UI, compact panels,
  restrained neon accents, React Flow graph canvas, and markdown rendering.
- Live UI should be useful even when connected late: replay event history and
  hydrate from disk snapshots.
- Old completed/partial runs must remain browsable after server restart by
  reading disk artifacts, not relying on an in-memory event buffer.
- Do not make real OpenAI calls in automated tests.

## Review

### Implemented

- Backend:
  - Added `research_deepdive/events.py` and `event_bus.py`.
  - Added `research_deepdive/snapshots.py` for disk-backed old-run snapshots.
  - Replaced `backend/api/research.py` stubs with run listing, start, status,
    snapshot, SSE stream, artifact, report, shared, and critique endpoints.
  - Added optional live event publication to `DeepDiveOrchestrator` and
    `LiveAgentRunner`.
- Frontend:
  - Added `/research` and `/research/:runId` routes.
  - Added isolated research pages/components under `frontend/src/pages/research`
    and `frontend/src/components/research`.
  - Added graph canvas, inspector drawer, persona/tool/artifact panels, event
    ticker, old-run browser, and live-run start form.
  - Added `api.research.*` client methods and Home navigation.
  - Added `remark-gfm` so deep-dive markdown tables render correctly.

### Verification

- `PYTHONPATH=backend python -c "import main; import api.review; import api.research; from research_deepdive.events import DeepDiveEvent; from research_deepdive.snapshots import build_run_snapshot; print('imports ok')"`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `PYTHONPATH=backend python backend/scripts/test_research_deepdive.py`
- FastAPI TestClient checked `/research/runs`, `/research/{run_id}/snapshot`,
  and `/research/{run_id}/report` against `live_gemma_mvp_20260425_codex_r7`.
- `npm run build`
- Playwright desktop smoke:
  - `/research` rendered 28 old-run cards.
  - `/research/live_gemma_mvp_20260425_codex_r7` rendered 22 graph nodes,
    424 tool events, and findings markdown.
- Playwright mobile smoke:
  - `/research/live_gemma_mvp_20260425_codex_r7` rendered the graph with no
    console errors at 390x844.
- Live dry-run API smoke:
  - Started `ui_dry_smoke_20260426` with one investigator/subagent in
    `dry_run` mode.
  - Status reached `completed`, with final report available.

### Notes

- Existing servers are reachable at backend `http://127.0.0.1:8000` and
  frontend `http://localhost:5173`.
- The production build emits Vite's usual large-chunk warning because the app
  includes React Flow and markdown rendering in the main bundle.
