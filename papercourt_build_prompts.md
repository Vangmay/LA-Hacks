# PaperCourt — Implementation Prompts

These are the exact prompts to feed into Claude Code (or any AI coding assistant) at each step.
Run them in order. Each prompt assumes the previous step is complete and working.

---

## PHASE 0 — Skeleton

### Prompt 0.1 — Project scaffold (team-ready)

```
Create a new PaperCourt project structured for a 4-person team working in parallel.
The primary goal is: every person can run the full stack on day one and work on their
own module without touching anyone else's files or breaking the main branch.

---

STACK:
- Backend: Python 3.11, FastAPI, Pydantic v2, uvicorn, python-dotenv
- Frontend: React 18 + Vite, Tailwind CSS, React Router v6
- Package manager: pip (backend), npm (frontend)

---

DIRECTORY STRUCTURE:

papercourt/
├── .env.example                  # template — copy to .env before running
├── .gitignore
├── README.md                     # start commands for all four workstreams
│
├── backend/
│   ├── main.py                   # FastAPI app entry, mounts all routers
│   ├── config.py                 # loads .env, exposes typed Settings object
│   ├── requirements.txt
│   │
│   ├── models/                   # ← Person A owns this directory
│   │   ├── __init__.py           # re-exports everything for clean imports
│   │   ├── claim.py              # ClaimUnit, ClaimType
│   │   ├── verification.py       # VerificationResult, VerificationTier
│   │   ├── adversarial.py        # Challenge, Rebuttal
│   │   ├── verdict.py            # ClaimVerdict
│   │   ├── report.py             # ReviewReport
│   │   ├── events.py             # DAGEvent, DAGEventType
│   │   ├── reader.py             # ClaimAnnotation, Exercise, Prerequisite, ComprehensionLevel, ComprehensionStatus
│   │   ├── poc.py                # PoCSpec, MetricCriterion, ExperimentResult, ReproducibilityReport, GapAnalysisEntry, ClaimTestability, ReproductionStatus
│   │   └── research.py           # Hypothesis, KnowledgeNode, ResearchSession
│   │
│   ├── agents/                   # ← Person A (base) + Person B (review) + Person D (poc)
│   │   ├── __init__.py
│   │   ├── base.py               # BaseAgent, AgentContext, AgentResult — Person A owns this
│   │   │
│   │   │   # Person A implements these (Phase 1):
│   │   ├── tex_parser.py
│   │   ├── claim_extractor.py
│   │   ├── dag_builder.py
│   │   │
│   │   │   # Person B implements these (Phase 2):
│   │   ├── symbolic_verifier.py
│   │   ├── numeric_adversary.py
│   │   ├── rag_retrieval.py
│   │   ├── attacker.py
│   │   ├── counterexample_search.py
│   │   ├── citation_gap.py
│   │   ├── defender.py
│   │   ├── verdict_aggregator.py
│   │   ├── cascade.py
│   │   ├── report_agent.py
│   │   │
│   │   │   # Person D implements these (Phase 7):
│   │   ├── claim_filter.py
│   │   ├── metric_extractor.py
│   │   ├── scaffold_generator.py
│   │   ├── results_analyzer.py
│   │   └── reproducibility_report.py
│   │
│   ├── core/                     # ← Person A owns this directory
│   │   ├── __init__.py
│   │   ├── dag.py                # DAG class: add_node, add_edge, has_cycle, topological_sort, get_descendants
│   │   ├── event_bus.py          # EventBus: create_channel, publish, subscribe
│   │   ├── job_store.py          # JobStore: create, get, update, all session state
│   │   └── orchestrators/
│   │       ├── __init__.py
│   │       ├── review.py         # ← Person B owns (Phase 2)
│   │       ├── poc.py            # ← Person D owns (Phase 7)
│   │       ├── reader.py         # stub only for now
│   │       └── research.py       # stub only for now
│   │
│   └── api/                      # each person owns their own route file
│       ├── __init__.py
│       ├── review.py             # ← Person B owns (Phase 2)
│       ├── poc.py                # ← Person D owns (Phase 7)
│       ├── reader.py             # stub only for now
│       └── research.py           # stub only for now
│
└── frontend/                     # ← Person C owns entirely
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── api/
    │   │   └── client.js         # all fetch calls — single source of truth for API URLs
    │   ├── components/
    │   │   └── .gitkeep
    │   └── pages/
    │       └── Home.jsx
    ├── index.html
    ├── vite.config.js            # proxy /api → localhost:8000
    └── package.json

---

IMPLEMENT THE FOLLOWING. Do not skip any item.

## 1. .env.example
```
OPENAI_API_KEY=your_key_here
BACKEND_PORT=8000
FRONTEND_PORT=5173
MAX_PARALLEL_CLAIMS=5
ATTACKER_CHALLENGE_CAP=3
LOG_LEVEL=INFO
```

## 2. config.py
Use pydantic-settings (pip install pydantic-settings):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    backend_port: int = 8000
    max_parallel_claims: int = 5
    attacker_challenge_cap: int = 3
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

## 3. All Pydantic models (fully typed, no Any except where noted)

models/claim.py:
```python
from pydantic import BaseModel
from typing import List, Literal, Optional

class ClaimUnit(BaseModel):
    claim_id: str
    text: str
    claim_type: Literal["theorem", "lemma", "corollary", "proposition", "assertion"]
    section: str
    equations: List[str]
    citations: List[str]
    dependencies: List[str]
```

models/verification.py:
```python
class VerificationResult(BaseModel):
    tier: Literal["symbolic", "numeric", "semantic"]
    status: Literal["passed", "failed", "inconclusive"]
    evidence: str
    confidence: float
```

models/adversarial.py:
```python
class Challenge(BaseModel):
    challenge_id: str
    claim_id: str
    attacker_agent: str
    challenge_text: str
    supporting_evidence: List[str]

class Rebuttal(BaseModel):
    challenge_id: str
    rebuttal_text: str
    supporting_evidence: List[str]
```

models/verdict.py:
```python
class ClaimVerdict(BaseModel):
    claim_id: str
    verdict: Literal["SUPPORTED", "CONTESTED", "REFUTED"]
    confidence: float
    is_cascaded: bool
    cascade_source: Optional[str]
    challenges: List[Challenge]
    rebuttals: List[Rebuttal]
    verification_results: List[VerificationResult]
```

models/report.py:
```python
from datetime import datetime

class ReviewReport(BaseModel):
    paper_title: str
    paper_hash: str
    reviewed_at: datetime
    total_claims: int
    supported: int
    contested: int
    refuted: int
    cascaded_failures: int
    verdicts: List[ClaimVerdict]
    dag_summary: dict
    markdown_report: str
```

models/events.py:
```python
from enum import Enum
from typing import Any, Optional
from datetime import datetime

class DAGEventType(str, Enum):
    NODE_CREATED      = "node_created"
    TIER_COMPLETE     = "tier_complete"
    CHALLENGE_ISSUED  = "challenge_issued"
    REBUTTAL_ISSUED   = "rebuttal_issued"
    VERDICT_EMITTED   = "verdict_emitted"
    CASCADE_TRIGGERED = "cascade_triggered"
    REVIEW_COMPLETE   = "review_complete"
    NODE_CLASSIFIED   = "node_classified"
    SCAFFOLD_GENERATED = "scaffold_generated"
    POC_READY         = "poc_ready"

class DAGEvent(BaseModel):
    event_id: str
    job_id: str
    event_type: DAGEventType
    claim_id: Optional[str] = None
    payload: dict
    timestamp: datetime
```

models/reader.py:
```python
from enum import Enum

class ComprehensionLevel(str, Enum):
    LAYPERSON     = "layperson"
    UNDERGRADUATE = "undergraduate"
    GRADUATE      = "graduate"
    EXPERT        = "expert"

class ComprehensionStatus(str, Enum):
    UNVISITED   = "unvisited"
    IN_PROGRESS = "in_progress"
    UNDERSTOOD  = "understood"
    FLAGGED     = "flagged"

class Prerequisite(BaseModel):
    concept: str
    description: str
    resource_links: List[str]

class Exercise(BaseModel):
    exercise_id: str
    prompt: str
    exercise_type: Literal["conceptual", "computational", "counterexample_mcq", "proof_fill"]
    answer_key: str
    user_answer: Optional[str] = None
    graded: Optional[bool] = None

class ClaimAnnotation(BaseModel):
    claim_id: str
    level: ComprehensionLevel
    explanation: str
    glossary: dict
    prerequisites: List[Prerequisite]
    exercises: List[Exercise]
    comprehension_status: ComprehensionStatus
```

models/poc.py:
```python
from enum import Enum

class ClaimTestability(str, Enum):
    TESTABLE    = "testable"
    THEORETICAL = "theoretical"

class ReproductionStatus(str, Enum):
    REPRODUCED = "REPRODUCED"
    PARTIAL    = "PARTIAL"
    FAILED     = "FAILED"
    PENDING    = "PENDING"

class MetricCriterion(BaseModel):
    metric_name: str
    paper_reported_value: str
    numeric_threshold: Optional[float]
    tolerance: float = 0.02
    comparison: Literal["gte", "lte", "eq", "within_tolerance"]
    experimental_conditions: dict

class PoCSpec(BaseModel):
    spec_id: str
    claim_id: str
    testability: ClaimTestability
    success_criteria: List[MetricCriterion]
    failure_criteria: List[MetricCriterion]
    scaffold_files: dict  # filename → content
    readme: str

class ExperimentResult(BaseModel):
    claim_id: str
    metric_name: str
    achieved_value: float
    status: ReproductionStatus
    delta: Optional[float] = None
    error_message: Optional[str] = None

class GapAnalysisEntry(BaseModel):
    claim_id: str
    explanation: str
    likelihood: Literal["high", "medium", "low"]
    suggested_fix: str

class ReproducibilityReport(BaseModel):
    session_id: str
    paper_title: str
    total_testable_claims: int
    reproduced: int
    partial: int
    failed: int
    reproduction_rate: float
    results: List[ExperimentResult]
    gap_analyses: List[GapAnalysisEntry]
    what_to_try_next: List[str]
    markdown_report: str
```

models/research.py:
```python
from typing import Any

class Hypothesis(BaseModel):
    hypothesis_id: str
    text: str
    source_gap: str
    proof_approach: Optional[Literal["induction", "construction", "contradiction", "numeric"]] = None
    verification_result: Optional[VerificationResult] = None
    status: Literal["proposed", "approved", "rejected", "proven", "disproven", "inconclusive"]
    user_approved: bool

class KnowledgeNode(BaseModel):
    node_id: str
    claim_text: str
    source_paper: str
    related_nodes: List[str]
    contradicting_nodes: List[str]

class ResearchSession(BaseModel):
    session_id: str
    query: str
    retrieved_papers: List[str]
    knowledge_graph: List[KnowledgeNode]
    detected_gaps: List[str]
    hypotheses: List[Hypothesis]
    iteration_count: int
    working_memory: dict
    research_note: Optional[str] = None
    self_review_verdict: Optional[ReviewReport] = None
