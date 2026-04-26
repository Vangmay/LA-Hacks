# PaperCourt × AXLE — Lean Formalization & Verification Plan

Status: **implemented on `vrathi101_axle`**. Kept as the design record for the
AXLE formalization feature.

## 1. Goal

Add a "Formalize & Verify" mode to PaperCourt that takes the existing
`ParsedPaper` + `ResearchAtom` graph and runs an **LLM-driven agentic loop**
that calls AXLE (Lean 4 verification API) to:

1. Generate a Lean 4 formal specification of each reviewable atom.
2. Iteratively repair the spec until `axle.check` compiles.
3. Generate a candidate proof using the paper's prose proof.
4. Iteratively repair / decompose the proof until `axle.verify_proof` accepts.
5. Emit a per-atom verdict (`fully_verified` / `conditionally_verified` /
   `formalized_only` / `disproved` / `formalization_failed` / `not_a_theorem`).
6. Stream **every step** to the frontend live so the user watches the LLM
   pick AXLE tools and react to their results.

Per-atom honesty matters more than blanket "the paper is verified" — the
verdict surface is intentionally fine-grained.

## 2. Design Principles

- **Total isolation.** All new backend code lives in `backend/formalization/`.
  All new frontend code lives in `frontend/src/features/formalization/`.
  Existing review code is touched in **at most three** locations
  (`backend/main.py` router registration, `backend/.env.example`,
  `frontend/src/pages/Review.jsx` to mount the new tab). This minimizes
  merge-conflict surface against teammates working on the review pipeline.
- **No edits to existing review models, agents, or orchestrator.**
  Formalization has its own models, store, event bus, and SSE channel.
- **Reuse data, not code.** We *read* `ParsedPaper`, `ResearchAtom`,
  `ResearchGraph`, `EquationBlock`, `SourceSpan` from `job_store`. We never
  modify them.
- **LLM calls follow existing conventions** (`AsyncOpenAI` from
  `core/openai_client.py`, `settings.openai_model`, JSON / tool-use modes,
  explicit error handling).
- **Per-atom verdicts only.** Never claim the paper is verified end-to-end.
- **Live, not batch.** Every LLM thought, tool call, and AXLE result is
  streamed via SSE so the demo is visibly working.

## 3. AXLE Reference (verified from docs)

**SDK:** `from axle import AxleClient` (already in `backend/requirements.txt`
as `axiom-axle`).

**Auth / config (env vars read by the client):**
```
AXLE_API_KEY            (required)
AXLE_API_URL            (defaults to https://axle.axiommath.ai)
AXLE_MAX_CONCURRENCY    (optional; client-side semaphore)
AXLE_TIMEOUT_SECONDS    (optional; per-call default)
```

**Usage pattern:** async context manager.
```python
async with AxleClient() as client:
    result = await client.check(content="...", environment="lean-4.28.0")
```

**Errors (all subclass `AxleApiError`):**
`AxleIsUnavailable` (503, auto-retried), `AxleRateLimitedError` (429,
auto-retried with backoff), `AxleInvalidArgument`, `AxleForbiddenError`,
`AxleNotFoundError`, `AxleConflictError`, `AxleInternalError`,
`AxleRuntimeError` (timeout/resource).

**Methods we will expose to the LLM as tools:**

| Method | Key params | Result fields |
|---|---|---|
| `check` | `content, environment, mathlib_options=False, ignore_imports=False, timeout_seconds=120` | `okay, content, lean_messages{errors,warnings,infos}, tool_messages, failed_declarations, timings` |
| `verify_proof` | `formal_statement, content, environment, permitted_sorries=[], use_def_eq=True, mathlib_options=False, ignore_imports=False, timeout_seconds=120` | `okay, content, lean_messages, tool_messages, failed_declarations, timings` |
| `repair_proofs` | `content, environment, names=None, repairs=None, terminal_tactics=['grind'], ignore_imports=False, timeout_seconds=120` | repaired content + messages |
| `sorry2lemma` | `content, environment, names=None, indices=None, extract_sorries=True, extract_errors=True, include_whole_context=True, reconstruct_callsite=False, timeout_seconds=120` | `content, lemma_names, messages` |
| `have2lemma` | `content, environment, names=None, indices=None, include_have_body=False, ...` | `content, lemma_names, messages` |
| `extract_decls` | `content, environment, ignore_imports=False, timeout_seconds=120` | `documents{name -> {kind, declaration, signature, type, type_hash, is_sorry, line_pos, end_line_pos, proof_length, tactic_counts, *_dependencies, declaration_messages}}` |
| `extract_theorems` | same as above | same shape, theorems only |
| `disprove` | `content, environment, names=None, ignore_imports=False` | `results{name -> outcome str}, disproved_theorems[], content, messages` (powered by Plausible) |
| `merge` | `documents: list[str], environment, use_def_eq=True, include_alts_as_comments=False, timeout_seconds=120` | `content, messages` (auto-renames conflicts, prefers error-free / sorry-free) |
| `normalize` | `content, environment, normalizations=["remove_sections","remove_duplicates","split_open_in_commands"], failsafe=True, ignore_imports=False, timeout_seconds=120` | `content, normalize_stats, messages` |

