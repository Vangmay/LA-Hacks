# Extensive Deep-Dive Report Prompt Refinement

## Goal

Ensure the research deep-dive final report and critique artifacts are extensive, organized, and synthesis-heavy rather than short summaries. The finalizer should combine all investigator, subagent, and critique ideas into a deep report, especially for `novelty_ideation` where spinoff proposals are the main product.

## Constraints

- Keep depth controls configurable, not hidden magic constants.
- Keep changes scoped to the deep-dive subsystem, runner, tests, and task notes.
- Do not disturb the v0.4 review pipeline.
- Preserve uncertainty and evidence discipline; extensive does not mean padded or hallucinated.
- Make critique artifacts substantial and useful, not one-line pass/fail summaries.

## Plan

- [x] Inspect current finalizer and critique prompts for depth constraints or missing detail requirements.
- [x] Add configurable report-depth settings for finalization and critique.
- [x] Thread depth specs into finalizer and critique prompts.
- [x] Update prompts to require extensive, structured synthesis, proposal details, critique integration, and evidence/risk matrices.
- [x] Add runner flags for depth-related settings.
- [x] Add smoke coverage that finalizer/critic prompts include extensiveness requirements.
- [x] Run focused and review-regression verification.
- [x] Document results and commit.

## Review

### What changed

- Added configurable depth settings:
  - `DEEPDIVE_REPORT_DETAIL_LEVEL`
  - `DEEPDIVE_FINAL_REPORT_MIN_SPINOFF_PROPOSALS`
  - `DEEPDIVE_FINAL_REPORT_MIN_EVIDENCE_ITEMS_PER_PROPOSAL`
  - `DEEPDIVE_FINAL_REPORT_MIN_OPEN_QUESTIONS`
  - `DEEPDIVE_CRITIQUE_MIN_POINTS_PER_LENS`
- Added matching live-runner flags:
  - `--report-detail-level`
  - `--min-spinoff-proposals`
  - `--min-evidence-items-per-proposal`
  - `--min-open-questions`
  - `--critique-min-points`
- Finalizer prompt now has an explicit `Report Depth Contract`.
- Critique prompt now has an explicit `Critique Depth Contract`.
- Novelty final reports now require extensive spinoff proposal structure:
  title, novelty claim, mechanism, closest-prior/future collision risks,
  evidence, validation path, falsification criteria, contribution type, and
  confidence.
- Literature-review reports are also forced to be extensive, but by expanding
  evidence coverage, contradictions, bucket comparisons, and search plans
  instead of inventing proposals.

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

All listed checks passed.
