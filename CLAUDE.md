# CLAUDE.md — PaperCourt

This file tells Claude Code how to work in this repository.
Read it fully before touching any file.

---

## What This Project Is

PaperCourt is a multi-agent system for engaging with research papers across four modes:

- **Review Mode** — adversarial attacker/defender agents verify each claim in a paper, cascade failures through a dependency DAG, produce a verdict report
- **Reader Mode** — per-claim explanations, prerequisite mapping, exercises, Socratic tutor
- **PoC Mode** — filters empirically testable claims, generates runnable implementation scaffolds, ingests experiment results, produces a reproducibility report
- **Research Mode** — autonomous literature retrieval, knowledge graph construction, gap detection, hypothesis generation, self-review loop

All four modes share one backend pipeline: arXiv URL/id → e-print source bundle → TexParserAgent → ClaimExtractorAgent → DAGBuilderAgent → mode-specific agents.

The live DAG is the primary UI — nodes update in real time via SSE as agents run.

---

## Stack

| Layer                 | Technology                                                 |
| --------------------- | ---------------------------------------------------------- |
| Backend               | Python 3.11, FastAPI, Pydantic v2, uvicorn                 |
| Async                 | asyncio, asyncio.gather, sse-starlette                     |
| LLM                   | OpenAI API (gpt-4o) via `openai.AsyncOpenAI`               |
| TeX ingestion         | arXiv e-print source download + safe TeX assembly          |
| Symbolic verification | SymPy                                                      |
| Numeric verification  | SciPy, NumPy                                               |
| Embeddings            | sentence-transformers (all-MiniLM-L6-v2)                   |
| Vector store          | ChromaDB                                                   |
| Graph                 | NetworkX                                                   |
| Frontend              | React 18 + Vite, Tailwind CSS, React Flow, React Router v6 |
| SSE client            | Native browser EventSource API                             |

---

## Directory Structure and Ownership

```
papercourt/
├── backend/
│   ├── main.py              # FastAPI app, mounts all routers — do not restructure
│   ├── config.py            # Settings via pydantic-settings, loads .env
│   ├── models/              # Pydantic models — Person A owns, everyone imports
│   ├── agents/
│   │   ├── base.py          # BaseAgent, AgentContext, AgentResult — do not modify without coordinating
│   │   ├── tex_parser.py    # Person A
│   │   ├── claim_extractor.py  # Person A
│   │   ├── dag_builder.py   # Person A
│   │   ├── symbolic_verifier.py  # Person B
│   │   ├── numeric_adversary.py  # Person B
│   │   ├── rag_retrieval.py      # Person B
│   │   ├── attacker.py           # Person B
│   │   ├── counterexample_search.py  # Person B
│   │   ├── citation_gap.py       # Person B
│   │   ├── defender.py           # Person B
│   │   ├── verdict_aggregator.py # Person B
│   │   ├── cascade.py            # Person B
│   │   ├── report_agent.py       # Person B
│   │   ├── claim_filter.py       # Person D
│   │   ├── metric_extractor.py   # Person D
│   │   ├── scaffold_generator.py # Person D
│   │   ├── results_analyzer.py   # Person D
│   │   └── reproducibility_report.py  # Person D
│   ├── core/
│   │   ├── dag.py           # Person A — used by everyone, do not break its interface
│   │   ├── event_bus.py     # Person A — singleton, import as `from core.event_bus import event_bus`
│   │   ├── job_store.py     # Person A — singleton, import as `from core.job_store import job_store`
│   │   └── orchestrators/
│   │       ├── review.py    # Person B
│   │       ├── poc.py       # Person D
│   │       ├── reader.py    # stub
│   │       └── research.py  # stub
│   └── api/
│       ├── review.py        # Person B
│       ├── poc.py           # Person D
│       ├── reader.py        # stub
│       └── research.py      # stub
└── frontend/                # Person C owns everything here
    └── src/
        └── api/
            └── client.js    # single source of truth for all API calls
```

---

## Core Conventions

### Agents

Every agent inherits from `BaseAgent` and implements one method:

```python
async def run(self, context: AgentContext) -> AgentResult:
```

- `context.job_id` — always present
- `context.claim` — the `ClaimUnit` being processed (None for orchestrator-level agents)
- `context.extra` — dict for mode-specific data (tier results, challenges, etc.)