**Default Lean environment:** `lean-4.28.0`. Made configurable via env.

## 4. Backend Folder Structure

### NEW (everything goes here)

```
backend/formalization/
  __init__.py
  config.py                 # AxleSettings (BaseSettings) — env-driven
  axle_client.py            # singleton wrapper: lazy AxleClient, structured errors,
                            # response normalization, per-call logging
  toolbox.py                # OpenAI tool schemas for each AXLE method +
                            # dispatch(name, args) -> normalized dict result
  prompts.py                # system + user prompt templates (constants)
  context_builder.py        # ResearchAtom + ParsedPaper -> formalization context
                            # (atom text, raw TeX excerpt, linked equations,
                            # nearby prose, dependency atoms via graph)
  models.py                 # FormalizationRun, AtomFormalization,
                            # ToolCallRecord, FormalizationLabel, etc.
  events.py                 # FormalizationEvent + FormalizationEventType
  event_bus.py              # local copy of the event_bus pattern, keyed by run_id
  store.py                  # FormalizationStore (in-memory, mirrors job_store style)
  agent.py                  # FormalizationAgent — agentic loop:
                            #   OpenAI tool-calls -> AXLE dispatch -> emit events
  orchestrator.py           # FormalizationOrchestrator.run(run_id):
                            #   build context per atom, run agent, aggregate verdict
  api.py                    # FastAPI router: POST/GET/SSE endpoints
  outputs.py                # write Lean artifacts to backend/outputs/formalizations/
  scripts/
    test_axle_smoke.py      # tiny live AXLE test (requires AXLE_API_KEY)
    test_toolbox_offline.py # mock client; exercises dispatch + schemas
    test_agent_offline.py   # mock client + mock OpenAI; full loop trace
    test_formalize_e2e.py   # real-paper E2E using existing job_store fixture
```

### TOUCHED (existing files — minimal edits)

| File | Edit |
|---|---|
| `backend/main.py` | registers the formalization router at `/formalize` |
| `backend/.env.example` | appends AXLE and formalization runtime settings |
| `backend/requirements.txt` | adds `axiom-axle` and pins `httpx<0.28` for Starlette `TestClient` compatibility |
| `backend/api/review.py` | uses `LoopSafeEventSourceResponse` for stable repeated SSE tests |
| `backend/core/sse.py` | adds the loop-safe SSE response helper |

No edits to `backend/agents/`, `backend/core/orchestrators/`,
`backend/models/*`, `backend/core/event_bus.py`, or `backend/core/job_store.py`.

## 5. Frontend Folder Structure

### NEW

```
frontend/src/features/formalization/
  api.js                              # POST /formalize, GET /formalize/{id},
                                      # EventSource('/api/formalize/{id}/stream')
  types.js                            # FormalizationEventType constants,
                                      # FormalizationLabel constants
  reducer.js                          # state machine for run + per-atom state
  hooks/
    useFormalizationStream.js         # SSE subscription + cleanup
  components/
    FormalizationPanel.jsx            # top-level mount; "Run AXLE Verification" button
    AtomList.jsx                      # left rail: per-atom status badges, click to select
    LiveTrace.jsx                     # middle: scrolling event log,
                                      # filterable by atom, color-coded by tool
    AtomDetail.jsx                    # right: spec | proof | attempts | LLM transcript
    ToolCallRow.jsx                   # one row in LiveTrace: icon + tool + okay/fail + duration
    LeanCodeBlock.jsx                 # syntax-highlighted Lean (highlight.js + lean grammar
                                      # OR Prism + custom; pick smallest dep)
    StatusBadge.jsx                   # ✅/⚠️/❌/⏭️ + label text
    AxleToolBadge.jsx                 # color-coded chip per AXLE tool name
    SummaryStrip.jsx                  # counts: fully / conditionally / formalized / failed
  styles/
    formalization.css                 # only if Tailwind isn't enough
```

