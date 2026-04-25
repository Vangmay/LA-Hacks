# Live 9-Personality Research Deep-Dive Test

## Goal

Run an actual live end-to-end research deep-dive with 3 investigator zones and 9 total search subagents/personas, using the configured Semantic Scholar API key and a strict below-1-rps Semantic Scholar pace. SerpAPI is available but must be capped to at most 50 requests for the run and used sparingly.

## Constraints

- Do not fake agent execution or replace it with dry-run artifacts.
- Keep Semantic Scholar under the approved cumulative rate limit: 1 request per second across endpoints.
- Run the 9 subagents concurrently at the orchestration layer while preserving the shared Semantic Scholar request pace.
- Enforce a hard SerpAPI cap in code before the live run.
- Monitor generated workspaces, tool traces, markdown memory, handoffs, critiques, and final report.
- If the run exposes a real bug, stop, fix the root cause, verify, then rerun.

## Plan

- [x] Add/configure a hard per-run SerpAPI request budget.
- [x] Verify configured keys are visible without printing secrets.
- [x] Run preflight smoke checks for imports and deep-dive test coverage.
- [x] Launch the live run with 3 investigators, 3 subagents each, and 9-way subagent concurrency.
- [x] Monitor live trace output and generated markdown memory while the run is executing.
- [x] Inspect all 9 subagent workspaces for tool calls, handoffs, and non-empty memory.
- [x] Inspect investigator synthesis, critique artifacts, and final report.
- [x] Run post-run verification checks.
- [x] Document results and commit any code/config/test changes from this run.

## Review

### Live run outcome

- Successful run id: `live_9agents_20260425_r11_final`.
- Command used thinking-profile routing for search subagents because the
  non-thinking Gemma/OpenAI-compatible path repeatedly emitted malformed or
  truncated JSON actions under large markdown writes.
- Workspace:
  `backend/outputs/research_deepdives/live_9agents_20260425_r11_final`.
- Final report:
  `backend/outputs/research_deepdives/live_9agents_20260425_r11_final/final/research_deep_dive_report.md`.

### Artifact counts

- Subagent traces: 9.
- Subagent handoffs: 9.
- Investigator syntheses: 3.
- Critique files: 4.
- Final report bytes: 5413.
- Tool errors in successful run: 0.

### Successful-run tool counts

- `read_workspace_markdown`: 9.
- `resolve_arxiv_paper`: 9.
- `get_citations`: 6.
- `get_references`: 6.
- `batch_get_papers`: 3.
- `append_workspace_markdown`: 12.
- `google_scholar_search`: 0 in the successful run; prior monitored attempts
  used at most 2, below the 50 request cap.

### Iterations from real failures

- Added hard SerpAPI per-run budget enforcement.
- Added `SERP_API_KEY` alias support for the existing local env naming.
- Simplified the live action protocol to use `action=<tool_name>` because the
  previous `action=tool/tool_name=...` split caused repeated model errors.
- Added provider-level pacing/retry handling for Gemma/OpenAI-compatible and
  OpenAI 429s.
- Moved Semantic Scholar bulk-search field selection into the runtime because
  `tldr` is unsupported on `/paper/search/bulk`.
- Normalized unsupported bulk `sort=relevance` to omitted sort because the API
  only accepts `paperId`, `publicationDate`, or `citationCount`.

### Verification commands

- `PYTHONPATH=backend python -c "import main; import api.review; import api.research; import research_deepdive; from research_deepdive import DeepDiveOrchestrator, DeepDiveConfig, DeepDiveLLMProvider; print('imports ok')"`
- `python backend/scripts/test_research_deepdive.py`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `python backend/scripts/test_tex_ingestion.py`
- `python backend/scripts/test_tex_parser.py`
- `python backend/scripts/test_numeric.py`
- `python backend/scripts/test_dag_builder.py`
- `python backend/scripts/test_defender.py`
- `python backend/scripts/test_prompt_2_agents.py`
- `python backend/scripts/test_review_tex_flow.py`
- `git diff --check`

All listed checks passed.
