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
