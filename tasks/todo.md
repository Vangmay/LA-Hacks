# Research Deep-Dive Live Provider And E2E Plan

## Goal

Make the deep-dive pipeline usable end to end with clean model-role routing:

- thinking model for Director, Investigator, Critique, Revision, and
  Finalization work;
- lightweight model for search subagents, extraction helpers, formatting,
  dedupe, and metadata classification;
- OpenAI and Gemini/Gemma through an OpenAI-compatible client where possible;
- monitored live execution with high configurable budgets and no silent fallback
  behavior that hides provider/tool bugs.

## Constraints

- Keep all counts, model names, provider URLs, timeout values, and tool-call
  budgets configurable.
- Keep changes scoped to the deep-dive subsystem, shared settings, tests, docs,
  and task notes.
- Do not disturb the implemented v0.4 review pipeline or reintroduce removed
  compatibility paths.
- Fail loudly on invalid model/tool/provider configuration; do not silently
  downgrade to another model or skip failed live stages.

## Plan

- [x] Record the correction in `tasks/lessons.md`.
- [x] Verify official Gemini/Gemma OpenAI-compatible API details against Google
  docs and document the supported assumptions.
- [x] Inspect current deep-dive scaffold for the smallest clean live execution
  boundary.
- [x] Add configurable model profiles for thinking and lightweight agent roles.
- [x] Add an OpenAI-compatible provider factory that supports both OpenAI and
  Gemini/Gemma via configured API key and base URL.
- [x] Expose role-to-model mapping in prompts, logs, run metadata, and tests.
- [x] Implement monitored live search-subagent execution with tool-call loop,
  per-agent markdown memory writes, and strict budget accounting.
- [x] Implement enough real research tools for one arXiv E2E: Semantic Scholar
  resolve, references, citations, bulk/relevance search, SPECTER2 batch ranking,
  and workspace read/write/append.
- [x] Run focused smoke tests and full offline review regression checks.
- [x] Run live E2E with small budgets and iterate on provider/tool/schema issues.
- [x] Commit changes in coherent chunks.

## Review

### Commands run

- `PYTHONPATH=backend python -c "import main; import api.review; import api.research; import research_deepdive; from research_deepdive import DeepDiveOrchestrator, DeepDiveConfig, DeepDiveLLMProvider; print('imports ok')"`
- `python backend/scripts/test_research_deepdive.py`
- `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `python backend/scripts/test_tex_ingestion.py`
- `python backend/scripts/test_tex_parser.py`
- `python backend/scripts/test_numeric.py`
- `python backend/scripts/test_dag_builder.py`
- `python backend/scripts/test_defender.py`
- `python backend/scripts/test_prompt_2_agents.py`
- `python backend/scripts/test_review_tex_flow.py`
- `PYTHONPATH=backend python backend/scripts/run_research_deepdive_live.py --arxiv-url https://arxiv.org/abs/1706.03762 --section "Architecture" --max-investigators 1 --subagents-per-investigator 1 --subagent-tool-calls 3 --subagent-steps 5 --parallel-subagents 1 --semantic-scholar-interval 8 --semantic-scholar-retries 6 --timeout-seconds 1800`
- `PYTHONPATH=backend python backend/scripts/run_research_deepdive_live.py --arxiv-url https://arxiv.org/abs/1706.03762 --section "Architecture" --max-investigators 1 --subagents-per-investigator 1 --subagent-tool-calls 1 --subagent-steps 2 --parallel-subagents 1 --semantic-scholar-interval 8 --semantic-scholar-retries 6 --timeout-seconds 900`

### Results

- Import smoke passed.
- Research deep-dive smoke test passed.
- Backend compileall passed.
- Offline review-pipeline script checks passed.
- Gemini/Gemma OpenAI-compatible light model call succeeded after normalizing
  provider-visible `<thought>` wrappers.
- Direct Semantic Scholar resolve/references/citations worked under slow pacing;
  anonymous Semantic Scholar search still hit HTTP 429.
- Tiny live deep-dive E2E succeeded with workspace traces, markdown memory,
  subagent handoff, investigator synthesis, critique artifacts, and final report.

### Follow-up risks

- A high-budget 3-investigator/9-subagent run should wait until
  `SEMANTIC_SCHOLAR_API_KEY` is configured. Anonymous Semantic Scholar traffic
  rate-limits too aggressively for honest high-budget literature search.
- SerpApi live checks were not exercised because no `SERPAPI_API_KEY` is
  configured.
