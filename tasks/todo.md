# Gemini 3.1 Pro Deep-Dive E2E

## Goal

Route the research deep-dive pipeline through `gemini-3.1-pro-preview` instead
of Gemma, using high reasoning for director/investigator/critique/revision/
finalization roles and medium reasoning for search/tool-heavy agents. Then run
an actual novelty-ideation E2E on `Attention Is All You Need` and inspect that
the final output contains substantive spinoff novelty proposals.

## Constraints

- Keep model names, reasoning effort, budgets, rate limits, and agent counts
  configurable.
- Do not disturb the v0.4 review pipeline.
- Do not commit `.env`, generated caches, or live output artifacts.
- Respect Semantic Scholar's 1 request/second keyed limit.
- Keep SerpAPI usage sparse; this test should primarily use Semantic Scholar.
- Do not fake the run or substitute dry-run artifacts.

## Plan

- [x] Inspect current deep-dive model routing, config defaults, and CLI flags.
- [x] Change defaults/config wiring so Gemini 3.1 Pro is the configured provider
  for both thinking and search roles, with role-specific reasoning effort.
- [x] Update tests/docs/examples that assert or document model routing.
- [x] Run focused offline verification.
- [ ] Run the live novelty-ideation E2E on `Attention Is All You Need` with 3
  investigator zones and 9 total search personalities.
- [ ] Inspect logs, tool traces, and final report for API/tool failures and
  actual spinoff novelty proposals.
- [x] Document verification results and commit code changes only.

## Review

### What changed

- Deep-dive defaults now route both thinking and light/search profiles through
  Google's OpenAI-compatible Gemini endpoint using `GEMINI_API_KEY`.
- Thinking roles default to `gemini-3.1-pro-preview` with
  `reasoning_effort=high`.
- Search/tool-heavy roles default to `gemini-3.1-pro-preview` with
  `reasoning_effort=medium`.
- The live runner now exposes explicit profile override flags for provider,
  model, API-key env var, base URL, reasoning effort, and profile pacing.
- Reasoning effort is sent through `extra_body` so the current installed
  `openai` package can pass the field without requiring a newer typed SDK
  signature.
- Env examples and model-routing docs now describe Gemini 3.1 Pro as the
  default deep-dive model path.

### Verification commands

- `python backend/scripts/test_research_deepdive.py`
- `PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `PYTHONPATH=backend python -c "import main; import api.review; import api.research; import research_deepdive; from research_deepdive import DeepDiveOrchestrator, DeepDiveConfig, DeepDiveRunRequest; print('imports ok')"`
- `python backend/scripts/test_tex_ingestion.py`
- `python backend/scripts/test_tex_parser.py`
- `python backend/scripts/test_numeric.py`
- `python backend/scripts/test_dag_builder.py`
- `python backend/scripts/test_defender.py`
- `python backend/scripts/test_prompt_2_agents.py`
- `python backend/scripts/test_review_tex_flow.py`
- `git diff --check`

All listed offline checks passed.

### Live E2E status

The live Gemini preflight reached Google successfully but returned `429
RESOURCE_EXHAUSTED` before any deep-dive run could start. The response reported
free-tier request and input-token quota limits of `0` for `gemini-3.1-pro`.
Because the requested E2E must not be faked or substituted with Gemma, the
actual 9-personality novelty-ideation run is blocked until the configured
Google project/key has quota for `gemini-3.1-pro-preview`.
