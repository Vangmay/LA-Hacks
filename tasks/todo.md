# Research Deep-Dive Objective Mode Refinement

## Goal

Make the deep-dive pipeline explicit about the difference between:

- `literature_review`: exhaustive evidence collection, bucketed synthesis, critique, and next searches;
- `novelty_ideation`: literature review plus concrete spinoff novelty proposals, where novelty generation is the final product and the literature review is the evidence base.

## Constraints

- Keep execution mode (`dry_run` vs `live`) separate from research objective.
- Do not disturb the v0.4 review pipeline.
- Keep changes scoped to `backend/research_deepdive`, the live runner CLI, task notes, and tests.
- Avoid making weak speculative proposals look evidence-backed.
- Preserve configurability and prompt clarity.

## Plan

- [x] Inspect current request models, orchestration, prompts, and tests for mode/objective ambiguity.
- [x] Add a clean objective field to the deep-dive request model.
- [x] Thread objective text through investigator, subagent, critique, cross-investigator, and finalizer prompts.
- [x] Make finalizer output requirements differ clearly between literature-review and novelty-ideation objectives.
- [x] Add CLI support for selecting objective.
- [x] Add smoke coverage for objective propagation and prompt content.
- [x] Run focused deep-dive tests and review-pipeline regression checks.
- [x] Document the result and commit the prompt/code refinement.

## Review

### What changed

- Added `DeepDiveRunRequest.research_objective` with values
  `novelty_ideation` and `literature_review`.
- Kept `mode` as execution mode only: `dry_run` or `live`.
- Default objective is `novelty_ideation`, matching the intended PaperCourt
  research pipeline.
- Added `--objective novelty_ideation|literature_review` to the live runner.
- Threaded objective directives into investigator, subagent, critique, shared
  tool, cross-investigator, and finalizer stages.
- Finalizer now has objective-specific report sections:
  - `novelty_ideation`: includes `Spinoff novelty proposals` and
    `Proposal triage matrix`.
  - `literature_review`: suppresses proposal invention and emphasizes coverage,
    evidence quality, and next searches.

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
