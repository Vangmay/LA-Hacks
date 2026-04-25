# Research Deep-Dive Commit And Completion Plan

## Goal

Commit the completed deep-dive scaffold in clean chunks, then address the two
requested design gaps:

- integrate the expanded `personas.py` library with configurable, zone-aware,
  complementary persona selection;
- expand the agent-visible tool contracts so prompts include complete Semantic
  Scholar, SPECTER2, SerpApi, derived-analysis, and workspace tool specs.

## Constraints

- Commit only scoped deep-dive/config/test/task files; leave unrelated generated
  outputs and unrelated untracked files alone.
- Keep budgets and counts configurable, including persona selection bounds.
- Preserve the existing review pipeline imports and do not reintroduce removed
  v0.4 compatibility paths.
- Avoid live OpenAI/Semantic Scholar/SerpApi calls in offline tests.

## Plan

- [x] Record the correction in `tasks/lessons.md`.
- [x] Inspect the expanded persona library without rewriting it wholesale.
- [x] Add configurable persona diversity settings.
- [x] Update persona generation to use zone hints and complementary coverage
  rather than cycling through the first archetypes.
- [x] Update investigator/subagent prompts to explain dynamic archetype choice
  with flexible diversity requirements.
- [x] Expand tool registry and shared tool prompt docs with exact I/O and example
  usage for the full planned research surface.
- [x] Update smoke tests for persona diversity and required tool coverage.
- [x] Run import, smoke, and compile verification.
- [x] Commit changes in coherent chunks.

## Review

### Commands run

- `PYTHONPATH=backend python -c "import main; import api.review; import api.research; import research_deepdive; from research_deepdive import DeepDiveOrchestrator, DeepDiveConfig; print('imports ok')"`
- `python backend/scripts/test_research_deepdive.py`
- `python -m compileall -q -x 'backend/.venv|backend/outputs' backend`
- `python backend/scripts/test_tex_ingestion.py`
- `python backend/scripts/test_tex_parser.py`
- `python backend/scripts/test_numeric.py`
- `python backend/scripts/test_dag_builder.py`
- `python backend/scripts/test_defender.py`
- `python backend/scripts/test_prompt_2_agents.py`
- `python backend/scripts/test_review_tex_flow.py`

### Results

- Import smoke passed.
- Research deep-dive smoke test passed.
- Backend compileall passed.
- Offline review-pipeline script checks passed.

### Follow-up risks

- Live Semantic Scholar, SerpApi, and OpenAI execution still needs to be wired
  behind the now-expanded tool contracts.
- The deterministic persona planner is a scaffold for live investigator-driven
  persona generation; live mode should preserve the same config bounds and
  complementarity guarantees.
