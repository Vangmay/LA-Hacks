# CLAUDE.md — PaperCourt

Read this before changing code in this repository.

## Current Implemented Design

PaperCourt v0.4 review mode is a TeX-first, source-grounded pipeline:

`arXiv URL/id -> e-print source bundle -> assembled TeX -> ParsedPaper -> ResearchAtom -> ResearchGraph -> CheckResult -> Challenge/Rebuttal -> AtomVerdict -> ReviewReport`

The old `ClaimUnit`, `ClaimExtractorAgent`, `DAGBuilderAgent`,
`TexParserAgent`, verifier-agent stack, and `utils.arxiv` path are removed.
Do not reintroduce compatibility fallbacks for those names.

## Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11, FastAPI, Pydantic v2, uvicorn |
| Async | asyncio, sse-starlette |
| LLM | OpenAI API via `openai.AsyncOpenAI` and `settings.openai_model` |
| TeX ingestion | arXiv e-print source download + safe TeX assembly |
| Parser | `backend/ingestion/tex_parser.py` |
| Symbolic check | SymPy service in `backend/checks/algebraic_sanity.py` |
| Numeric check | SciPy/NumPy service in `backend/checks/numeric_probe.py` |
| Frontend | React 18 + Vite, Tailwind CSS, React Flow |

## Backend Layout

```text
backend/
  ingestion/
    arxiv.py          # parse/fetch arXiv e-print source and assemble TeX
    tex_parser.py     # deterministic TeX -> ParsedPaper
  models/
    source.py         # PaperSource, ParsedPaper, SourceSpan, sections/equations/cites
    atoms.py          # ResearchAtom and atom taxonomy
    graph.py          # ResearchGraph and typed edge taxonomy
    checks.py         # CheckResult and check statuses
    adversarial.py    # Challenge and Rebuttal
    verdict.py        # AtomVerdict
    report.py         # ReviewReport
    events.py         # DAGEvent emitted over SSE
    jobs.py           # Review job metadata
  agents/
    atom_extractor.py
    graph_builder.py
    challenge_agent.py
    defense_agent.py
    verdict_aggregator.py
    cascade.py
    report_agent.py
  checks/
    algebraic_sanity.py
    numeric_probe.py
    citation_probe.py
  core/
    span_resolver.py
    equation_linker.py
    citation_linker.py
    event_bus.py
    job_store.py
    orchestrators/review.py
  api/review.py
```

Reader, PoC, and Research mode files are still mostly stubs. Keep their imports
healthy, but do not expand those modes unless the task explicitly asks for it.

## Core Conventions

- Import public models from `models`, not from individual model modules, unless
  there is a clear local reason.
- `AgentContext` uses `parsed_paper`, `atom`, `graph`, `checks`, `challenges`,
  and `rebuttals`. There is no `context.claim`.
- Deterministic services such as ingestion, parsing, linkers, and checks should
  stay as functions/services, not fake agents.
- Every review artifact should carry source grounding when possible:
  `SourceSpan`, `EquationBlock`, `CitationEntry`, or typed `Evidence`.
- Use `settings.openai_model`; do not hardcode model names in agents.
- LLM calls must use `AsyncOpenAI`, JSON mode when expecting structured output,
  and explicit parse/error handling.
- Keep the pipeline centralized. Do not add old-path fallback code that silently
  bypasses the v0.4 atom pipeline.

## Edge Direction

`ResearchGraph` follows the existing DAG convention:

`source_id -> target_id` means the source atom depends on the target atom.

Process roots first. If a target atom is refuted or likely flawed, dependent
source atoms are at cascade risk.

## Review API

- `POST /review/arxiv` with JSON `{ "arxiv_url": "https://arxiv.org/abs/..." }`
- `POST /review` with form field `arxiv_url`
- `GET /review/{job_id}/status`
- `GET /review/{job_id}/dag`
- `GET /review/{job_id}/atoms/{atom_id}`
- `GET /review/{job_id}/stream`
- `GET /review/{job_id}/report`
- `GET /review/{job_id}/report/markdown`

`/status` reports `completed_atoms` and `total_atoms`.

## Verification

Run these before calling a review-pipeline change done:

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

Live E2E with OpenAI and arXiv:

```bash
python backend/scripts/test_pipeline.py --papers-file good_papers.txt
```

Inspect the generated JSON files under `backend/outputs/` and compare atom
coverage against the paper text, especially atom types, sections, equations,
citations, graph roots, and high-risk verdicts.

## Local Run

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

cd ../frontend
npm install
npm run dev
```

## What Not To Do

- Do not resurrect deleted modules or model aliases for convenience.
- Do not add PDF/html fallback ingestion to the implemented review path.
- Do not use `time.sleep()` in async code.
- Do not import agents from models or APIs from agents/core.
- Do not make real OpenAI calls in offline tests; mock clients there.
- Do not commit `.env` or generated caches.
