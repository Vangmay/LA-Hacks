# PaperCourt

Multi-agent system for engaging with research papers across four modes:
Review, Reader, PoC, and Research.

## Quick Start

```
cp backend/.env.example backend/.env
# Add your OPENAI_API_KEY to backend/.env

# Terminal 1 — Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev

# Verify
curl http://localhost:8000/health        # should return {"status": "ok"}
open http://localhost:5173               # should show PaperCourt landing page
```

## Who owns what

- **Person A**: `backend/models/`, `backend/core/`, and `backend/agents/{parser,claim_extractor,dag_builder}.py`
- **Person B**: `backend/agents/` (review agents), `backend/core/orchestrators/review.py`, `backend/api/review.py`
- **Person C**: `frontend/` (all of it)
- **Person D**: `backend/agents/` (poc agents), `backend/core/orchestrators/poc.py`, `backend/api/poc.py`

## Branch strategy

`main` is always runnable. Work on your own branch:

```
git checkout -b person-a/pipeline
```

Merge to main only when your feature works end-to-end. Never edit another
person's owned files without coordinating first.

## Verify scaffold

After installing both stacks, all six checks below must pass:

```
cd backend && uvicorn main:app --reload                       # no import errors
curl http://localhost:8000/health                              # {"status": "ok"}
curl http://localhost:8000/review/test-id/dag                  # {"nodes": [], "edges": []}
cd frontend && npm run dev                                     # page loads
python -c "from models import ClaimUnit, PoCSpec, ReviewReport; print('models ok')"
python -c "from agents.parser import ParserAgent; print(ParserAgent().agent_id)"
```