```

models/__init__.py — re-export everything:
```python
from .claim import ClaimUnit
from .verification import VerificationResult
from .adversarial import Challenge, Rebuttal
from .verdict import ClaimVerdict
from .report import ReviewReport
from .events import DAGEvent, DAGEventType
from .reader import ClaimAnnotation, ComprehensionLevel, ComprehensionStatus, Exercise, Prerequisite
from .poc import PoCSpec, MetricCriterion, ExperimentResult, ReproducibilityReport, GapAnalysisEntry, ClaimTestability, ReproductionStatus
from .research import Hypothesis, KnowledgeNode, ResearchSession
```

## 4. agents/base.py — the shared contract all agents implement

```python
from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel
from models import ClaimUnit

class AgentContext(BaseModel):
    job_id: str
    claim: Optional[ClaimUnit] = None
    extra: dict = {}  # mode-specific context injected by orchestrators

class AgentResult(BaseModel):
    agent_id: str
    claim_id: Optional[str] = None
    status: Literal["success", "error", "inconclusive"]
    output: dict
    confidence: float
    error: Optional[str] = None

class BaseAgent(ABC):
    agent_id: str

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        pass

    def _mock_result(self, claim_id: Optional[str] = None, output: dict = {}) -> AgentResult:
        """Convenience method for stub implementations."""
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output=output,
            confidence=0.5,
        )
```

## 5. All agent stubs

Every agent file must:
- Define a class that inherits from BaseAgent
- Set agent_id as a class variable
- Implement run() using self._mock_result() with a realistic output shape

Stubs for Person A's agents (tex_parser.py, claim_extractor.py, dag_builder.py):
- tex_parser.py output shape: {"title": "Paper title", "sections": [], "equations": [], "bibliography": [], "raw_text": ""}
- claim_extractor.py mock output: {"claims": [{"claim_id": "claim_001", "text": "Mock theorem", "claim_type": "theorem", "section": "1", "equations": [], "citations": [], "dependencies": []}]}
- dag_builder.py mock output: {"edges": [], "adjacency": {}, "roots": ["claim_001"], "topological_order": ["claim_001"]}

Stubs for Person B's agents: return empty/minimal valid shapes matching what the real agent will return.
- symbolic_verifier.py mock: {"tier": "symbolic", "status": "inconclusive", "evidence": "stub", "confidence": 0.5}
- numeric_adversary.py mock: same shape as symbolic
- rag_retrieval.py mock: same shape
- attacker.py mock: {"challenges": []}
- defender.py mock: {"rebuttals": []}
- verdict_aggregator.py mock: {"claim_id": "claim_001", "verdict": "SUPPORTED", "confidence": 0.8, "is_cascaded": False, "cascade_source": None, "challenges": [], "rebuttals": [], "verification_results": []}
- cascade.py mock: {"updated_verdicts": {}}
- report_agent.py output shape: {"markdown": "# Review Report"}

Stubs for Person D's agents:
- claim_filter.py mock: {"testable": ["claim_001"], "theoretical": [], "classifications": {}}
- metric_extractor.py mock: {"spec_id": "spec_001", "claim_id": "claim_001", "testability": "testable", "success_criteria": [], "failure_criteria": []}
- scaffold_generator.py mock: {"scaffold_files": {"README.md": "# Mock scaffold"}, "readme": "Mock"}
- results_analyzer.py mock: {"results": [], "claim_statuses": {}}
- reproducibility_report.py mock: {"markdown": "# Mock reproducibility report"}

## 6. core/dag.py
Implement fully (not a stub — everyone depends on this):
```python
from collections import defaultdict, deque

class DAG:
    def __init__(self):
        self.nodes: set = set()
        self.edges: dict = defaultdict(set)     # from → set of to
        self.reverse: dict = defaultdict(set)   # to → set of from

    def add_node(self, node_id: str): ...
    def add_edge(self, from_id: str, to_id: str): ...  # from depends on to? No: from_id → to_id means from_id REQUIRES to_id
    def has_cycle(self) -> bool: ...              # Kahn's algorithm
    def topological_sort(self) -> list: ...       # raises ValueError if cycle
    def get_descendants(self, node_id: str) -> set: ...  # all nodes downstream
    def get_roots(self) -> list: ...              # nodes with no incoming edges
    def to_dict(self) -> dict: ...                # serializable {nodes: [...], edges: [...]}
```

## 7. core/event_bus.py
Implement fully:
```python
import asyncio
from typing import AsyncIterator
from models import DAGEvent

class EventBus:
    def __init__(self):
        self._channels: dict[str, asyncio.Queue] = {}
        self._history: dict[str, list[DAGEvent]] = {}

    def create_channel(self, job_id: str): ...
    async def publish(self, job_id: str, event: DAGEvent): ...
    async def subscribe(self, job_id: str, last_event_id: str = None) -> AsyncIterator[DAGEvent]:
        # If last_event_id provided, replay history from that point first, then stream live
        ...
    def channel_exists(self, job_id: str) -> bool: ...
    def close_channel(self, job_id: str): ...

event_bus = EventBus()   # singleton
```

## 8. core/job_store.py
Implement fully as an in-memory store with typed session shapes:
```python
from typing import Optional, Any
import uuid

class JobStore:
    def __init__(self):
        self._jobs: dict = {}

    def create_job(self, mode: str, **kwargs) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {"job_id": job_id, "mode": mode, "status": "queued", **kwargs}
        return job_id

    def get(self, job_id: str) -> Optional[dict]: ...
    def update(self, job_id: str, **kwargs): ...
    def set_status(self, job_id: str, status: str): ...
    def exists(self, job_id: str) -> bool: ...

job_store = JobStore()   # singleton
```

## 9. Orchestrator stubs (core/orchestrators/)

Each orchestrator stub must:
- Define an async run(job_id, ...) method
- Immediately set job status to "processing"
- Sleep 0.1 seconds
- Set job status to "complete"
- Not raise any exceptions

## 10. API routes — all wired and returning valid mock responses

api/review.py — mount at /review:
- POST /review → create job, return {"job_id": str, "status": "queued"}
- GET /review/{job_id}/status → {"status": str, "completed_claims": 0, "total_claims": 0}
- GET /review/{job_id}/stream → SSE with one heartbeat comment, then closes
- GET /review/{job_id}/report → completed ReviewReport or 202 while processing
- GET /review/{job_id}/dag → {"nodes": [], "edges": []}
- GET /review/{job_id}/report/markdown → completed markdown report

api/poc.py — mount at /poc:
- POST /poc → {"session_id": str, "status": "queued"}
- GET /poc/{session_id}/claims → {"total": 1, "testable": 1, "theoretical": 0, "claims": []}
- GET /poc/{session_id}/claim/{claim_id}/spec → mock PoCSpec
- GET /poc/{session_id}/scaffold.zip → 202 {"detail": "not ready"}
- POST /poc/{session_id}/results → {"status": "analyzing"}
- GET /poc/{session_id}/report → 202 or mock ReproducibilityReport
- GET /poc/{session_id}/dag → {"nodes": [], "edges": []}

api/reader.py and api/research.py — stub only: every route returns {"status": "not implemented"} with 200.

## 11. main.py — mount all routers

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.review import router as review_router
from api.poc import router as poc_router
from api.reader import router as reader_router
from api.research import router as research_router

app = FastAPI(title="PaperCourt API")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router, prefix="/review")
app.include_router(poc_router, prefix="/poc")
app.include_router(reader_router, prefix="/read")
app.include_router(research_router, prefix="/research")

@app.get("/health")
async def health(): return {"status": "ok"}
```

## 12. Frontend scaffold

vite.config.js — proxy /api to backend:
```js
export default {
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8000', rewrite: (p) => p.replace(/^\/api/, '') } }
  }
}
```

frontend/src/api/client.js — single file for all API calls, everyone imports from here:
```js
const BASE = '/api'

export const api = {
  review: {
    submit: (file) => { /* POST /review with FormData */ },
    status: (jobId) => fetch(`${BASE}/review/${jobId}/status`).then(r => r.json()),
    dag: (jobId) => fetch(`${BASE}/review/${jobId}/dag`).then(r => r.json()),
    stream: (jobId) => new EventSource(`${BASE}/review/${jobId}/stream`),
    report: (jobId) => fetch(`${BASE}/review/${jobId}/report`).then(r => r.json()),
  },
  poc: {
    submit: (file) => { /* POST /poc with FormData */ },
    claims: (sessionId) => fetch(`${BASE}/poc/${sessionId}/claims`).then(r => r.json()),
    spec: (sessionId, claimId) => fetch(`${BASE}/poc/${sessionId}/claim/${claimId}/spec`).then(r => r.json()),
    uploadResults: (sessionId, file) => { /* POST /poc/{sessionId}/results */ },
    report: (sessionId) => fetch(`${BASE}/poc/${sessionId}/report`).then(r => r.json()),
    stream: (sessionId) => new EventSource(`${BASE}/poc/${sessionId}/stream`),
  }
}
```

App.jsx — set up React Router with placeholder routes:
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/review/:jobId" element={<div>Review page (Person C builds this)</div>} />
        <Route path="/poc/:sessionId" element={<div>PoC page (Person C builds this)</div>} />
      </Routes>
    </BrowserRouter>
  )
}
```

Home.jsx — landing with two buttons: "Review a Paper" and "Build a PoC". Both just navigate to /review and /poc for now.

## 13. README.md at repo root

Must contain:
```
# PaperCourt

## Quick Start

cp backend/.env.example backend/.env
# Add your OPENAI_API_KEY to backend/.env

# Terminal 1 — Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend  
cd frontend && npm install && npm run dev

# Verify
curl http://localhost:8000/health        # should return {"status": "ok"}
open http://localhost:5173               # should show PaperCourt landing page

## Who owns what
Person A: backend/models/, backend/core/, backend/agents/tex_parser.py, claim_extractor.py, dag_builder.py
Person B: backend/agents/ (review agents), backend/core/orchestrators/review.py, backend/api/review.py
Person C: frontend/ (all of it)
Person D: backend/agents/ (poc agents), backend/core/orchestrators/poc.py, backend/api/poc.py

## Branch strategy
main is always runnable. Work on your own branch: git checkout -b person-a/pipeline
Merge to main only when your feature works end-to-end.
Never edit another person's owned files without coordinating first.
```

## 14. requirements.txt for backend

Include all dependencies upfront so everyone can install once:
fastapi, uvicorn[standard], pydantic[email], pydantic-settings, python-dotenv,
python-multipart, sse-starlette, openai, sympy, scipy, numpy,
sentence-transformers, chromadb, networkx, httpx, tenacity, python-json-logger

---

VERIFY THE SCAFFOLD WORKS by running:
1. cd backend && uvicorn main:app --reload → no import errors
2. curl http://localhost:8000/health → {"status": "ok"}
3. curl http://localhost:8000/review/test-id/dag → {"nodes": [], "edges": []}
4. cd frontend && npm run dev → page loads without errors
5. python -c "from models import ClaimUnit, PoCSpec, ReviewReport; print('models ok')"
6. python -c "from agents.tex_parser import TexParserAgent; a = TexParserAgent(); print(a.agent_id)"

All six checks must pass before anyone starts Phase 1.
```

---

## PHASE 1 — Parser + DAG

### Prompt 1.1 — TexParserAgent

