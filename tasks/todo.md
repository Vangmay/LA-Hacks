# Formalization Snapshot Atom Metadata Debug

## Goal
Fix why Autoformalization atom Overview and Context tabs can show dashes for
type, importance, queue, section, and context counts even after tool calls are
visible for that atom.

## Checklist
- [x] Trace Overview and Context tab fields to frontend reducer state.
- [x] Trace reducer fields back to backend formalization events and snapshots.
- [x] Add a focused regression that reproduces the missing snapshot metadata.
- [x] Persist atom display metadata and context summary in the backend run
  snapshot.
- [x] Hydrate frontend context from persisted snapshot data.
- [x] Run targeted backend and frontend verification.

## Review
- Root cause: Overview fields (`text`, `atom_type`, `importance`, queue
  position) and Context fields were only carried by live SSE events
  (`atom_queued`, `atom_context_built`). The persisted formalization run
  snapshot kept status, tool calls, artifacts, and verdicts, but not the atom
  display metadata or context summary. A late connection, refresh, or dashboard
  reopen could therefore show tool calls while Overview/Context stayed blank.
- Fix: `AtomFormalization` now stores atom display metadata and a
  `context_summary`. The orchestrator writes the queued atom payload and context
  summary into the store before publishing their events. The frontend hydrates
  `atom.context` from `context_summary` when a run snapshot is loaded.
- Regression: `test_formalization_run_snapshot_keeps_atom_metadata` reproduces
  the stale/late snapshot path with a fake agent and asserts the snapshot keeps
  type, importance, queue, section, context counts, and TeX/prose char counts.
- Verification:
  - `PYTHONPATH=backend python backend/formalization/scripts/test_formalization_api_offline.py`
  - `PYTHONPATH=backend python -c "import main; from formalization.api import router as _formalization_router; from formalization.models import AtomFormalization; print('imports ok')"`
  - `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py`
  - `python backend/scripts/test_atom_candidate_cleanup.py`
  - `python backend/scripts/test_review_api.py`
  - `python backend/scripts/test_review_tex_flow.py`
  - `npm run build` in `frontend/`

---

# AXLE Import Error Debug

## Goal
Explain why Formalization can report `axiom-axle is not installed` even when
the package appears installed locally.

## Checklist
- [x] Locate the code path that raises the `axiom-axle is not installed` error.
- [x] Check whether the current shell Python can import `axle.AxleClient`.
- [x] Check whether a live backend process is running under a different
  interpreter or checkout.
- [x] Distinguish Gemma model/tool-calling behavior from local AXLE tool
  execution.

## Review
- The error is raised locally in `backend/formalization/axle_client.py` when the
  backend executes an AXLE tool and cannot import `from axle import AxleClient`.
- In the current shell, `/opt/anaconda3/bin/python` can import
  `axle.AxleClient`, and `python -m pip show axiom-axle` reports version
  `1.2.0` installed in `/opt/anaconda3/lib/python3.11/site-packages`.
- No uvicorn/Vite server is currently listening, so the live backend interpreter
  could not be inspected. If the error came from an older run, it can also be
  stale state from before the package was installed or before the backend was
  restarted.
- Gemma does not install or host AXLE. Gemma emits tool calls; the FastAPI
  backend executes those tool calls through the local `axiom-axle` Python
  client.

---

# Transient Algorithm Caption Nodes Debug

## Goal
Explain and fix why the Review graph briefly shows the same two VAE-looking
algorithm caption nodes regardless of the paper submitted.

## Checklist
- [x] Locate where `caption Minibatch...` and `caption Pseudocode...` enter the
  graph data.
- [x] Add or run a focused reproduction check before changing behavior.
- [x] Identify whether this is stale job state, frontend state reuse, parser
  noise, or event ordering.
- [x] Apply the smallest root-cause fix if needed.
- [x] Run targeted verification.

## Review
- Root cause: the two nodes are raw `algorithm` environment candidates from the
  VAE paper source, not meaningful review atoms. The TeX contains those exact
  captions in algorithm blocks, and the extractor was publishing deterministic
  candidates to the live graph before the local cleanup pass removed them from
  the final atom set.
- Secondary UI issue: the Review page kept prior reducer state until the next
  job loaded, so stale nodes from a previous job could briefly flash when
  navigating between jobs.
