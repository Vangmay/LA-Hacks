# PaperCourt

PaperCourt is a multi-agent research-paper review system. The implemented
review path is now source-grounded around `ResearchAtom`, not the older
`ClaimUnit` pipeline.

## Implemented Review Pipeline

```text
arXiv URL/id
  -> arXiv e-print source bundle
  -> assembled TeX
  -> ParsedPaper
  -> ResearchAtom extraction
  -> ResearchGraph dependency graph
  -> SymPy/SciPy/citation checks
  -> challenge + defense agents
  -> AtomVerdict cascade
  -> ReviewReport JSON + markdown
```

Reader, PoC, and Research mode routes still exist mostly as stubs.

## Quick Start

```bash
cp backend/.env.example backend/.env
# Add OPENAI_API_KEY to backend/.env for live review runs.

cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

cd ../frontend
npm install
npm run dev
```

Health check:

```bash
curl http://localhost:8000/health
```

Submit a review:

```bash
curl -X POST http://localhost:8000/review/arxiv \
  -H 'Content-Type: application/json' \
  -d '{"arxiv_url":"https://arxiv.org/abs/1706.03762"}'
```

## Review API

- `POST /review/arxiv` — JSON arXiv submission.
- `POST /review` — form field `arxiv_url`.
- `GET /review/{job_id}/status` — status plus atom progress.
- `GET /review/{job_id}/dag` — frontend graph snapshot.
- `GET /review/{job_id}/atoms/{atom_id}` — atom detail plus verdict.
- `GET /review/{job_id}/stream` — SSE `DAGEvent` stream.
- `GET /review/{job_id}/report` — completed `ReviewReport`.
- `GET /review/{job_id}/report/markdown` — markdown report.

## Verification

Offline checks:

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

Live end-to-end checks using `good_papers.txt`:

```bash
python backend/scripts/test_pipeline.py --papers-file good_papers.txt
```

Outputs are written to `backend/outputs/`.