```
Implement TexParserAgent in backend/agents/tex_parser.py.

INPUT: assembled TeX text from an arXiv e-print source bundle.
OUTPUT: AgentResult where output contains:
{
  "title": str,
  "abstract": str,
  "sections": [{"heading": str, "content": str}],
  "equations": [{"id": str, "latex": str, "section": str}],
  "bibliography": [{"ref_id": str, "raw_text": str}],
  "raw_text": str
}

IMPLEMENTATION:
1. Strip TeX comments and identify the document body.
2. Section detection: identify `\section`, `\subsection`, `\subsubsection`, and `\paragraph` headings.
3. Equation extraction: extract math from `$...$`, `$$...$$`, `\[...\]`, and equation-like environments. Assign sequential IDs like "eq_1", "eq_2".
4. Bibliography: parse `thebibliography`, `\bibitem`, and `\bibliography{...}` references.
5. Preserve math spans in raw text so downstream symbolic and numeric agents can inspect original notation.
6. Add a `parse_tex_text(tex_text: str) -> dict` convenience function that instantiates and runs the parser.

Write a simple test script that parses a representative TeX fixture and prints the section count and equation count.
```

### Prompt 1.2 — ClaimExtractorAgent

```
Implement ClaimExtractorAgent in backend/agents/claim_extractor.py.

INPUT: The parsed output dict from TexParserAgent (sections, equations, bibliography, raw_text).
OUTPUT: AgentResult where output contains:
{
  "claims": [ClaimUnit, ...]   // list of fully populated ClaimUnit objects as dicts
}

ClaimUnit fields (already defined in models/claim.py):
- claim_id: str (format: "claim_001", "claim_002", ...)
- text: str (the claim as stated in the paper)
- claim_type: Literal["theorem", "lemma", "corollary", "proposition", "assertion"]
- section: str (which section it appears in)
- equations: List[str] (equation IDs from TexParserAgent output that belong to this claim)
- citations: List[str] (reference IDs cited within this claim or its proof)
- dependencies: List[str] (leave empty for now — DAGBuilderAgent fills this)

IMPLEMENTATION:
1. Use the OpenAI API (model: gpt-4o). Load the API key from environment variable OPENAI_API_KEY.
2. System prompt: "You are a mathematical claim extractor. Given sections of a research paper, identify every theorem, lemma, corollary, proposition, and key load-bearing assertion. For each, return a JSON object with the fields specified. Be exhaustive — include informal assertions that are critical to the proof chain even if not labeled."
3. User prompt: pass the full raw_text (truncated to 12000 tokens if needed). Ask for a JSON array response only, no prose.
4. Parse the JSON response. If parsing fails, retry once with a stricter prompt. If it fails again, return status="inconclusive" with whatever partial claims were extracted.
5. Match equation IDs to claims heuristically: if an equation appears within 200 characters of a claim's text in the raw document, associate it.
6. Match citation IDs similarly: scan for [1], [2] style references in the claim text and surrounding proof.
7. Assign sequential claim_ids.
8. Validate each claim against the ClaimUnit Pydantic model before returning. Drop malformed claims with a warning log.

Use async OpenAI client (openai.AsyncOpenAI). The run() method must be async.
```

### Prompt 1.3 — DAGBuilderAgent

```
Implement DAGBuilderAgent in backend/agents/dag_builder.py.

INPUT: List of ClaimUnit dicts (from ClaimExtractorAgent).
OUTPUT: AgentResult where output contains:
{
  "edges": [{"from": claim_id, "to": claim_id}, ...],
  "adjacency": {claim_id: [claim_id, ...]},  // claim_id → list of claim_ids it depends on
  "roots": [claim_id, ...],                  // claims with no dependencies
  "topological_order": [claim_id, ...]
}

IMPLEMENTATION:
1. Use the OpenAI API (gpt-4o). 
2. System prompt: "You are a mathematical dependency analyzer. Given a list of claims from a paper, determine which claims logically depend on which others. A claim B depends on A if understanding or proving B requires A to be established first. Return ONLY a JSON array of dependency edges: [{from: claim_id, to: claim_id}] where 'to' depends on 'from'. Be conservative — only add an edge if the dependency is clear."
3. User prompt: pass the list of claims as a compact JSON array (id + text only, not full objects).
4. After receiving edges, use the DAG class from core/dag.py:
   - Add all claim nodes
   - Add all edges
   - Run has_cycle() — if a cycle is detected, log a warning and remove the offending edge (the last one that created the cycle)
   - Run topological_sort() to get the processing order
   - Identify roots (nodes with no incoming edges)
5. Update the `dependencies` field on each ClaimUnit with its incoming neighbors.
6. Return the adjacency map, roots list, and topological order.
7. Also populate the DAG instance in core/dag.py so the orchestrator can use it directly.
```

### Prompt 1.4 — Pipeline integration test

```
Wire arXiv source ingestion → TexParserAgent → ClaimExtractorAgent → DAGBuilderAgent into a runnable pipeline script at backend/scripts/test_pipeline.py.

The script should:
1. Accept an arXiv URL or bare article id as a command-line argument
2. Fetch `https://arxiv.org/e-print/{id}`, assemble TeX, and run all three agents in sequence
3. Print a formatted summary:
   - Paper title
   - Number of sections parsed
   - Number of equations found
   - Number of claims extracted (broken down by type: theorem/lemma/etc.)
   - DAG: number of edges, number of root claims, topological order
   - Print each claim in topological order: "claim_id (type): first 80 chars of text..."
4. If any agent returns status="inconclusive", print a warning but continue
5. Save the full pipeline output as JSON to outputs/{paper_hash}_pipeline.json

Find a real arXiv paper to test with. Use one with clearly labeled lemmas and theorems — a combinatorics or linear algebra paper works best (e.g. arXiv:2301.00001 or similar).

The script must run with: python scripts/test_pipeline.py https://arxiv.org/abs/1706.03762
```

---

## PHASE 2 — Review Mode Backend

### Prompt 2.1 — SymbolicVerifierAgent

```
Implement SymbolicVerifierAgent in backend/agents/symbolic_verifier.py.

INPUT (via AgentContext): A single ClaimUnit dict.
OUTPUT: AgentResult where output is a VerificationResult dict:
{
  "tier": "symbolic",
  "status": "passed" | "failed" | "inconclusive",
  "evidence": str,   // what was checked and what the result was
  "confidence": float
}

IMPLEMENTATION:
1. Use SymPy (pip install sympy).
2. For each equation string in claim.equations:
   a. Attempt to parse it as a SymPy expression using sympy.sympify() or sympy.parse_latex() (pip install antlr4-python3-runtime for LaTeX parsing).
   b. If the equation is an identity (LHS = RHS), check with sympy.simplify(LHS - RHS) == 0.
   c. If the equation is an inequality, attempt to verify with sympy.solve() or sympy.reduce_inequalities().
   d. If parsing fails, skip this equation and note it in evidence.
3. If no equations are present or all fail to parse, return status="inconclusive" with evidence="no parseable equations found".
4. If any equation check definitively fails (simplify != 0 for an identity), return status="failed".
5. If all parseable equations pass, return status="passed".
6. Wrap everything in try/except — SymPy can raise on malformed input. Always return a result, never raise.
7. Set confidence: 0.9 if passed with ≥1 verified equation, 0.5 if inconclusive, 0.85 if failed with evidence.
```

### Prompt 2.2 — NumericAdversaryAgent

```
Implement NumericAdversaryAgent in backend/agents/numeric_adversary.py.

INPUT: A single ClaimUnit dict.
OUTPUT: AgentResult where output is a VerificationResult dict with tier="numeric".

GOAL: Search for a numeric counterexample to the claim. Focus on universally quantified claims ("for all x...", "for every n...", bounds like "≤", "≥", "< ε").

IMPLEMENTATION:
1. Use SciPy (pip install scipy) and NumPy.
2. First, use GPT-4o to extract a testable numeric predicate from the claim:
   System prompt: "Given this mathematical claim, if it contains a universally quantified numeric assertion (for all x in domain, f(x) satisfies condition), extract it as a Python lambda string: {'predicate': 'lambda x: ...', 'domain': [low, high], 'is_universal': bool}. If the claim has no testable numeric form, return {'is_universal': false}. Return JSON only."
3. If is_universal is false or extraction fails, return status="inconclusive".
4. If a predicate is extracted:
   a. Evaluate the predicate at 1000 random points in the domain using numpy.random.uniform.
   b. If any evaluation returns False (or raises), record it as a counterexample and return status="failed" with evidence showing the counterexample value.
   c. Use scipy.optimize.minimize with the negated predicate to search for a minimum that violates the bound. If the minimum found is < 0 (violates), return status="failed".
   d. If no counterexample found after both checks, return status="passed" with confidence=0.7 (numeric passing is not a proof).
5. All numpy/scipy calls in try/except. If the lambda string is unsafe (contains imports, exec, etc.), reject it and return inconclusive.
6. Maximum 5 seconds of compute per claim — use a timeout.
```

### Prompt 2.3 — AttackerAgent + sub-agents

```
Implement AttackerAgent in backend/agents/attacker.py, and its two sub-agents CounterexampleSearchAgent and CitationGapAgent.

ATTACKER AGENT:
INPUT (AgentContext): ClaimUnit dict + list of VerificationResult dicts from tiers.
OUTPUT: AgentResult where output contains:
{
  "challenges": [Challenge dict, ...]
}

Challenge fields: challenge_id, claim_id, attacker_agent, challenge_text, supporting_evidence (list of strings).

IMPLEMENTATION:
1. System prompt: "You are a hostile but rigorous peer reviewer. Your job is to find every possible flaw in the given mathematical claim. Use the verification results as ammunition. Generate between 1 and 3 challenges. Each challenge must be: specific (reference the exact part of the claim being attacked), technically grounded (not vague), and falsifiable. Return a JSON array of challenges."
2. Include in the user prompt: the claim text, claim type, any equations, and a summary of tier results (e.g. "Symbolic check: FAILED — equation identity does not hold").
3. Spawn CounterexampleSearchAgent if claim_type is theorem or proposition and the claim contains "for all", "for every", "∀".
4. Spawn CitationGapAgent if claim.citations is non-empty.
5. Merge challenges from all sub-agents into the final output.
6. Assign sequential challenge IDs: "ch_{claim_id}_001", etc.

COUNTEREXAMPLE SEARCH AGENT (in same file or agents/counterexample_search.py):
- GPT-4o prompt: "Construct an explicit mathematical counterexample to this claim if one exists. If you can construct one, describe it precisely with specific values. If the claim appears universally valid, say so. Return JSON: {counterexample_found: bool, description: str, values: dict}"
- If counterexample_found, add it as a challenge with supporting_evidence containing the specific values.

CITATION GAP AGENT (in agents/citation_gap.py):
- GPT-4o prompt: "Given this claim and its cited references (listed by ref_id only since we don't have full text), identify any citation gaps: places where the claim makes an appeal to a result but either cites nothing, cites something implausibly general, or the citation seems mismatched. Return JSON: {gaps: [{location: str, issue: str}]}"
- Convert each gap to a Challenge object.
```

### Prompt 2.4 — DefenderAgent

```
Implement DefenderAgent in backend/agents/defender.py.

INPUT (AgentContext): ClaimUnit dict + list of Challenge dicts from AttackerAgent.
OUTPUT: AgentResult where output contains:
{
  "rebuttals": [Rebuttal dict, ...]
}