- Fix: filter deterministic and batched progress candidates with the same local
  candidate cleanup used for final atoms, drop raw caption/algorithmic LaTeX
  candidates, publish the final atom list with `atom_extraction_complete`, and
  make the frontend reconcile to that final atom list while resetting state on
  `jobId` changes.
- Verification:
  - `python backend/scripts/test_atom_candidate_cleanup.py`
  - `PYTHONPATH=backend python -c "import main; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; print('imports ok')"`
  - `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
  - `python backend/scripts/test_review_tex_flow.py`
  - `python backend/scripts/test_review_api.py`
  - `npm run build` in `frontend/`

---

# Review Atom Formalize Button Debug

## Goal
Find why completed Review atoms do not show the Lean/Formalize controls in the
atom detail view, then fix the smallest wiring or rendering bug if the feature
is present but unreachable.

## Checklist
- [x] Review relevant existing lessons before changing code.
- [x] Trace frontend Review atom selection/detail rendering.
- [x] Trace frontend FormalizationPanel conditions, API paths, and button text.
- [x] Trace backend formalization router mounting and route compatibility.
- [x] Reproduce or statically prove why the button is absent in the user path.
- [x] Apply the smallest correct fix if this is a product bug.
- [x] Run targeted verification.

## Review
- Root cause: the currently running local servers are from the sibling checkout
  `/Users/vedantrathi/Desktop/LA-Hacks`, not this repo
  `/Users/vedantrathi/Desktop/LA-Hacks-2`.
- The live Vite server on `localhost:5173` serves a `Review.jsx` that contains
  `Atom statement` and `Review Thread` but not `FormalizationPanel`,
  `AXLE Verification`, or `Run selected`.
- The live backend on `localhost:8000` exposes `/review` routes but no
  `/formalize` routes in `openapi.json`.
- In this repo, `frontend/src/pages/Review.jsx` imports and mounts
  `FormalizationPanel` for every selected atom, and `backend/main.py` mounts
  the formalization router at `/formalize`.
- No product-code patch was needed for `LA-Hacks-2`; the fix is to run the
  frontend and backend from this checkout or merge these changes into the
  checkout currently serving `localhost`.
- Verification:
  - `curl -s http://localhost:5173/src/pages/Review.jsx | rg ...` proved the
    live Vite server was serving a Review page without formalization controls.
  - `python` route inspection against the `LA-Hacks-2` app found
    `/formalize/{job_id}`, `/formalize/{job_id}/atom/{atom_id}`,
    `/formalize/runs/{run_id}`, `/formalize/runs/{run_id}/stream`, and
    `/formalize/runs/{run_id}/lean`.
  - `rg` confirmed `FormalizationPanel` is mounted in `Review.jsx` and exposes
    `AXLE Verification`, `Run selected`, and `Run reviewable`.
  - `npm install` was needed once because `LA-Hacks-2/frontend/node_modules`
    was missing declared packages; then `npm run build` passed with the existing
    large-chunk warning.

---

# Pull Main And Commit Formalization Dashboard

## Goal
Sync `vrathi101_axle` with the latest `origin/main`, preserve the clean Lean
formalization live dashboard work, resolve any conflicts, verify, and commit the
final branch state.

## Checklist
- [x] Stash current local formalization/dashboard edits.
- [x] Fetch and merge latest `origin/main`.
- [x] Reapply local edits and resolve conflicts if needed.
- [x] Run targeted backend/frontend verification.
- [x] Commit the final synced changes.

## Review
- Fetched `origin/main` and merged it into `vrathi101_axle`; Git completed the
  merge without textual conflicts.
- Reapplied the local formalization dashboard work cleanly after the merge.
- Verified after merge:
  - `PYTHONPATH=backend python -c "import main; import api.review; import api.research; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; from formalization.api import router as _formalization_router; print('imports ok')"`
  - `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_formalization_api_offline.py`
  - `npm run build` in `frontend/`
- Residual note: frontend build passes with Vite's existing large-chunk warning.

---

# Lean Formalization Live UI

## Goal
Rebuild Formalize mode into a clean, observable Lean/AXLE agent experience that
matches the high-level live deep-research UI style: visible run topology,
parallel atom progress, model/tool activity, Lean artifacts, AXLE feedback, and
high tool-call/runtime limits using the same Gemma thinking profile conventions
as deep research where the local code supports it.