### TOUCHED

| File | Edit |
|---|---|
| `frontend/src/pages/Review.jsx` | one import + one tab/section that mounts `<FormalizationPanel jobId={jobId} />` |

`frontend/src/api/client.js` is **not** touched — formalization API calls live
inside the feature folder.

## 6. Data Models (`formalization/models.py`)

```python
class FormalizationStatus(str, Enum):
    QUEUED = "queued"
    BUILDING_CONTEXT = "building_context"
    LLM_THINKING = "llm_thinking"
    AXLE_RUNNING = "axle_running"
    COMPLETE = "complete"
    ERROR = "error"
    SKIPPED = "skipped"

class FormalizationLabel(str, Enum):
    FULLY_VERIFIED = "fully_verified"
    CONDITIONALLY_VERIFIED = "conditionally_verified"
    FORMALIZED_ONLY = "formalized_only"
    DISPROVED = "disproved"
    FORMALIZATION_FAILED = "formalization_failed"
    NOT_A_THEOREM = "not_a_theorem"
    GAVE_UP = "gave_up"

class ToolCallRecord(BaseModel):
    call_id: str
    tool_name: str                       # e.g. "axle_check", "axle_verify_proof"
    arguments: dict[str, Any]            # exactly what was sent
    started_at: datetime
    completed_at: datetime | None
    status: Literal["pending","success","error"]
    result_summary: dict[str, Any] | None  # truncated for SSE
    error: str | None

class FormalizationArtifact(BaseModel):
    artifact_id: str
    kind: Literal["spec","proof","helper_lemma","merged"]
    lean_code: str
    axle_check_okay: bool | None
    axle_verify_okay: bool | None
    iteration: int

class AtomFormalization(BaseModel):
    atom_id: str
    paper_id: str
    status: FormalizationStatus
    label: FormalizationLabel | None
    rationale: str | None
    artifacts: list[FormalizationArtifact]
    tool_calls: list[ToolCallRecord]
    llm_messages: list[dict]             # OpenAI message log (full transcript)
    used_assumptions: list[str]
    confidence: float
    started_at: datetime
    completed_at: datetime | None
    error: str | None

class FormalizationRun(BaseModel):
    run_id: str
    job_id: str                          # the originating review job
    paper_id: str
    selected_atom_ids: list[str]
    status: FormalizationStatus
    started_at: datetime
    completed_at: datetime | None
    atom_formalizations: dict[str, AtomFormalization]   # atom_id -> result
    summary: dict[str, int]              # counts per FormalizationLabel
    error: str | None
```

## 7. Event Types (`formalization/events.py`)

```python
class FormalizationEventType(str, Enum):
    RUN_STARTED            = "run_started"
    ATOM_QUEUED            = "atom_queued"
    ATOM_CONTEXT_BUILT     = "atom_context_built"
    LLM_THOUGHT            = "llm_thought"           # streamed assistant text
    TOOL_CALL_STARTED      = "tool_call_started"
    TOOL_CALL_COMPLETE     = "tool_call_complete"
    AXLE_CHECK_RESULT      = "axle_check_result"     # convenience flat event
    AXLE_VERIFY_RESULT     = "axle_verify_result"
    ARTIFACT_RECORDED      = "artifact_recorded"     # spec / proof committed
    ATOM_VERDICT           = "atom_verdict"
    ATOM_ERROR             = "atom_error"
    RUN_COMPLETE           = "run_complete"
    RUN_ERROR              = "run_error"

class FormalizationEvent(BaseModel):
    event_id: str
    run_id: str
    event_type: FormalizationEventType
    atom_id: str | None
    payload: dict[str, Any]
    timestamp: datetime
```