Rebuttal fields: challenge_id, rebuttal_text, supporting_evidence (list of strings).

IMPLEMENTATION:
1. For each challenge, generate one rebuttal. Run all rebuttals concurrently with asyncio.gather.
2. System prompt per challenge: "You are the author of the paper defending this claim against a peer reviewer's challenge. Give the strongest possible rebuttal. If the challenge reveals a genuine flaw, acknowledge the scope limitation but argue why the core result still holds. If the challenge is wrong, explain exactly why. Be precise and technical. Return JSON: {rebuttal_text: str, supporting_evidence: [str]}"
3. User prompt: include the full claim text + the specific challenge text.
4. If the GPT-4o response cannot be parsed as JSON, wrap the raw text as rebuttal_text with empty supporting_evidence.
5. Match each rebuttal to its challenge_id.
6. The DefenderAgent should never refuse to generate a rebuttal — even a weak defense is better than none.
```

### Prompt 2.5 — VerdictAggregatorAgent + CascadeAgent

```
Implement VerdictAggregatorAgent in backend/agents/verdict_aggregator.py and CascadeAgent in backend/agents/cascade.py.

VERDICT AGGREGATOR:
INPUT (AgentContext): ClaimUnit + list of VerificationResults + list of Challenges + list of Rebuttals.
OUTPUT: AgentResult where output is a ClaimVerdict dict.

IMPLEMENTATION:
1. Build a structured summary for GPT-4o:
   - Tier results: symbolic/numeric/semantic statuses and confidences
   - Number of challenges and their texts
   - Number of rebuttals and their texts
2. System prompt: "You are a senior mathematical journal editor making a final verdict on a claim. Weigh the evidence: verification tier results (symbolic/numeric checks carry more weight than semantic), attacker challenges, and defender rebuttals. Return JSON: {verdict: 'SUPPORTED'|'CONTESTED'|'REFUTED', confidence: float 0-1, rationale: str (2-3 sentences)}. 
   Scoring guidance: if any tier failed AND attacker has an unrefuted challenge → lean REFUTED. If tiers passed but challenger raised valid scope issue → CONTESTED. If tiers passed and all challenges rebutted → SUPPORTED."
3. Populate the full ClaimVerdict model: claim_id, verdict, confidence, is_cascaded=False, cascade_source=None, challenges, rebuttals, verification_results.
4. Return the ClaimVerdict as output.

CASCADE AGENT:
INPUT: dict of {claim_id: ClaimVerdict} + DAG adjacency map.
OUTPUT: AgentResult where output contains updated {claim_id: ClaimVerdict} dict with cascade verdicts applied.

IMPLEMENTATION:
1. Get topological order from core/dag.py.
2. Walk in topological order. For each claim:
   - Check if any of its dependencies (parent claims) have verdict=REFUTED
   - If yes, override this claim's verdict to REFUTED, set is_cascaded=True, set cascade_source to the refuted parent's claim_id
   - Set confidence to 1.0 for cascaded refutations (they are deterministic)
3. A claim cascades even if its own direct verdict was SUPPORTED — the dependency failure overrides.
4. Return the full updated verdicts dict.
```

### Prompt 2.6 — ReviewOrchestrator + ReportAgent

```
Implement ReviewOrchestrator in backend/core/orchestrators/review.py and ReportAgent in backend/agents/report_agent.py.

REVIEW ORCHESTRATOR:
This is the top-level controller for Review Mode. It must:

1. Accept a job_id and parsed pipeline output (ClaimUnits + DAG).
2. Emit DAGEvent(event_type=NODE_CREATED) for each claim node via event_bus.publish().
3. Run the per-claim agent swarm in topological order, respecting dependencies:
   - For claims with no pending dependencies: run immediately
   - Use asyncio.gather to run ALL of: SymbolicVerifierAgent, NumericAdversaryAgent, RAGRetrievalAgent, AttackerAgent, DefenderAgent in parallel for each claim
   - After gather: run VerdictAggregatorAgent for that claim
   - Emit DAGEvents at each milestone: TIER_COMPLETE, CHALLENGE_ISSUED, REBUTTAL_ISSUED, VERDICT_EMITTED
4. After all per-claim verdicts are collected: run CascadeAgent
   - Emit CASCADE_TRIGGERED events for each cascaded claim
5. Run ReportAgent
6. Emit REVIEW_COMPLETE
7. Store the final ReviewReport in job_store.

For parallelism: claims whose all dependencies are resolved can be processed in parallel batches.
Use asyncio.create_task to kick off each claim's swarm as soon as its dependencies complete.

REPORT AGENT:
INPUT: dict of {claim_id: ClaimVerdict} + paper metadata.
OUTPUT: AgentResult where output contains:
{
  "report": ReviewReport dict,
  "markdown": str
}

IMPLEMENTATION:
1. Compute summary stats: total_claims, supported, contested, refuted, cascaded_failures.
2. Generate markdown report with GPT-4o:
   System prompt: "Generate a structured peer review report in markdown. Include: executive summary, critical findings (refuted claims with rationale), contested claims requiring attention, cascade failure chain if present, and an overall assessment. Be direct and technical."
   User prompt: pass the full verdicts JSON.
3. Populate the ReviewReport Pydantic model fully.
4. Return both the model and the markdown string.
```

### Prompt 2.7 — Review Mode API routes

```
Wire Review Mode end-to-end in backend/api/review.py.

ROUTES TO IMPLEMENT:

POST /review
- Accept an arXiv URL/id
- Fetch and assemble the arXiv e-print source under /tmp/papercourt/{job_id}
- Create job in job_store with status="queued"
- Launch ReviewOrchestrator as a background task (asyncio.create_task) — run the full pipeline: TexParserAgent → ClaimExtractorAgent → DAGBuilderAgent → ReviewOrchestrator
- Return: {"job_id": str, "status": "queued"}

GET /review/{job_id}/status
- Return current job status from job_store: queued | parsing | extracting | reviewing | complete | error
- Include progress: {"completed_claims": int, "total_claims": int}

GET /review/{job_id}/stream
- SSE endpoint using sse-starlette (pip install sse-starlette)
- Subscribe to event_bus channel for this job_id
- Stream each DAGEvent as: event: dag_update\ndata: {json}\n\n
- Keep connection alive with a heartbeat comment every 15 seconds
- Close stream when REVIEW_COMPLETE event is received or job not found

GET /review/{job_id}/report
- Return the ReviewReport JSON from job_store
- 404 if job not found, 202 if still in progress

GET /review/{job_id}/dag
- Return the current DAG snapshot: nodes (with current verdict if available), edges
- Always available once DAGBuilderAgent has run (even mid-review)

GET /review/{job_id}/report/markdown
- Return the markdown string from ReportAgent as text/markdown

Error handling: all routes must return structured error responses {"error": str, "job_id": str}.
Add request logging middleware that logs method, path, status, and duration.
```

---

## PHASE 3 — SSE + Live DAG UI

### Prompt 3.1 — React app scaffold + DAG canvas

```
Build the PaperCourt frontend in the frontend/ directory.