## Checklist
- [x] Inspect deep-research live UI, model routing, tool limits, and concurrency
  patterns.
- [x] Inspect current formalization API/events/store/frontend state shape.
- [x] Update formalization config/runtime defaults for Gemma thinking and much
  higher iteration/tool-call budgets while preserving bounded concurrency.
- [x] Add any missing event payloads needed for frontend observability.
- [x] Rework formalization frontend into an organized live dashboard for run
  overview, atom parallelism, stream timeline, AXLE calls, and Lean artifacts.
- [x] Run backend import/compile/formalization offline tests.
- [x] Run frontend build.

## Review
- Backend formalization remains isolated under `backend/formalization/`.
  Defaults now mirror the deep-dive Gemma thinking profile:
  `gemma-4-26b-a4b-it`, `GEMMA_API_KEY`, Google OpenAI-compatible base URL,
  high reasoning effort, 32k output tokens, 20 model retries, and deep-dive
  parallelism defaults for atom workers / AXLE concurrency.
- Formalization SSE now starts with a run snapshot and includes runtime
  metadata, atom queue details, context summaries, model/iteration deltas,
  Lean artifact code, tool durations, and artifact status updates after AXLE
  checks / proof verification.
- Frontend formalization UI stays under `frontend/src/features/formalization/`.
  The compact Review sidebar panel now opens a full live dashboard with a
  React Flow atom-agent graph, run/atom inspector, tool timeline, model thought
  stream, context panel, Lean artifact viewer, and bottom activity ticker.
- Verification:
  - `PYTHONPATH=backend python -c "import main; import api.review; import api.research; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; from formalization.api import router as _formalization_router; print('imports ok')"`
  - `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py`
  - `PYTHONPATH=backend python backend/formalization/scripts/test_formalization_api_offline.py`
  - `npm run build` in `frontend/`
- Frontend build still emits the existing Vite large chunk warning.

---

# AXLE Pipeline Explanation

## Goal
Explain the latest AXLE commits and trace how Formalize mode works end to end
from completed review job to frontend stream and Lean artifact output.

## Checklist
- [ ] Review latest branch commits and identify the AXLE-specific changes.
- [ ] Trace backend API, orchestrator, agent, AXLE toolbox, store, events, and
  outputs.
- [ ] Trace frontend formalization panel, API calls, SSE reducer, and atom UI.
- [ ] Summarize the full pipeline with concrete file references.

## Review
- Pending.

---

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

# Main Merge And Commit Plan

## Goal

Bring `atom-candidate-clean-dag` up to date with `main`, resolve conflicts
without losing local work, verify the branch, and create a clean commit.

## Checklist

- [x] Inspect current dirty worktree and separate intended files from generated
  outputs/scratch artifacts.
- [x] Fetch latest `main`.
- [x] Preserve local changes safely before merging.
- [x] Merge `main` into the branch and resolve conflicts if any.
- [x] Run focused verification after the merge.
- [x] Commit the intended code/docs changes.
- [x] Document final commit and verification.

## Review

### Implemented

- Fetched `origin/main` and fast-forward merged it into
  `atom-candidate-clean-dag`.
- Reapplied local atom/DAG/OpenRouter/UI work with no merge conflicts.
- Excluded generated output JSONs and transient lockfile churn from the commit.
- Fixed the newly pulled persistent job-store JSON serialization issue for
  datetimes/enums and corrupted cache recovery.

### Verification

- `PYTHONPATH=backend python -c "import main; import api.review; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport, AtomCandidate; print('imports ok')"`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `PYTHONPATH=backend python backend/scripts/test_atom_candidate_cleanup.py`
- `PYTHONPATH=backend python backend/scripts/test_edge_candidates.py`
- `PYTHONPATH=backend python backend/scripts/test_graph_validators.py`
- `PYTHONPATH=backend python backend/scripts/test_prompt_2_agents.py`
- `PYTHONPATH=backend python backend/scripts/test_dag_builder.py`
- `PYTHONPATH=backend python backend/scripts/test_review_tex_flow.py`
- `PYTHONPATH=backend python backend/scripts/test_job_store.py`
- `npm install`
- `npm run build`
- `git diff --check`

