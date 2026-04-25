# AGENTS.md — PaperCourt

## Workflow

- For non-trivial work, write and maintain a checklist in `tasks/todo.md`.
- Keep changes scoped to the requested area and the current v0.4 design.
- If a test or assumption fails, stop, update the plan, and fix the root cause
  before continuing.
- Record final verification results in `tasks/todo.md`.

## Current Code Design

The implemented review path is:

`arXiv source -> assembled TeX -> ParsedPaper -> ResearchAtom -> ResearchGraph -> CheckResult -> Challenge/Rebuttal -> AtomVerdict -> ReviewReport`

Do not reintroduce the removed `ClaimUnit` pipeline or old modules such as
`agents.claim_extractor`, `agents.dag_builder`, `agents.tex_parser`,
`agents.symbolic_verifier`, `agents.numeric_adversary`, `agents.attacker`,
`agents.defender`, or `utils.arxiv`.

## Testing Standard

Before marking review-pipeline work complete, run:

```bash
PYTHONPATH=backend python -c "import main; import api.review; from models import ResearchAtom, ParsedPaper, AtomVerdict, ReviewReport; print('imports ok')"
python -m compileall -q -x 'backend/.venv|backend/outputs' backend
python backend/scripts/test_tex_ingestion.py
python backend/scripts/test_tex_parser.py
python backend/scripts/test_numeric.py
python backend/scripts/test_dag_builder.py
python backend/scripts/test_defender.py
python backend/scripts/test_prompt_2_agents.py
python backend/scripts/test_review_tex_flow.py
```

For extraction quality work, also run:

```bash
python backend/scripts/test_pipeline.py --papers-file good_papers.txt
```

Then inspect the generated `backend/outputs/*_pipeline.json` files and compare
the extracted atoms against the actual paper text.

## Documentation

When changing the pipeline contract, update:

- `CLAUDE.md`
- `AGENTS.md`
- `README.md`
- `backend/REVAMP_NOTES.md`
- `tasks/todo.md`

Use `tasks/lessons.md` only after a user correction identifies a repeatable
mistake pattern.