The `event_bus.py` here is a clone of `backend/core/event_bus.py` keyed by
`run_id` instead of `job_id`. Pure copy keeps the review path zero-impact.

## 8. API Surface (`formalization/api.py`)

All routes mounted at `/api/formalize/*`.

| Method | Path | Body / params | Response |
|---|---|---|---|
| POST | `/api/formalize/{job_id}` | `{atom_ids?: list[str], options?: {...}}` (default = all reviewable atoms) | `{run_id, status, selected_atom_ids}` |
| POST | `/api/formalize/{job_id}/atom/{atom_id}` | optional options | `{run_id, status}` (single-atom run) |
| GET | `/api/formalize/runs/{run_id}` | — | full `FormalizationRun` JSON |
| GET | `/api/formalize/runs/{run_id}/atom/{atom_id}` | — | single `AtomFormalization` |
| GET | `/api/formalize/runs/{run_id}/stream` | header `last-event-id` (optional) | SSE of `FormalizationEvent` |
| GET | `/api/formalize/runs/{run_id}/lean` | — | merged Lean file (`text/x-lean`) — produced via `axle.merge` |

Pre-conditions enforced:
- `job_store.get(job_id).status == "complete"` (must have atoms + parsed paper).
- If atom_ids missing, default = atoms in `REVIEWABLE_ATOM_TYPES` with
  `importance ≥ MEDIUM` (from `models/atoms.py:85-99`).

## 9. Per-Atom Flow (Agentic Loop)

```
build context for atom
  → emit ATOM_CONTEXT_BUILT
loop (capped at MAX_ITERATIONS, default 12):
    OpenAI chat.completions.create(
        model=settings.openai_model,
        messages=transcript,
        tools=AXLE_TOOLS_SCHEMA + META_TOOLS_SCHEMA,
        stream=True,                           # stream assistant text live
    )
    while streaming:
        emit LLM_THOUGHT (delta text)
    if response has tool_calls:
        for each tool_call in parallel (where safe):
            emit TOOL_CALL_STARTED
            result = await toolbox.dispatch(tool_call.name, tool_call.args)
            emit TOOL_CALL_COMPLETE (truncated summary)
            if name in {"axle_check","axle_verify_proof"}:
                emit AXLE_CHECK_RESULT / AXLE_VERIFY_RESULT (flat convenience event)
            append tool result to transcript
    elif response has emit_verdict tool call OR final structured message:
        finalize AtomFormalization, emit ATOM_VERDICT
        break
    else:
        # plain assistant message with no tool call, no verdict
        nudge via system message and continue
on AxleApiError or unrecoverable LLM error:
    emit ATOM_ERROR
    label = FORMALIZATION_FAILED / GAVE_UP
```

**Termination guaranteed by:**
- max iterations cap
- max AXLE call cap per atom (default 8)
- `give_up` meta-tool the LLM can call

**Per-run concurrency:** `asyncio.Semaphore(settings.formalization_parallelism)`,
default 2 (lower than review's 5 because AXLE compiles are heavier and the
account has rate limits the SDK already manages).

## 10. AXLE Toolbox (`formalization/toolbox.py`)

The toolbox is two things:

### a) OpenAI tool schemas

One JSON schema per AXLE method, plus four meta-tools. Tool descriptions
are curated for the LLM — they say *when* to use the tool, not just what it
is, so the model picks correctly.

Sketch of one entry:
```python
{
  "type": "function",
  "function": {
    "name": "axle_check",
    "description": (
      "Check that a Lean 4 file compiles (no errors). Use this AFTER you "
      "write or edit a spec/proof file, BEFORE attempting verify_proof. "
      "Returns okay=true if the file is valid Lean."
    ),
    "parameters": {
      "type": "object",
      "properties": {
        "content":   {"type": "string", "description": "Full Lean source."},
        "mathlib_options":  {"type": "boolean", "default": True},
        "ignore_imports":   {"type": "boolean", "default": False},
      },
      "required": ["content"]
    }
  }
}
```

The `environment` and `timeout_seconds` parameters are filled server-side
from settings — the LLM never picks them.

### b) Meta-tools (managed by the agent, not AXLE)

