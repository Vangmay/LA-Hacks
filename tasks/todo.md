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