`AgentResult` fields: `agent_id`, `claim_id`, `status`, `output`, `confidence`, `error`.

**Rules:**

- Never raise exceptions inside `run()`. Catch all errors, return `status="error"` with the error message.
- Never return `status="error"` AND raise. Pick one.
- `output` must always be a dict that matches the agent's documented output shape, even on error (use empty/default values).
- `confidence` is always a float in [0, 1].
- Stubs must return `self._mock_result(...)` with a valid output shape — never `NotImplementedError`.

### Models

- Import from `models` directly: `from models import ClaimUnit, AgentResult`
- Never import from a sub-module like `from models.claim import ClaimUnit` in agent files — use the re-exported `__init__.py`
- All models are Pydantic v2. Use `model_validate()` not `parse_obj()`. Use `model_dump()` not `dict()`.
- No bare `dict` or `Any` in model fields except `extra: dict` in `AgentContext` and `payload: dict` in `DAGEvent`.

### OpenAI Calls

Always use the async client. Never use the sync client — it blocks the event loop.

```python
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)
```

Standard call pattern:

```python
response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    response_format={"type": "json_object"},  # always request JSON
    max_tokens=1000,
)
raw = response.choices[0].message.content
```

Always wrap in try/except. Always parse JSON with a fallback:

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    # retry once with stricter prompt, then return inconclusive
```

Never hardcode `gpt-4o` as a string — use `settings.openai_model` (add it to config if not present).

### Parallelism

Use `asyncio.gather` for parallel agent execution. Never use `threading`. Never call `asyncio.run()` inside an async function.

```python
# Correct pattern for parallel per-claim agents
results = await asyncio.gather(
    symbolic_verifier.run(ctx),
    numeric_adversary.run(ctx),
    rag_retrieval.run(ctx),
    return_exceptions=True,  # always — don't let one failure kill the gather
)
# Filter out exceptions and handle them
```

# Use PydanticAI for structured outputs inside agent run() methods

from pydantic_ai import Agent as PydanticAgent

# Define at class level, not inside run() — avoid re-instantiating on every call

class AttackerAgent(BaseAgent):
agent_id = "attacker"
\_llm = PydanticAgent(
'openai:gpt-4o',
result_type=list[Challenge],
system_prompt="You are a hostile peer reviewer..."
)

    async def run(self, context: AgentContext) -> AgentResult:
        result = await self._llm.run(context.claim.text)
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=context.claim.claim_id,
            status="success",
            output={"challenges": [c.model_dump() for c in result.data]},
            confidence=0.8,
        )

### SSE Events

Emit a `DAGEvent` via the event bus at every meaningful state transition. Do not batch events — emit immediately.

```python
from core.event_bus import event_bus
from models import DAGEvent, DAGEventType
import uuid
from datetime import datetime

await event_bus.publish(job_id, DAGEvent(
    event_id=str(uuid.uuid4()),
    job_id=job_id,
    event_type=DAGEventType.VERDICT_EMITTED,
    claim_id=claim.claim_id,
    payload={"verdict": verdict.verdict, "confidence": verdict.confidence},
    timestamp=datetime.utcnow(),
))
```

### API Routes

- All routes use the FastAPI `APIRouter`, never the app directly.
- All routes return Pydantic models or dicts — never raw strings except for markdown endpoints.
- Background tasks use `asyncio.create_task()`, not FastAPI's `BackgroundTasks`.
- SSE endpoints use `sse_starlette.sse.EventSourceResponse`.
- All routes have explicit error handling: 404 for not found, 202 for in-progress, 500 only for unexpected errors.

```python
from fastapi import APIRouter, HTTPException
router = APIRouter()

@router.get("/{job_id}/report")
async def get_report(job_id: str):
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = job_store.get(job_id)
    if job["status"] != "complete":
        raise HTTPException(status_code=202, detail="Review in progress")
    return job["report"]
```

### Frontend API Calls

**Never** hardcode API URLs in components. Always import from `src/api/client.js`:

```js
import { api } from "../api/client";