DESIGN DIRECTION:
Dark theme. The aesthetic is "scientific terminal meets research tool" — think dark navy/charcoal backgrounds, monospace accents for claim IDs and confidence scores, clean sans-serif for body text. Use a distinctive font pairing: a geometric display font for headings, JetBrains Mono for technical identifiers. Color palette: dark background (#0F1117), card surfaces (#1A1D2E), accent blue (#4A9EFF), green (#22C55E), yellow (#EAB308), red (#EF4444), dark red (#7F1D1D). Thin colored borders on cards rather than heavy shadows.

PAGES/COMPONENTS TO BUILD:

1. App.jsx — top-level layout with a persistent header and main content area

2. Header component:
   - Left: "PAPERCOURT" in monospace with a small glyph (⚖ or similar)
   - Center: mode tabs — [Review] [Reader] [Research] — only Review is active for now, others are dimmed
   - Right: arXiv URL button (opens modal)

3. SubmissionModal component:
   - arXiv URL/id input
   - On submit: POST /review with the arXiv value
   - Show submission progress, then transition to "Analyzing paper..."
   - On success: navigate to /review/{job_id}

4. ReviewPage at route /review/:jobId:
   - Full viewport split: DAG canvas (75%) + Activity Feed (25%)
   - Summary bar at top: live counts for ✓ Supported / ? Contested / ✗ Refuted / ⟳ Processing
   - Fetches /review/{jobId}/dag on mount for initial snapshot
   - Connects to /review/{jobId}/stream (EventSource) immediately
   - On each SSE event: updates node state in local React state

5. DAGCanvas component using React Flow:
   - Install: npm install reactflow
   - Nodes: custom ClaimNode component (see below)
   - Layout: use dagre for hierarchical layout (npm install dagre @dagrejs/dagre)
   - Edges: animated when cascade is active
   - Controls: zoom, fit view, minimap
   - On node click: dispatch to open NodeDetailPanel

6. ClaimNode component (custom React Flow node):
   - Size: 180px × 80px
   - Shows: claim_id (monospace, small), claim_type badge, status indicator
   - Border color = current state color
   - Pulsing ring animation (CSS keyframes) when status = "processing"
   - Smooth color transition on status change (CSS transition)

7. NodeDetailPanel component (slides in from right, 40% width):
   - Claim text (full)
   - Tier results: three rows (Symbolic / Numeric / Semantic) each with pass/fail/inconclusive badge
   - Challenges section: expandable list
   - Rebuttals section: expandable list
   - Verdict badge with confidence percentage
   - "CASCADED FROM: claim_id" note if is_cascaded

8. ActivityFeed component:
   - Scrolling list of DAGEvent entries
   - Each entry: icon + agent name + short description + timestamp
   - Auto-scrolls to bottom on new entries
   - Max 200 entries, oldest dropped

NODE STATE COLORS (use CSS variables):
- pending: #6B7280
- processing: #3B82F6 (with pulsing ring)
- SUPPORTED: #22C55E
- CONTESTED: #EAB308
- REFUTED: #EF4444
- REFUTED_CASCADE: #7F1D1D

The SSE → React state update logic:
- node_created: add node to nodes array with status=pending
- tier_complete: update node metadata
- challenge_issued / rebuttal_issued: append to activity feed
- verdict_emitted: update node status and verdict data
- cascade_triggered: update node status to REFUTED_CASCADE, animate affected edges red
- review_complete: show completion banner, enable "Download Report" button
```

### Prompt 3.2 — Polish the live DAG experience

```
Polish the ReviewPage DAG experience with the following improvements:

1. DAGRE LAYOUT: After nodes/edges are set, run the dagre layout algorithm to position nodes in a top-down hierarchy. Re-run layout whenever new nodes are added via SSE. Animate node position changes with a smooth transition (use React Flow's node position interpolation or a spring animation).

2. EDGE ANIMATIONS:
   - Normal edges: thin grey (#374151), animated dashed line moving in dependency direction
   - Cascade edges (connecting a REFUTED source to a cascaded target): turn red (#EF4444), add a bright sweep animation traveling along the edge direction to visualize failure propagation

3. LOADING STATE: While the pipeline is ingesting source or extracting claims (before any nodes appear), show a centered loading indicator with live status text: "Fetching TeX source...", "Extracting claims...", "Building dependency graph..."

4. NODE TOOLTIP: On hover (not click), show a small tooltip with: full claim text preview (first 120 chars), claim type, current confidence score if verdict is available.

5. MINIMAP: Add React Flow minimap in bottom-left. Minimap node colors should match the main node state colors.

6. SUMMARY BAR: Animate count changes — when a number increments, briefly flash the badge (scale up, then back to normal, CSS keyframe).

7. COMPLETION STATE: When REVIEW_COMPLETE fires:
   - Show a banner at top: "Review complete — {n} claims analyzed"
   - Enable "Download Report (MD)" button that fetches /review/{jobId}/report/markdown and triggers browser download
   - Nodes stop pulsing. All edges stop animating except cascade edges which stay red.

8. EMPTY STATE: If the job is not found or errored, show a clear error state with a "Start new review" button.

9. RESPONSIVE: The 75/25 split becomes a 60/40 split on smaller viewports. Activity feed collapses to an icon-only bar below 768px with a toggle to expand.
```

---

## PHASE 4 — Reader Mode

### Prompt 4.1 — Reader Mode agents

```
Implement the five Reader Mode agents. Each agent follows the same BaseAgent interface.

1. ExplainerAgent (backend/agents/explainer.py):
INPUT: ClaimUnit dict + comprehension_level (Literal["layperson","undergraduate","graduate","expert"])
OUTPUT: {"explanation": str, "key_insight": str, "worked_example": str | null}

System prompt: "You are a mathematical expositor. Explain this claim at the specified level. 
- layperson: no equations, use everyday analogies, focus on what the result means
- undergraduate: minimal jargon, one intuitive example, light formalism
- graduate: full formalism, proof sketch, connection to standard results
- expert: terse, assume full background, focus on what's novel or surprising
Return JSON with: explanation (full explanation at level), key_insight (one sentence core takeaway), worked_example (a concrete example if applicable, null otherwise)."

2. PrerequisiteMapperAgent (backend/agents/prerequisite_mapper.py):
INPUT: ClaimUnit dict
OUTPUT: {"prerequisites": [{"concept": str, "description": str, "resource_links": [str]}]}

System prompt: "Identify mathematical concepts from OUTSIDE this paper that a reader needs to understand this claim. For each, provide: concept name, one-sentence description, and 1-2 resource links. For resource links, use real Wikipedia URLs (https://en.wikipedia.org/wiki/[Topic]) for fundamental concepts. Return JSON array."

After getting GPT-4o response, validate each Wikipedia URL with a HEAD request (use httpx async). Replace any 404 links with the Wikipedia search URL for that concept.

3. GlossaryAgent (backend/agents/glossary_agent.py):
INPUT: ClaimUnit dict
OUTPUT: {"glossary": {"term": "definition", ...}}

System prompt: "Extract all non-standard mathematical terms from this claim text and provide one-sentence definitions. Include notation that may be unfamiliar. Return a JSON object mapping term → definition."

4. ExerciseGeneratorAgent (backend/agents/exercise_generator.py):
INPUT: ClaimUnit dict + comprehension_level
OUTPUT: {"exercises": [Exercise dict, ...]}

Exercise types to generate (generate one of each if applicable):
- conceptual: "Which of the following correctly interprets this claim? (A)... (B)... (C)..." type:counterexample_mcq
- computational: a numerical or algebraic calculation that tests the claim. type:computational
- proof_fill: "Fill in the missing step: Given X, we know Y because ___." type:proof_fill

System prompt: "Generate 2-3 exercises to test understanding of this mathematical claim at the given level. Return JSON array of Exercise objects with fields: prompt, exercise_type, answer_key."

5. SocraticTutorAgent (backend/agents/socratic_tutor.py):
INPUT: ClaimUnit dict + user_message (str) + conversation_history (list of {role, content})
OUTPUT: {"response": str}

System prompt: "You are a Socratic math tutor. The student is asking about a specific claim from a paper. Your job is to guide them to understanding through questions and targeted explanations — not to just give answers. Stay strictly scoped to this claim. If the student's objection reveals a genuine gap in the claim, acknowledge it. Be concise. Return JSON: {response: str}"

Include conversation_history in the messages array for context.
```

### Prompt 4.2 — Reader Mode orchestrator + API

```
Implement ReaderOrchestrator and Reader Mode API routes.

READER ORCHESTRATOR (backend/core/orchestrators/reader.py):
1. Runs the shared pipeline (TexParser → ClaimExtractor → DAGBuilder) on the submitted arXiv paper
2. Identifies entry-point claims: root nodes (no intra-paper dependencies) that also have the fewest prerequisites (initially estimated by claim complexity — shorter claims with no equations are simpler)
3. Marks those 1-3 claims as "start_here" in the session state
4. Does NOT pre-generate annotations for all claims — annotations are generated lazily on demand when the user clicks a node (to save cost)
5. Caches all generated ClaimAnnotations in the session store keyed by (session_id, claim_id)

READER SESSION STORE: 
Add reader sessions to job_store.py:
{
  "session_id": str,
  "status": str,
  "comprehension_level": ComprehensionLevel,
  "claims": {claim_id: ClaimUnit},
  "dag": DAG,
  "annotations": {claim_id: ClaimAnnotation},   # populated lazily
  "comprehension_states": {claim_id: ComprehensionStatus},
  "start_here": [claim_id],
  "paper_metadata": dict
}

API ROUTES (backend/api/reader.py):

POST /read
- Accept: arXiv URL/id + form field "level" (default: "undergraduate")
- Create session, launch ReaderOrchestrator as background task
- Return: {"session_id": str, "status": "processing"}

GET /read/{session_id}/dag
- Return DAG snapshot with comprehension_status overlay per node
- Include start_here flags
- Same format as review DAG but with comprehension_status instead of verdict

GET /read/{session_id}/claim/{claim_id}
- If annotation cached: return it immediately
- If not cached: run all 4 agents in parallel (Explainer, PrerequisiteMapper, GlossaryAgent, ExerciseGenerator) using asyncio.gather
- Cache result in session store
- Return full ClaimAnnotation dict
- Typical latency target: < 15s

POST /read/{session_id}/claim/{claim_id}/tutor
- Body: {"message": str, "history": [{role, content}]}
- Run SocraticTutorAgent
- Return {"response": str}

POST /read/{session_id}/claim/{claim_id}/grade
- Body: {"exercise_id": str, "answer": str}
- GPT-4o grading call: compare answer to answer_key, return {correct: bool, feedback: str}
- Update exercise in session store

PATCH /read/{session_id}/claim/{claim_id}/status
- Body: {"status": "understood" | "in_progress" | "flagged"}
- Update comprehension_states in session store
- Return updated state

GET /read/{session_id}/study-guide
- Compile all visited ClaimAnnotations into a structured markdown study guide:
  - Paper title and metadata
  - Comprehension progress summary
  - Per-claim sections (in topological order): explanation, prerequisites, exercises with answers
  - Full glossary (deduplicated across all claims)
  - Prerequisite reading list (deduplicated, ordered by how many claims depend on each concept)
- Return as text/markdown
```

### Prompt 4.3 — Reader Mode UI

```
Add Reader Mode UI to the frontend.

The mode selector in the header should now switch between Review and Reader modes. Reader mode has a distinct but related visual feel — same dark theme but warmer (slight navy → dark teal shift in backgrounds).

NEW COMPONENTS:

1. ReaderPage at route /read/:sessionId:
   - Same layout as ReviewPage (DAG canvas + side panel)
   - DAG nodes colored by comprehension status instead of verdict:
     - unvisited: #374151 (dark grey)
     - in_progress: #1D4ED8 (blue)
     - understood: #15803D (green)  
     - flagged: #B45309 (amber)
   - "Start here" nodes have a small ★ badge and a subtle glow
   - No activity feed; instead: a "Progress" panel showing comprehension stats

2. ReaderNodePanel (replaces NodeDetailPanel in reader mode):
   Tabs at top: [Explain] [Prerequisites] [Exercises] [Tutor]
   
   EXPLAIN TAB:
   - Level selector: Layperson / Undergraduate / Graduate / Expert (pills)
   - Renders the explanation markdown
   - Key insight highlighted in a callout box
   - Worked example in a code-style block
   - Loading skeleton while fetching
   
   PREREQUISITES TAB:
   - List of prerequisite cards: concept name + description + "Learn →" link
   - Empty state: "No external prerequisites identified"
   
   EXERCISES TAB:
   - Each exercise as a card with the prompt
   - Text input or MCQ depending on type
   - Submit button → calls /grade → shows ✓ or ✗ with feedback
   - Completed exercises show answer key inline
   
   TUTOR TAB:
   - Chat interface scoped to this claim
   - Message history displayed as chat bubbles
   - Input at bottom: "Ask about this claim..."
   - Calls POST /read/{sessionId}/claim/{claimId}/tutor
   - Loading state while waiting for response

3. ProgressPanel (replaces ActivityFeed in reader mode):
   - Claims understood: {n}/{total} with a progress bar
   - Claims flagged: list of claim IDs with click-to-navigate
   - "Export Study Guide" button at bottom → fetches /read/{sessionId}/study-guide → downloads as .md

4. Comprehension status controls on each node:
   - On hover: show three small icon buttons: ✓ (understood) / ⟳ (in progress) / ⚑ (flagged)
   - Clicking updates status via PATCH endpoint and immediately recolors the node

Transitions between Review and Reader mode (when both are available for the same paper) should be smooth — the DAG canvas position and zoom state should be preserved.
```

---

## PHASE 5 — Research Mode

### Prompt 5.1 — Literature retrieval + knowledge graph

```
Implement LiteratureSearchAgent and KnowledgeGraphAgent.

LITERATURE SEARCH AGENT (backend/agents/literature_search.py):
INPUT: query string (research question or topic)
OUTPUT: {"papers": [{"arxiv_id": str, "title": str, "abstract": str, "authors": [str], "year": int, "pdf_url": str, "relevance_score": float}]}

IMPLEMENTATION:
1. Use the Semantic Scholar API (no auth required for basic use):
   GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}&fields=title,abstract,authors,year,openAccessPdf&limit=20
2. Use httpx.AsyncClient for the request.
3. Rank results by relevance: use sentence-transformers (all-MiniLM-L6-v2) to embed the query and each abstract, compute cosine similarity, sort descending.
4. Filter to top 10 by relevance score > 0.3.
5. For papers with openAccessPdf, include the PDF URL. For others, construct arXiv URL if arxiv_id is available.
6. Return ranked list.
7. Graceful degradation: if Semantic Scholar is down or rate-limited (429), fall back to arXiv API: GET http://export.arxiv.org/api/query?search_query=all:{query}&max_results=10

KNOWLEDGE GRAPH AGENT (backend/agents/knowledge_graph.py):
INPUT: list of paper dicts (from LiteratureSearchAgent) + already-extracted claims from prior sessions (optional, for incremental updates)
OUTPUT: {"nodes": [KnowledgeNode dicts], "cross_paper_edges": [...], "contradictions": [...]}

IMPLEMENTATION:
1. For each paper: run the Parser → ClaimExtractor pipeline to get ClaimUnits. Run in parallel across papers with asyncio.gather (max 5 concurrent to avoid API rate limits).
2. Assign globally unique claim IDs: "{arxiv_id}_claim_001" etc.
3. Build intra-paper edges (from each paper's DAGBuilderAgent output).
4. Build cross-paper edges: for each pair of claims across different papers, use GPT-4o to detect:
   - SUPPORTS: claim A from paper X supports claim B from paper Y
   - CONTRADICTS: claim A and claim B assert incompatible results
   - EXTENDS: claim B generalizes or extends claim A
   Use batched prompts (compare 10 claim pairs per GPT-4o call) to reduce API calls.
5. Flag CONTRADICTS pairs as contradictions in the output.
6. Use NetworkX to store the full graph (pip install networkx).
7. Return serializable node/edge lists.
```

### Prompt 5.2 — Gap detection + hypothesis generation

```
Implement GapDetectorAgent and HypothesisGeneratorAgent.

GAP DETECTOR AGENT (backend/agents/gap_detector.py):
INPUT: KnowledgeGraph output (nodes + edges + contradictions) + original research query
OUTPUT: {"gaps": [{"gap_id": str, "description": str, "type": "open_problem"|"contradiction"|"underexplored", "supporting_evidence": [str], "relevant_claim_ids": [str]}]}

IMPLEMENTATION:
1. Build a compressed summary of the knowledge graph for GPT-4o:
   - List all CONTRADICTS pairs with the claim texts
   - List all "leaf" nodes (claims with no outgoing EXTENDS or SUPPORTS edges — these are frontier results with nothing built on them)
   - List claims that cite "future work" or "open problem" language (scan claim texts for these phrases)
2. System prompt: "You are a research gap analyst. Given this knowledge graph summary of a research area, identify:
   1. Open problems: explicitly stated unsolved questions
   2. Contradictions: pairs of results that conflict and haven't been reconciled
   3. Underexplored directions: frontier results with no follow-up work in the graph
   For each gap, describe it precisely, explain why it matters, and cite the relevant claims. Return JSON array."
3. Assign sequential gap IDs: "gap_001", etc.

HYPOTHESIS GENERATOR AGENT (backend/agents/hypothesis_generator.py):
INPUT: list of Gap dicts + research query
OUTPUT: {"hypotheses": [Hypothesis dicts]}

IMPLEMENTATION:
1. For each gap (up to 3), generate one hypothesis with GPT-4o.
2. System prompt: "You are a mathematical researcher. Given this research gap, propose a precise, falsifiable conjecture that would address it. The conjecture must:
   - Be specific enough to attempt a proof or disproof
   - State clearly what would constitute a counterexample
   - Identify what proof approach (induction, construction, contradiction, numeric) seems most promising
   Return JSON: {text: str, falsification_strategy: str, proof_approach: str, confidence_prior: float 0-1}"
3. Populate the Hypothesis Pydantic model. Set status="proposed", user_approved=False.
4. Pre-filter: if GPT-4o's confidence_prior < 0.2 or the hypothesis is trivially related to a known SUPPORTED claim in the graph, skip it and try the next gap.
5. Return up to 3 hypotheses max per session.
```

### Prompt 5.3 — Proof strategy + research memory + draft writer

```
Implement ProofStrategyAgent, ResearchMemoryAgent, and DraftWriterAgent.

PROOF STRATEGY AGENT (backend/agents/proof_strategy.py):
INPUT: Hypothesis dict + ResearchSession working_memory
OUTPUT: {"proof_attempt": str, "verification_results": [VerificationResult dicts], "status": "proven"|"disproven"|"inconclusive"}

IMPLEMENTATION:
1. Based on hypothesis.proof_approach, scaffold a proof structure with GPT-4o:
   - induction: generate base case check + inductive step as SymPy expressions where possible
   - construction: generate a specific construction as a Python function for numeric testing
   - contradiction: generate the negation of the hypothesis and attempt to derive a contradiction
   - numeric: generate boundary test cases
2. Extract any SymPy-testable expressions from the proof scaffold → run SymbolicVerifierAgent
3. Extract any numerically testable predicates → run NumericAdversaryAgent
4. Use GPT-4o to synthesize: given the verification results + proof scaffold, is the hypothesis proven, disproven, or inconclusive?
5. Return the full proof attempt text and combined VerificationResults.

RESEARCH MEMORY AGENT (backend/agents/research_memory.py):
This agent is stateful — it holds and updates the session working memory.

Methods (not just run()):
- record_hypothesis_attempt(hypothesis_id, result, reason)
- record_retrieved_paper(arxiv_id)
- is_already_tried(hypothesis_text) → bool (fuzzy match using sentence-transformers)
- get_dead_ends() → list of failure reasons
- get_summary() → str (compact summary for injecting into other agent prompts)

Store as a dict in the ResearchSession model. Serialize to JSON for persistence.

DRAFT WRITER AGENT (backend/agents/draft_writer.py):
INPUT: list of proven/accepted Hypothesis dicts + KnowledgeGraph + research query
OUTPUT: {"markdown": str, "title": str, "abstract": str}

IMPLEMENTATION:
1. System prompt: "You are a mathematical research note writer. Given these proven conjectures, the knowledge graph context, and the original research question, write a structured research note in markdown. Include:
   # Title
   ## Abstract (3-4 sentences)
   ## Background (what was known, citing source papers)
   ## Main Results (each accepted hypothesis as a proposition with proof sketch)
   ## Limitations and Future Work
   ## References
   Be precise and technical. Use LaTeX notation inline ($...$). This will be submitted to adversarial review — make it defensible."
2. Return the full markdown string as output.
```

### Prompt 5.4 — Research Mode orchestrator + API

```
Implement ResearchDirectorAgent and Research Mode API routes.

RESEARCH DIRECTOR (backend/core/orchestrators/research.py):
This is the outer loop controller. Max 5 iterations.

LOOP STRUCTURE:
async def run_research_loop(session_id, query):
  memory = ResearchMemoryAgent()
  
  # Step 1: Literature retrieval
  papers = await LiteratureSearchAgent.run(query)
  memory.record_retrieved_papers(papers)
  emit_event(session_id, "papers_retrieved", {count: len(papers)})
  
  # Step 2: Knowledge graph
  kg = await KnowledgeGraphAgent.run(papers)
  emit_event(session_id, "knowledge_graph_built", {nodes: len(kg.nodes)})
  
  for iteration in range(MAX_ITERATIONS=5):
    # Step 3: Gap detection
    gaps = await GapDetectorAgent.run(kg, query)
    emit_event(session_id, "gaps_detected", {gaps: gaps})
    
    # Step 4: Hypothesis generation  
    hypotheses = await HypothesisGeneratorAgent.run(gaps, query)
    # Filter already-tried hypotheses
    hypotheses = [h for h in hypotheses if not memory.is_already_tried(h.text)]
    
    if not hypotheses:
      break  # exhausted generatable hypotheses
    
    # Step 5: Store hypotheses, await human approval (set status=proposed)
    store_hypotheses(session_id, hypotheses)
    emit_event(session_id, "hypotheses_ready", {hypotheses: [h.dict() for h in hypotheses]})
    
    # PAUSE — wait for user approval via API endpoint
    approved = await wait_for_approval(session_id, timeout=3600)  # 1 hour timeout
    
    if not approved:
      break
    
    # Step 6: Proof attempts on approved hypotheses
    results = await asyncio.gather(*[
      ProofStrategyAgent.run(h, memory) for h in approved
    ])
    
    for h, result in zip(approved, results):
      memory.record_hypothesis_attempt(h.hypothesis_id, result.status, result.proof_attempt)
      emit_event(session_id, "proof_complete", {hypothesis_id: h.hypothesis_id, status: result.status})
    
    proven = [h for h, r in zip(approved, results) if r.status == "proven"]
    if proven:
      break  # have results to write up
  
  # Step 7: Draft + self-review
  if proven_hypotheses:
    draft = await DraftWriterAgent.run(proven_hypotheses, kg, query)
    emit_event(session_id, "draft_complete", {})
    
    # Self-review: run full Review Mode pipeline on the draft
    # Pass draft text to the self-review path
    self_review = await SelfReviewAgent.run(draft.markdown, proven_hypotheses)
    emit_event(session_id, "self_review_complete", {verdict_summary: self_review.summary})
  
  emit_event(session_id, "research_complete", {})

For wait_for_approval: use an asyncio.Event stored in the session. The approval API endpoint sets it.

RESEARCH API ROUTES (backend/api/research.py):

POST /research
- Body: {"query": str}
- Create ResearchSession in store, launch loop as background task
- Return: {"session_id": str, "status": "running"}

GET /research/{session_id}/stream
- SSE stream of research loop events
- Event types: papers_retrieved, knowledge_graph_built, gaps_detected, hypotheses_ready, proof_complete, draft_complete, self_review_complete, research_complete

GET /research/{session_id}/hypotheses
- Return list of hypotheses with status="proposed"

POST /research/{session_id}/hypotheses/{hypothesis_id}/approve
- Set hypothesis status="approved", trigger the waiting asyncio.Event

POST /research/{session_id}/hypotheses/{hypothesis_id}/reject
- Set hypothesis status="rejected", record in memory

GET /research/{session_id}/note
- Return {"markdown": str, "self_review": ReviewReport dict}

GET /research/{session_id}/knowledge-graph
- Return full KG snapshot: nodes, edges, contradictions
```

### Prompt 5.5 — Research Mode UI

```
Build Research Mode UI.

NEW COMPONENTS:

1. ResearchPage at route /research/:sessionId (and a landing at /research for starting a new session):

LANDING STATE (no session yet):
- Large centered input: "Enter a research question or topic"
- Placeholder: "e.g. What are open problems in spectral graph theory related to expanders?"
- Submit button → POST /research → redirect to /research/:sessionId
- Below: "or upload a paper to analyze" → links to Review Mode

SESSION STATE layout:
- Left panel (40%): Research timeline / progress feed
- Right panel (60%): Main content area (changes per phase)

2. ResearchTimeline component (left panel):
Vertical timeline showing the loop phases. Each phase is a step:
  ○ Searching literature...
  ● Knowledge graph built (12 papers, 47 claims)
  ● Gaps detected (3 gaps found)  
  ⏸ Awaiting your input — 2 hypotheses ready for review
  ○ Proof attempts
  ○ Writing research note
  ○ Self-review

Active step pulses. Completed steps show a checkmark. The "Awaiting your input" step glows amber.

3. HypothesisApprovalPanel (right panel, shown when hypotheses_ready fires):
For each hypothesis, a card showing:
  - Hypothesis text (full)
  - Falsification strategy
  - Proposed proof approach badge
  - Prior confidence estimate as a meter
  - [Approve] and [Reject] buttons
  - Approved hypotheses show a green checkmark; rejected show strikethrough

4. KnowledgeGraphView (right panel, togglable):
- Render the cross-paper knowledge graph using React Flow
- Nodes colored by source paper (each paper gets a distinct hue)
- Contradiction edges highlighted red
- SUPPORTS/EXTENDS edges in grey/blue
- Toggle button to switch between this view and the timeline

5. ResearchNotePanel (right panel, shown after draft_complete):
- Render markdown research note with syntax highlighting (use react-markdown + remark-math + rehype-katex for LaTeX rendering)
- npm install react-markdown remark-math rehype-katex katex
- Self-review verdict shown as a banner below: SUPPORTED / CONTESTED / REFUTED badge with key findings
- "Download Note" button
- "View Full Self-Review" expands a ReviewPage-style verdict breakdown for the draft

6. Activity feed (live, replaces timeline detail):
Stream all research events in plain language:
"📚 Retrieved 12 papers from Semantic Scholar"
"🔗 Built knowledge graph: 47 claims across 12 papers"  
"⚠️ Contradiction detected: [Smith 2021] vs [Jones 2022] on Lemma 3"
"💡 2 hypotheses generated — your approval needed"
"🔬 Proof attempt: induction approach on Hypothesis 1"
"✓ Hypothesis 1 verified (confidence 0.83)"
"📝 Research note drafted"
"⚖️ Self-review: SUPPORTED with 1 contested claim"
```

---

## PHASE 6 — Polish

### Prompt 6.1 — Mode switcher + unified session

```
Add a unified mode switcher so users can switch between Review and Reader modes for the same submitted paper.

BACKEND:
1. Add a unified session concept: when an arXiv paper is submitted via /review, also create a reader session for the same paper and link the two by paper_hash.
2. Add GET /paper/{paper_hash}/sessions → returns {review_job_id, reader_session_id} if both exist.
3. The DAG data (claims + edges) should be computed once and shared between modes — store it in a shared paper_store keyed by paper_hash.

FRONTEND:
1. When on ReviewPage or ReaderPage, the mode tabs in the header should be active (not dimmed) once both sessions exist for this paper.
2. Switching tabs should navigate to the other mode's page while preserving the DAG zoom/pan state.
3. The mode switch should be a smooth cross-fade transition, not a hard page reload.
4. Add a URL parameter ?claim=claim_id so clicking a node and sharing the URL opens the same paper in the same mode with the same node panel open.
```

### Prompt 6.2 — RAGRetrievalAgent (complete implementation)

```
Complete the RAGRetrievalAgent implementation in backend/agents/rag_retrieval.py.

INPUT: ClaimUnit dict.
OUTPUT: VerificationResult with tier="semantic" and evidence listing retrieved contradicting/supporting passages.

IMPLEMENTATION:
1. Use sentence-transformers to embed the claim text (model: all-MiniLM-L6-v2).
2. Query a ChromaDB collection (pip install chromadb) containing arXiv abstracts.
3. For the vector store: on first run, if the collection doesn't exist, populate it from a small seed corpus:
   - Download abstracts for 50 highly-cited papers in math/physics using the Semantic Scholar API
   - Embed and store each abstract as a document with metadata: paper_id, title, year
   - This build step should run as a one-time setup script at backend/scripts/build_rag_corpus.py
4. Query the collection for top-5 nearest neighbors.
5. Use GPT-4o to assess each retrieved passage: "Does this passage contradict, support, or is irrelevant to the given claim? Return JSON: {relationship: 'contradicts'|'supports'|'irrelevant', explanation: str}"
6. If any passage contradicts: status="failed", evidence lists the contradicting passages.
7. If no contradiction and ≥1 support: status="passed".
8. If all irrelevant: status="inconclusive".
```

### Prompt 6.3 — Error handling + observability

```
Add production-quality error handling and observability across the backend.

1. STRUCTURED LOGGING: Replace all print() calls with Python's logging module. Use a JSON formatter (pip install python-json-logger). Every log entry should include: timestamp, level, agent_id (if in agent context), job_id/session_id (if available), message, duration_ms (for agent run() calls).

2. AGENT TIMEOUT WRAPPER: Add a timeout decorator to BaseAgent.run(). Default timeout: 60 seconds. If an agent times out, return AgentResult with status="error", error="timeout after 60s" rather than raising. Log the timeout with agent_id and claim_id.

3. COST TRACKING: Add a simple cost tracker. Every GPT-4o API call should record: agent_id, input_tokens, output_tokens, estimated_cost (use $0.005/1K input, $0.015/1K output). Store per job_id. Expose via GET /review/{job_id}/cost.

4. JOB CLEANUP: Add a background task that runs every 5 minutes and deletes temp source files + event bus channels for jobs older than 2 hours.

5. HEALTH CHECK: Add GET /health → {"status": "ok", "agents": int, "active_jobs": int, "uptime_seconds": float}

6. RETRY LOGIC: For all OpenAI API calls, add exponential backoff retry (max 3 attempts) using tenacity (pip install tenacity). Only retry on rate limit (429) and server errors (500, 503). Do not retry on 400 (bad request — indicates a prompt issue).

7. FRONTEND ERROR STATES: For every fetch call in the React frontend, add error boundary handling. If an SSE stream errors, show a toast notification and offer a "Reconnect" button that re-subscribes from the last received event_id.
```

---

## PHASE 7 — PoC Mode

### Prompt 7.1 — ClaimFilterAgent + MetricExtractorAgent

```
Implement ClaimFilterAgent and MetricExtractorAgent in backend/agents/claim_filter.py and backend/agents/metric_extractor.py.

CLAIM FILTER AGENT:
INPUT: List of ClaimUnit dicts (full DAG output from Phase 1).
OUTPUT: AgentResult where output contains:
{
  "testable": [claim_id, ...],
  "theoretical": [claim_id, ...],
  "classifications": {claim_id: {"testability": "testable"|"theoretical", "reason": str}}
}

A claim is TESTABLE if it contains at least one of:
- A quantitative performance bound (e.g. "achieves 94.3% accuracy", "reduces error by 40%")
- An algorithmic complexity assertion (e.g. "runs in O(n log n)", "converges in O(1/ε²) iterations")
- A benchmark comparison (e.g. "outperforms baseline X by Y%")
- A convergence result with a numeric rate
- A resource usage claim (memory, time, FLOPs)

A claim is THEORETICAL if it is:
- A pure existence result ("there exists...")
- An algebraic identity or inequality without experimental context
- A structural result (graph properties, topological claims)
- A definition or notation introduction

IMPLEMENTATION:
1. Use GPT-4o. For each claim, include the full claim text in a batch prompt (process up to 10 claims per API call to reduce cost).
2. System prompt: "Classify each mathematical/algorithmic claim as 'testable' (can be verified by running an experiment and measuring a metric) or 'theoretical' (requires mathematical proof only). For testable claims, briefly state what experiment would verify it. Return a JSON array: [{claim_id, testability, reason}]"
3. Parse and validate. If classification is ambiguous, default to 'theoretical' (conservative — don't generate scaffolds for claims that can't actually be tested).
4. Return the split lists and full classification dict.

---

METRIC EXTRACTOR AGENT:
INPUT: A single testable ClaimUnit dict.
OUTPUT: AgentResult where output contains a PoCSpec dict (partial — no scaffold_files yet):
{
  "spec_id": str,
  "claim_id": str,
  "testability": "testable",
  "success_criteria": [MetricCriterion dict, ...],
  "failure_criteria": [MetricCriterion dict, ...]
}

MetricCriterion fields: metric_name, paper_reported_value (string as in paper), numeric_threshold (float), tolerance (float, default 0.02), comparison ("gte"|"lte"|"eq"|"within_tolerance"), experimental_conditions (dict of dataset/hyperparams).

IMPLEMENTATION:
1. System prompt: "Extract all quantitative success and failure criteria from this claim. For each metric:
   - metric_name: what is being measured (e.g. 'top-1 accuracy', 'training time', 'memory usage')
   - paper_reported_value: exact string from paper (e.g. '94.3% on ImageNet')
   - numeric_threshold: the numeric value as a float
   - tolerance: how much deviation counts as reproduction (default 0.02 = 2% relative)
   - comparison: 'gte' if the metric should be >= threshold, 'lte' if <=, 'within_tolerance' if ± tolerance
   - experimental_conditions: dict of required conditions stated in paper (dataset, model size, batch size, etc.)
   Return JSON: {success_criteria: [...], failure_criteria: [...]}
   Failure criteria = the negation of success criteria plus any explicit failure conditions stated."
2. If numeric_threshold cannot be extracted (e.g. claim says "significantly better" with no number), set numeric_threshold=null and mark the criterion as unverifiable in a note field. Do not fabricate numbers.
3. Validate all MetricCriterion objects against the Pydantic model.
4. Return the partial PoCSpec.
```

### Prompt 7.2 — ScaffoldGeneratorAgent

```
Implement ScaffoldGeneratorAgent in backend/agents/scaffold_generator.py.

INPUT: PoCSpec dict (with success_criteria populated) + the full ClaimUnit dict + paper metadata (title, abstract, relevant sections from TexParserAgent output).
OUTPUT: AgentResult where output contains the completed PoCSpec with scaffold_files populated:
{
  "scaffold_files": {
    "implementation.py": str,    // core method implementation
    "test_harness.py": str,      // pytest-based test file with assertions
    "results_logger.py": str,    // utility to log results as JSON
    "requirements.txt": str,     // dependencies
    "README.md": str             // how to run
  }
}

IMPLEMENTATION:

Generate each file separately with a focused GPT-4o call. Use gpt-4o for all generation.

FILE 1 — implementation.py:
System prompt: "You are implementing a research paper's method in Python. Generate clean, runnable code that implements the algorithm/method described in the claim and surrounding paper context. 
Requirements:
- Include detailed inline comments referencing specific paper sections (e.g. # See Section 3.2: Algorithm 1)
- Add a comment at the top: # Implements claim {claim_id}: {first 100 chars of claim text}
- Use only standard Python + numpy + torch/sklearn as appropriate — no obscure dependencies
- Include a main() function that runs a minimal demonstration
- If the full method is too complex for one file, implement the core component that tests the specific claim
Return ONLY the Python code, no explanation."
User prompt: claim text + relevant paper sections + success criteria as context.

FILE 2 — test_harness.py:
System prompt: "Generate a pytest test file that verifies the success criteria for this claim. 
Requirements:
- Import from implementation.py
- One test function per success criterion: def test_{metric_name}():
- Each test function must call the implementation, measure the metric, and assert the criterion
- Use the exact numeric thresholds and tolerances provided
- Add a comment before each assert: # Paper reports: {paper_reported_value}
- Include a results collection dict that accumulates all metrics for the logger
- At the end of all tests, call save_results() from results_logger.py
Return ONLY the pytest code."
User prompt: PoCSpec success_criteria as JSON + implementation.py content.

FILE 3 — results_logger.py:
Simple utility — generate directly without LLM:
- save_results(results: dict, output_path: str = "poc_results.json")
- Writes: {claim_id, timestamp, metrics: {metric_name: value}, status per criterion, system_info}

FILE 4 — requirements.txt:
GPT-4o: scan implementation.py and test_harness.py for imports, generate minimal requirements.txt.

FILE 5 — README.md:
System prompt: "Write a clear README for this proof-of-concept scaffold. Include: what claim this tests, setup instructions (pip install -r requirements.txt), how to run (pytest test_harness.py -v), how to interpret results, and what the success criteria are. Be concise — max 40 lines."

After generating all files, run a basic syntax check on implementation.py and test_harness.py using Python's `ast.parse()`. If syntax errors are found, attempt one GPT-4o correction pass. If still broken, include the error in the AgentResult output and set status="inconclusive".
```

### Prompt 7.3 — ResultsAnalyzerAgent + ReproducibilityReportAgent

```
Implement ResultsAnalyzerAgent and ReproducibilityReportAgent.

RESULTS ANALYZER AGENT (backend/agents/results_analyzer.py):
INPUT: uploaded results JSON (as dict) + list of PoCSpec dicts for the session.
OUTPUT: AgentResult where output contains:
{
  "results": [ExperimentResult dict, ...],
  "claim_statuses": {claim_id: ReproductionStatus}
}

Expected results JSON format (produced by results_logger.py):
{
  "claim_id": str,
  "timestamp": str,
  "metrics": {"metric_name": float, ...},
  "system_info": {...}
}

IMPLEMENTATION:
1. For each ExperimentResult in the uploaded JSON:
   a. Find the corresponding PoCSpec by claim_id
   b. For each success criterion in the spec:
      - Fetch the achieved value from metrics dict (match by metric_name)
      - Evaluate the criterion: gte/lte/within_tolerance comparison against numeric_threshold
      - Compute delta = achieved_value - numeric_threshold
      - Determine status:
        * REPRODUCED: criterion passes
        * PARTIAL: within 2x the tolerance (right direction, close miss)
        * FAILED: outside 2x tolerance or metric missing entirely
   c. Overall claim status = worst status across all its criteria
2. If a metric is missing from the results JSON, status = FAILED with error_message = "metric not found in results"
3. Return all ExperimentResult objects and the claim_statuses dict.

REPRODUCIBILITY REPORT AGENT (backend/agents/reproducibility_report.py):
INPUT: list of ExperimentResult dicts + list of PoCSpec dicts + paper metadata.
OUTPUT: AgentResult where output contains a ReproducibilityReport dict.

IMPLEMENTATION:
1. Compute summary stats: total_testable, reproduced, partial, failed, reproduction_rate.
2. For each non-REPRODUCED claim, generate a gap analysis using GPT-4o:
   System prompt: "A researcher attempted to reproduce this paper's claim but got a different result. Analyze the likely causes. Return JSON: {explanations: [{explanation: str, likelihood: 'high'|'medium'|'low', suggested_fix: str}]} ordered by likelihood descending."
   User prompt: claim text + success criterion + paper_reported_value + achieved_value + experimental_conditions.
3. Generate "what_to_try_next" list with GPT-4o: given all failed/partial claims and their gap analyses, what are the top 3–5 concrete next steps to improve reproduction rate?
4. Generate markdown report with GPT-4o:
   Include: executive summary with reproduction rate, per-claim status table (claim_id | type | paper_value | your_value | status | delta), gap analysis for failures, what to try next.
5. Populate and return the full ReproducibilityReport Pydantic model.
```

### Prompt 7.4 — PoCOrchestrator + API routes

```
Implement PoCOrchestrator and PoC Mode API routes.

POC ORCHESTRATOR (backend/core/orchestrators/poc.py):
1. Run shared pipeline: Parser → ClaimExtractor → DAGBuilder (same as other modes)
2. Run ClaimFilterAgent on all claims
3. Run MetricExtractorAgent in parallel on all testable claims (asyncio.gather)
4. Run ScaffoldGeneratorAgent in parallel on all testable claims (asyncio.gather, max 5 concurrent)
5. Package all scaffold files into a zip (use Python zipfile stdlib):
   - One folder per claim: poc_scaffold/{claim_id}/
   - Each folder contains: implementation.py, test_harness.py, results_logger.py, requirements.txt, README.md
   - Root README.md explaining the full project structure
6. Store PoCSpecs and zip path in session store
7. Emit DAGEvents for each step:
   - NODE_CLASSIFIED (testable/theoretical) for each claim
   - SCAFFOLD_GENERATED for each testable claim
   - POC_READY when zip is packaged

SESSION STORE for PoC:
{
  "session_id": str,
  "status": str,
  "paper_metadata": dict,
  "claims": {claim_id: ClaimUnit},
  "dag": DAG,
  "poc_specs": {claim_id: PoCSpec},
  "zip_path": str,
  "experiment_results": Optional[ReproducibilityReport]
}

API ROUTES (backend/api/poc.py):

POST /poc
- Accept arXiv URL/id
- Create session, launch PoCOrchestrator as background task
- Return: {"session_id": str, "status": "processing"}

GET /poc/{session_id}/stream
- SSE stream: node_classified, scaffold_generated, poc_ready events

GET /poc/{session_id}/claims
- Return all claims with their testability classification and PoCSpec summary (no scaffold_files — too large)
- Include counts: {total, testable, theoretical}

GET /poc/{session_id}/claim/{claim_id}/spec
- Return full PoCSpec including scaffold_files content for a single claim
- 404 if claim is theoretical

GET /poc/{session_id}/scaffold.zip
- Stream the zip file as application/zip
- Content-Disposition: attachment; filename="poc_scaffold_{paper_hash}.zip"

POST /poc/{session_id}/results
- Accept: multipart JSON file upload OR raw JSON body
- Validate against expected results format
- Run ResultsAnalyzerAgent + ReproducibilityReportAgent as background task
- Return: {"status": "analyzing"}

GET /poc/{session_id}/report
- Return ReproducibilityReport JSON
- 202 if analysis still in progress

GET /poc/{session_id}/report/markdown
- Return markdown report as text/markdown

GET /poc/{session_id}/dag
- Return DAG snapshot with reproduction_status overlay
- Nodes colored by: REPRODUCED/PARTIAL/FAILED/PENDING/theoretical
```

### Prompt 7.5 — PoC Mode UI

```
Build PoC Mode UI in the frontend.

Add [PoC] tab to the mode selector in the header. PoC Mode has a distinct visual feel within the same dark theme — use a slightly warmer tint (dark slate → dark olive) to signal "implementation" vs "theory".

NEW COMPONENTS:

1. PoCPage at route /poc/:sessionId:
Layout: DAG canvas (65%) + right panel (35%)
The right panel has two states: ClaimListPanel (default) and SpecPanel (when node clicked)

DAG nodes in PoC Mode have two visual tiers:
- Testable nodes: solid border, colored by reproduction status
  * PENDING: blue `#1D4ED8` (scaffold ready, not run)
  * REPRODUCED: green `#15803D`
  * PARTIAL: amber `#B45309`
  * FAILED: red `#DC2626`
- Theoretical nodes: dashed grey border, dimmed — clearly secondary

A "testable claims" filter toggle at the top of the canvas: when on, theoretical nodes collapse to dots.

2. ClaimListPanel (default right panel):
Summary bar: "{n} testable claims · {reproduced} reproduced · {partial} partial · {failed} failed"
Below: a list of testable claims, each showing:
- claim_id + claim_type badge
- Success criterion (first one, truncated)
- Status badge (PENDING/REPRODUCED/PARTIAL/FAILED)
- Click navigates to that node in the DAG and opens SpecPanel

At bottom: two CTAs:
- "Download Scaffold (.zip)" → GET /poc/{sessionId}/scaffold.zip
- "Upload Results" → opens upload modal (see below)

3. SpecPanel (opens on node click, replaces ClaimListPanel):
Tabs: [Spec] [Code] [Results]

SPEC TAB:
- Claim text (full, in a monospace block)
- Success Criteria table: metric | paper value | threshold | tolerance | comparison
- Experimental conditions as key-value pairs
- Failure Criteria (collapsible)

CODE TAB:
- File selector: implementation.py / test_harness.py / results_logger.py / README.md
- Syntax-highlighted code display (npm install react-syntax-highlighter)
- "Copy" button per file
- Language: python (or markdown for README)

RESULTS TAB (shows after results are uploaded):
If REPRODUCED: green banner "✓ Reproduced — within tolerance"
If PARTIAL: amber banner "⚠ Partial — close but outside tolerance"
If FAILED: red banner "✗ Failed to reproduce"
Below banner:
- Metric comparison table: metric | paper value | your value | delta | status
- Gap analysis (if PARTIAL or FAILED): expandable list of explanations with likelihood badges
- "What to try next" as a numbered list

4. UploadResultsModal:
- Drag-and-drop JSON file zone
- JSON preview (first 20 lines) before confirm
- On confirm: POST /poc/{sessionId}/results
- Progress indicator while analysis runs
- On complete: refreshes SpecPanel Results tab

5. ReproducibilityReportView (accessible via "View Full Report" button):
- Full markdown report rendered with react-markdown
- Export as .md button

6. Activity feed in PoC Mode (replaces generic feed):
"🔍 Classifying 14 claims for testability..."
"✓ 6 testable claims identified"  
"⚙ Generating scaffold for Theorem 3 (accuracy claim)..."
"📦 Scaffold ready — download available"
"📊 Results uploaded — analyzing..."
"✓ Theorem 3: REPRODUCED (94.1% achieved, threshold 94.3%, within tolerance)"
"⚠ Lemma 5: PARTIAL (78.2% achieved, threshold 80%, delta -1.8%)"
```

---

## Updated Build Order Checklist

```
Phase 0:  [ ] 0.1 Project scaffold
Phase 1:  [ ] 1.1 TexParserAgent
          [ ] 1.2 ClaimExtractorAgent  
          [ ] 1.3 DAGBuilderAgent
          [ ] 1.4 Pipeline integration test  ← CHECKPOINT
Phase 2:  [ ] 2.1 SymbolicVerifierAgent
          [ ] 2.2 NumericAdversaryAgent
          [ ] 2.3 AttackerAgent + sub-agents
          [ ] 2.4 DefenderAgent
          [ ] 2.5 VerdictAggregator + CascadeAgent
          [ ] 2.6 ReviewOrchestrator + ReportAgent
          [ ] 2.7 Review Mode API routes
Phase 3:  [ ] 3.1 React scaffold + DAG canvas  ← CHECKPOINT: live DAG in browser
          [ ] 3.2 Polish live DAG              ← DEMO READY
Phase 4:  [ ] 4.1 Reader Mode agents
          [ ] 4.2 Reader Mode orchestrator + API
          [ ] 4.3 Reader Mode UI
Phase 5:  [ ] 5.1 Literature retrieval + knowledge graph
          [ ] 5.2 Gap detection + hypothesis generation
          [ ] 5.3 Proof strategy + memory + draft writer
          [ ] 5.4 Research Mode orchestrator + API
          [ ] 5.5 Research Mode UI
Phase 6:  [ ] 6.1 Unified mode switcher
          [ ] 6.2 RAGRetrievalAgent (complete)
          [ ] 6.3 Error handling + observability
Phase 7:  [ ] 7.1 ClaimFilterAgent + MetricExtractorAgent
          [ ] 7.2 ScaffoldGeneratorAgent
          [ ] 7.3 ResultsAnalyzerAgent + ReproducibilityReportAgent
          [ ] 7.4 PoCOrchestrator + API routes
          [ ] 7.5 PoC Mode UI
```

## Hackathon Build Order (36 hours, 4 people)

For the hackathon, target only Phases 0–3 and 7.1–7.4 (PoC backend only, no UI).
Demo story: enter arXiv URL → live DAG review → download scaffold → show the zip contents.
PoC UI can be described verbally during pitch if not built in time.

```
Person A: Prompts 0.1, 1.1, 1.2, 1.3, 1.4
Person B: Prompts 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7 + mock SSE stream script
Person C: Prompts 3.1, 3.2
Person D: Prompts 7.1, 7.2, 7.3, 7.4 (PoC backend) + demo prep
```