# PoC Scaffold Atom-Grounded Prompt Plan

## Goal

Make PoC scaffold generation implement the selected atom directly, not a broad
or adjacent paper method. Use a scaffold-specific model profile that defaults to
the Gemma high-thinking configuration and make the prompt explicit enough that
algorithm atoms become minimal algorithm implementations.

## Checklist

- [x] Confirm branch and worktree state before editing.
- [x] Review the current scaffold prompt, model routing, and PoC context passed
  into scaffold generation.
- [x] Add a scaffold-specific model/config path that can use Gemma high
  thinking without changing the global review model.
- [x] Rewrite scaffold prompts to require atom-local implementation,
  source-grounded comments, no markdown fences, and minimal scope.
- [x] Improve context selection so the selected atom's source excerpt and
  surrounding section are prioritized over generic first sections.
- [x] Add focused tests for prompt contents/model routing and markdown-fence
  cleanup.
- [x] Run verification and document results.

## Review

### Implemented

- Added PoC scaffold-specific model settings in `backend/config.py`, defaulting
  to the Gemma high-thinking OpenAI-compatible profile.
- Reworked `ScaffoldGeneratorAgent` so implementation and test prompts are
  selected-atom-first, include the atom source excerpt, forbid broad/generic
  adjacent implementations, and explicitly call out the VAE estimator failure
  mode.
- Prioritized context from the atom's own section/source excerpt instead of
  blindly using the first five parsed sections.
- Stripped markdown code fences from generated Python and requirements files
  before syntax validation/package output.
- Added an offline mocked regression script covering prompt contents, model
  routing, reasoning effort, selected-section context, and fence cleanup.

### Verification