const dag = await api.review.dag(jobId);
const stream = api.review.stream(jobId); // returns EventSource
```

---

## What Not To Do

- **Do not** use `time.sleep()` anywhere. Use `asyncio.sleep()`.
- **Do not** import from `agents/` in `models/`. Models have zero dependencies on agents.
- **Do not** import from `api/` in `agents/` or `core/`. Data flows one way: api → orchestrator → agents → core.
- **Do not** store file paths or job state in module-level variables. Use `job_store`.
- **Do not** use `print()` for logging. Use Python `logging` module: `logger = logging.getLogger(__name__)`.
- **Do not** call `event_bus.create_channel()` more than once per job. Check `event_bus.channel_exists()` first.
- **Do not** write tests that make real OpenAI API calls. Mock the client.
- **Do not** commit `.env` files. Only `.env.example`.
- **Do not** edit another person's owned files without a comment in the PR explaining why.
- **Do not** add new dependencies to `requirements.txt` without checking if it conflicts with existing ones (`pip check` after installing).

---

## DAG Conventions

The `DAG` class in `core/dag.py` uses this edge direction convention:

> An edge from `A → B` means **A depends on B** (B must be established before A).

This means:

- `dag.get_roots()` returns claims with **no dependencies** — process these first
- `dag.topological_sort()` returns claims in the order they should be processed
- `dag.get_descendants(node_id)` returns all claims that would be affected if `node_id` is refuted

Do not invert this convention in any agent. The CascadeAgent walks `get_descendants()` to propagate failures.

---

## Running Locally

```bash
# Backend
cd backend
cp .env.example .env        # fill in OPENAI_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev                 # runs on port 5173

# Verify everything works
curl http://localhost:8000/health
```

Six checks that must all pass before starting feature work:

```bash
curl http://localhost:8000/health                          # {"status": "ok"}
curl http://localhost:8000/review/test-id/dag              # {"nodes": [], "edges": []}
curl http://localhost:8000/poc/test-id/claims              # {"total": 1, ...}
python -c "from models import ClaimUnit, PoCSpec, ReviewReport; print('models ok')"
python -c "from agents.tex_parser import TexParserAgent; print(TexParserAgent().agent_id)"
python -c "from core.dag import DAG; d = DAG(); d.add_node('a'); print('dag ok')"
```

---

## Branch Strategy

- `main` is always runnable and demo-able. Never push broken code to main.
- Work on personal branches: `person-a/pipeline`, `person-b/review-agents`, `person-c/frontend`, `person-d/poc-agents`
- Merge to main only when your feature works end-to-end and all six checks above still pass.
- If you need to change `base.py`, `dag.py`, `event_bus.py`, or `job_store.py` — these are shared infrastructure. Coordinate before changing, bump everyone's branch after merging.

---

## Test Paper

For consistent testing across all branches, everyone uses the same paper:

**arXiv:1706.03762** — "Attention Is All You Need" (Vaswani et al., 2017)

Use: `https://arxiv.org/abs/1706.03762`

The backend extracts the article id and downloads `https://arxiv.org/e-print/1706.03762`. This paper has clearly labeled propositions, explicit performance numbers (BLEU scores), and complexity claims — it exercises all four modes well.

---

## Hackathon Priorities (36 hours)

Build in this order. Do not move to the next phase until the current one passes its checkpoint.

| Phase                     | Owner    | Checkpoint                                                           |
| ------------------------- | -------- | -------------------------------------------------------------------- |
| 0 — Scaffold              | Person A | All 6 verify checks pass                                             |
| 1 — Parser + DAG          | Person A | `python scripts/test_pipeline.py https://arxiv.org/abs/1706.03762 --max-claims 1` prints claims + DAG |
| 2 — Review agents         | Person B | `POST /review` returns full ReviewReport JSON for test paper         |
| 3 — Live DAG UI           | Person C | Enter arXiv URL, watch nodes turn green/red in browser in real time  |
| 7 (partial) — PoC backend | Person D | `GET /poc/{id}/scaffold.zip` downloads a real runnable scaffold      |

Phases 4 (Reader), 5 (Research), 6 (polish) are post-hackathon unless ahead of schedule.

The demo arc: enter arXiv URL → live DAG updates as review runs → click a node to see attacker/defender exchange → switch to PoC mode → download scaffold zip → show the generated test_harness.py. That's the story.