| Tool | Purpose |
|---|---|
| `record_artifact` | LLM commits a Lean file as `kind ∈ {spec, proof, helper_lemma}`. Fires `ARTIFACT_RECORDED`. |
| `emit_verdict` | LLM declares the final outcome: `{label, rationale, used_assumptions, confidence}`. Terminates the loop. |
| `give_up` | LLM bails with a reason. Terminates with `label=GAVE_UP`. |

### c) Dispatcher

```python
async def dispatch(self, name: str, args: dict) -> ToolCallRecord:
    if name.startswith("axle_"):
        method = getattr(self.client, name[len("axle_"):])
        result = await method(**args, environment=self.env, ...)
        summary = self._truncate_for_sse(result)
        return ToolCallRecord(..., status="success", result_summary=summary)
    elif name == "record_artifact": ...
    elif name == "emit_verdict": ...
    elif name == "give_up": ...
```

Truncation rule for SSE: keep `okay`, `failed_declarations` (names only),
counts of `errors / warnings / infos`, and the *first three error messages*
verbatim. Full result lives in the store and is fetched via the run-state
endpoint when the user clicks into a tool call.

## 11. Prompts (`formalization/prompts.py`)

**System prompt outline:**

> You are formalizing a single research claim from a math/CS paper into Lean 4
> using the AXLE verification API. You have these tools: `axle_check`,
> `axle_verify_proof`, `axle_repair_proofs`, `axle_sorry2lemma`,
> `axle_have2lemma`, `axle_extract_decls`, `axle_extract_theorems`,
> `axle_disprove`, `axle_merge`, `axle_normalize`, `record_artifact`,
> `emit_verdict`, `give_up`.
>
> Workflow:
> 1. Read the atom statement and surrounding paper context.
> 2. Decide if this is a real theorem (vs notation, sampling assumption,
>    experimental hyperparameter). If not, call `emit_verdict` with
>    `label=not_a_theorem`.
> 3. Write a minimal Lean 4 file that imports Mathlib and **states** the
>    claim with `:= by sorry`. Call `record_artifact(kind="spec", ...)` then
>    `axle_check`.
> 4. If `axle_check` fails, repair imports/types/names and re-check.
>    Don't weaken the statement to make it compile.
> 5. Once the spec compiles, write a candidate proof using the paper's
>    proof prose. Call `record_artifact(kind="proof", ...)` then
>    `axle_verify_proof(formal_statement=spec, content=proof)`.
> 6. On failure: try `axle_repair_proofs`, then `axle_sorry2lemma` to
>    decompose into helper lemmas, prove each helper, retry verify.
> 7. When done, call `emit_verdict` with one of: `fully_verified`,
>    `conditionally_verified` (if you used `permitted_sorries`),
>    `formalized_only` (spec compiles but proof unverified),
>    `disproved` (`axle_disprove` succeeded), `formalization_failed`,
>    or `gave_up`.
>
> Rules:
> - Never weaken a theorem statement just to make it compile.
> - Approximations (`\simeq`, `\approx`) must be encoded as a relation, not
>   as equality.
> - Sampling statements are assumptions, not proofs.
> - Be honest in `emit_verdict`. Don't claim `fully_verified` if you used
>   `permitted_sorries`.

**User prompt template:** built by `context_builder.py`, contains:
- Atom type, importance, atom_id
- Verbatim atom text (`atom.text`)
- Raw TeX excerpt (`assembled_tex[span.tex_start:span.tex_end]`)
- Linked equations (latex strings + labels)
- Linked citations (titles)
- Nearby prose from the section (`raw_text` ± N chars)
- Up to 3 dependency atoms from the graph (their text + verdict, if known)

## 12. UX Wireframe

The Formalize panel mounts as a tab inside the existing Review page next
to whatever sidebar exists. Tailwind + daisyui to match the existing look.