- `PYTHONPATH=backend python backend/scripts/test_poc_scaffold_generator.py`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend/poc/agents/scaffold_generator.py backend/scripts/test_poc_scaffold_generator.py backend/config.py`
- `PYTHONPATH=backend python -c "import main; import api.poc; from poc.agents.scaffold_generator import ScaffoldGeneratorAgent; print('imports ok')"`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `git diff --check -- backend/config.py backend/poc/agents/scaffold_generator.py backend/scripts/test_poc_scaffold_generator.py tasks/todo.md`

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

# Atom Candidate Clean DAG Plan

## Goal

Keep `tex_parser.py` as the provenance/source-map layer, then make review DAG
atoms cleaner by introducing an internal candidate stage, strict grounding,
deterministic edge candidates, and graph validators before finalization.

## Checklist

- [x] Confirm branch/worktree state and avoid unrelated edits.
- [x] Inspect current atom extraction, graph builder, source grounding, and
  focused test scripts.
- [x] Add an internal `AtomCandidate` layer without changing `tex_parser.py`.
- [x] Rewrite atom extraction to produce candidates, enforce grounding, run a
  critic/repair pass, dedupe, then emit final `ResearchAtom` objects.
- [x] Add deterministic edge candidate generation.
- [x] Add graph edge validation and conservative repair/drop logic.
- [x] Refactor `GraphBuilderAgent` so the LLM classifies candidate edges rather
  than inventing edges from scratch.
- [x] Add focused offline tests for grounding, dedupe, candidate edges,
  validators, and cycle handling.
- [x] Run offline verification.
- [x] Run live pipeline checks for `1706.03762` and `1312.6114` using the
  configured local `.env` without printing secrets.
- [x] Review generated atom/graph outputs critically and document results.

## Notes

- Do not touch `backend/ingestion/tex_parser.py` except for unrelated bug fixes;
  none are planned for this task.
- Preserve current public `ResearchAtom` shape where practical so existing
  review/reader/PoC code remains healthy.

## Review

### Implemented

- Kept `backend/ingestion/tex_parser.py` unchanged.
- Added `AtomCandidate` and reviewability/checkability metadata.
- Reworked `AtomExtractorAgent` into candidate extraction, span resolution,
  optional quote repair, critic cleanup, dedupe, final `ResearchAtom`
  conversion, and header normalization.
- Added OpenRouter config/client support through `OPENROUTER_API_KEY`,
  `OPENROUTER_MODEL`, headers, and base URL. With OpenRouter configured and no
  explicit `OPENAI_MODEL`, the active model is `google/gemini-3-flash-preview`.
- Added JSON repair for LaTeX-heavy model outputs and listed `json-repair` in
  backend requirements.
- Added deterministic edge candidates and graph validators for type, direction,
  low confidence, weak dependency rationales, and cycles.
- Refactored `GraphBuilderAgent` so the LLM classifies proposed candidates
  instead of inventing edges from all atom pairs.
- Added `--skip-reader-probe` to `test_pipeline.py` for low-call extraction and
  graph smoke tests.

### Verification

- `PYTHONPATH=backend python -c "import main; import api.review; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport, AtomCandidate; print('imports ok')"`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `PYTHONPATH=backend python backend/scripts/test_tex_ingestion.py`
- `PYTHONPATH=backend python backend/scripts/test_tex_parser.py`
- `PYTHONPATH=backend python backend/scripts/test_numeric.py`
- `PYTHONPATH=backend python backend/scripts/test_dag_builder.py`
- `PYTHONPATH=backend python backend/scripts/test_defender.py`
- `PYTHONPATH=backend python backend/scripts/test_prompt_2_agents.py`
- `PYTHONPATH=backend python backend/scripts/test_review_tex_flow.py`
- `PYTHONPATH=backend python backend/scripts/test_atom_candidate_cleanup.py`
- `PYTHONPATH=backend python backend/scripts/test_edge_candidates.py`
- `PYTHONPATH=backend python backend/scripts/test_graph_validators.py`
- `git diff --check`

### Live Checks

- OpenRouter preflight returned valid JSON with `google/gemini-3-flash-preview`.
- `1706.03762` extraction/graph smoke:
  - command used test-only `MAX_PARALLEL_CLAIMS=1`, `--max-review-atoms 0`,
    and `--skip-reader-probe`.
  - result: 20 atoms, 11 graph edges, 0 graph warnings.
  - critical note: coverage is now much better than the first overly strict
    8-atom run. Some checkability labels are still imperfect but not blocking.
- `1312.6114` extraction/graph smoke:
  - command used the same test-only low-call settings.
  - result after JSON repair: 15 atoms, 4 graph edges in the saved pipeline
    output.
  - final graph-only check after validator tightening dropped weak
    duplicate/reiteration dependency rationales; VAE graph over saved atoms
    produced 5 edges with 1 expected weak-rationale warning before the final
    `supports` marker tightening.

### Residual Notes

- Generated output JSONs under `backend/outputs/` were produced/updated by the
  live checks and should be treated as test artifacts, not core code.
- The VAE paper still has lower atom coverage than Transformer because several
  candidates are dropped by strict span grounding. This is preferable to
  allowing ungrounded DAG nodes, but future quote-repair can be improved.

## Header Grammar Bugfix

### Checklist

- [x] Add a regression test for dangling generated atom headers such as headers
  ending in `because`.
- [x] Harden final atom header filtering so bad headers cannot survive LLM
  normalization failure or missing decisions.
- [x] Run focused extractor tests.

### Verification

- `PYTHONPATH=backend python backend/scripts/test_atom_candidate_cleanup.py`
- `PYTHONPATH=backend python backend/scripts/test_prompt_2_agents.py`
- `PYTHONPATH=backend python -m py_compile backend/agents/atom_extractor.py backend/scripts/test_atom_candidate_cleanup.py`

## Full English Atom Display Plan

### Checklist

- [x] Stop cropping stored atom display text in backend cleanup.
- [x] Require LLM atom display statements to be clean English with no raw LaTeX.
- [x] Reject raw-LaTeX or dangling display text locally.
- [x] Keep graph/list labels compact in the UI but make the selected atom
  statement expandable in the inspector.
- [x] Add focused tests for long non-cropped English and raw-LaTeX rejection.
- [x] Run focused backend/frontend verification.

### Verification

- `PYTHONPATH=backend python backend/scripts/test_atom_candidate_cleanup.py`
- `PYTHONPATH=backend python backend/scripts/test_prompt_2_agents.py`
- `PYTHONPATH=backend python -m py_compile backend/agents/atom_extractor.py backend/core/orchestrators/review.py backend/scripts/test_atom_candidate_cleanup.py`
- `npm install`
- `npm run build`