```
┌─ Review: arxiv:1312.6114 ─────────────────────────────────────────────┐
│ [Atoms] [Graph] [Report] [Formalize ●]                                │
├───────────────────────────────────────────────────────────────────────┤
│ ┌── Atoms ─────┐  ┌── Live Trace ──────────────┐  ┌── Detail ──────┐ │
│ │ ▢ all (12)   │  │ 10:42:01 t3 context built  │  │ theorem_3      │ │
│ │ ✅ thm_1     │  │ 10:42:02 t3 LLM: "I'll..." │  │ ELBO identity  │ │
│ │ ⚠️ thm_2     │  │ 10:42:03 t3 → axle_check   │  │                │ │
│ │ ❌ thm_3     │  │ 10:42:05 t3 ← ❌ 2 errors  │  │ Spec ✅        │ │
│ │ ⏭️ asm_1     │  │ 10:42:06 t3 LLM: "Need.."  │  │ Proof ⚠️       │ │
│ │ ...          │  │ 10:42:07 t3 → axle_check   │  │                │ │
│ │              │  │ 10:42:09 t3 ← ✅           │  │ [Spec] [Proof] │ │
│ │              │  │ 10:42:10 t3 → verify_proof │  │ [Attempts (3)] │ │
│ │              │  │ 10:42:14 t3 ← ❌ failed    │  │ [Transcript]   │ │
│ │              │  │ 10:42:15 t3 → sorry2lemma  │  │                │ │
│ │              │  │ ...                        │  │ <Lean code>    │ │
│ │              │  │ 10:42:30 t3 VERDICT: ⚠️   │  │                │ │
│ │              │  │                            │  │                │ │
│ │ Summary:     │  │                            │  │                │ │
│ │ ✅ 4 ⚠️ 3    │  │                            │  │                │ │
│ │ ❌ 1 ⏭️ 4    │  │ [Run AXLE Verification]    │  │ [Download .lean]│ │
│ └──────────────┘  └────────────────────────────┘  └────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

Visual notes:
- Each AXLE tool gets a distinct color chip (e.g., check=blue, verify=green,
  repair=orange, sorry2lemma=purple, disprove=red).
- LLM thoughts render in muted gray italic; tool calls in mono with arrows;
  results with ✅ / ❌ + first error if any (click to expand full).
- Auto-scroll the trace, with a "pause auto-scroll" toggle.
- Clicking a trace row scrolls the Detail panel to that artifact.
- `LeanCodeBlock` uses `react-syntax-highlighter` (lightweight, already
  popular). Lean isn't in its default grammar; we ship a tiny Lean grammar
  or fall back to `text` styling — acceptable for v1.

## 13. Merge-Conflict Isolation Strategy

A teammate hacking on the review pipeline will not collide with this work
because:

- All new backend code: `backend/formalization/**`
- All new frontend code: `frontend/src/features/formalization/**`
- Existing files touched (one-line edits, well-separated):
  - `backend/main.py` — single `include_router` line
  - `backend/.env.example` — two appended env keys
  - `frontend/src/pages/Review.jsx` — one import + one JSX tab/section

Formalization has its **own** event bus, store, and SSE channel — so no
risk of stomping on `core/event_bus.py`, `core/job_store.py`, or
`api/review.py`'s SSE endpoint.

## 14. Verification Plan (per CLAUDE.md)

Before claiming done:

```bash
# Existing suite must still pass
PYTHONPATH=backend python -c "import main; from formalization.api import router as _; print('ok')"
python -m compileall -q -x 'backend/.venv|backend/outputs' backend
python backend/scripts/test_tex_ingestion.py
python backend/scripts/test_tex_parser.py
python backend/scripts/test_review_tex_flow.py
# (the rest of the existing list)

# New formalization-specific tests
PYTHONPATH=backend python backend/formalization/scripts/test_toolbox_offline.py
PYTHONPATH=backend python backend/formalization/scripts/test_agent_offline.py

# Live tests (require AXLE_API_KEY + OPENAI_API_KEY in .env)
PYTHONPATH=backend python backend/formalization/scripts/test_axle_smoke.py
PYTHONPATH=backend python backend/formalization/scripts/test_formalize_e2e.py \
    --paper-id 1312.6114 \
    --atom-id <theorem-atom-id>
```

Manual demo check: open the frontend, submit `1312.6114`, click "Run AXLE
Verification", confirm the live trace populates and the final summary
strip shows realistic counts.

## 15. Implementation Order (checkboxes)

### Backend
- [ ] 15.1 Scaffold `backend/formalization/` package (empty modules, `__init__.py`).
- [ ] 15.2 `config.py` — `AxleSettings` (env-driven) + `formalization_parallelism`, `max_iterations_per_atom`, `max_axle_calls_per_atom`, `lean_environment`.
- [ ] 15.3 `axle_client.py` — singleton `get_client()` returning a shared `AxleClient`; structured logging; normalize error → dict.
- [ ] 15.4 `models.py` — Pydantic models from §6.
- [ ] 15.5 `events.py` + `event_bus.py` — clone of existing pattern, keyed by `run_id`.
- [ ] 15.6 `store.py` — in-memory `FormalizationStore` (create_run / get_run / update_run / per-atom updates).
- [ ] 15.7 `outputs.py` — write each artifact's Lean to `backend/outputs/formalizations/{run_id}/{atom_id}/<kind>_<iter>.lean`.
- [ ] 15.8 `toolbox.py` — tool schemas, dispatcher, response truncation. Unit-testable offline.
- [ ] 15.9 `prompts.py` — system prompt + user prompt template.
- [ ] 15.10 `context_builder.py` — read job_store; assemble context dict from `ParsedPaper` + `ResearchAtom` + graph.
- [ ] 15.11 `agent.py` — agentic loop with tool-calls, streaming, event emission.
- [ ] 15.12 `orchestrator.py` — per-run iteration over atoms, semaphore.
- [ ] 15.13 `api.py` — FastAPI router + SSE endpoint (mirror `api/review.py:109-154`).
- [ ] 15.14 Wire router into `backend/main.py`. Append env keys to `.env.example`.
- [ ] 15.15 Smoke test: `test_axle_smoke.py` (1+1=2 check) — requires `AXLE_API_KEY` to be added to `backend/.env`.
- [ ] 15.16 Offline tests: `test_toolbox_offline.py`, `test_agent_offline.py` (mock OpenAI + mock AxleClient).

### Frontend
- [ ] 15.17 Scaffold `frontend/src/features/formalization/` directory.
- [ ] 15.18 `api.js` + `types.js`.
- [ ] 15.19 `useFormalizationStream.js` + `reducer.js`.
- [ ] 15.20 Build leaf components: `StatusBadge`, `AxleToolBadge`, `LeanCodeBlock`, `ToolCallRow`.
- [ ] 15.21 Build container components: `AtomList`, `LiveTrace`, `AtomDetail`, `SummaryStrip`.
- [ ] 15.22 `FormalizationPanel.jsx` — layout + "Run AXLE Verification" button → `POST /api/formalize/{jobId}`.
- [ ] 15.23 Mount in `Review.jsx` as a new tab.
- [ ] 15.24 Add Lean syntax highlighting (or accept plain `<pre>` for v1 and revisit).

### E2E
- [ ] 15.25 Live run on VAE paper (`1312.6114`); verify trace, verdicts, downloadable Lean file.
- [ ] 15.26 Cost / latency check; tune `max_iterations_per_atom` and parallelism.
- [ ] 15.27 Update `CLAUDE.md` with the new Formalize mode (one new section near "Review API").

## 16. Open Questions (please confirm)

1. **AXLE_API_KEY** — do you have one ready to drop into `backend/.env`?
   The smoke test won't run without it. (Can be deferred to step 15.15.)
2. **Default Lean env** — `lean-4.28.0` per AXLE docs. OK to pin?
3. **Atom selection default** — start with `REVIEWABLE_ATOM_TYPES` filtered
   to importance ≥ MEDIUM (so we don't blast every minor assertion). UI can
   let the user check/uncheck individual atoms before running. OK?
4. **Trigger** — on-demand button only (not auto-after-review). Keeps the
   review pipeline pure and keeps cost predictable. OK?
5. **Lean syntax highlighting** — accept `text` highlighting for v1, ship
   real Lean grammar in v2? (Saves a dependency.)
6. **Run scope** — one `FormalizationRun` covers a whole paper; per-atom
   POST creates a single-atom run for ad-hoc retries. OK?
7. **Verdict integration with `ReviewReport`** — keep formalization verdicts
   separate (their own panel, their own download) for v1. We can splice
   them into the markdown report in a follow-up. OK?

## 17. Out of Scope (explicit non-goals)

- Modifying the existing review pipeline behavior or output schema.
- Reader / PoC / Research mode integration.
- Persisting runs across server restarts (in-memory like `job_store`).
- Multi-user auth on `/api/formalize/*` (inherits whatever the rest has).
- Automatic Lean file PR generation, GitHub integration, etc.
