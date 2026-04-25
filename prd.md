# PaperCourt — Product Requirements Document

**Version:** 0.4 (Draft)  
**Author:** Vangmay Sachan  
**Status:** Pre-development  
**Last Updated:** April 2026

---

## Active v0.4 Product Contract

The current implemented backend uses a source-grounded `ResearchAtom` design.
This is the active schema and implementation contract for Review Mode:

`arXiv e-print source -> assembled TeX -> ParsedPaper -> ResearchAtom extraction -> ResearchGraph -> checks -> challenges/rebuttals -> AtomVerdict -> ReviewReport`.

### Active schema

- `PaperSource` records arXiv/manual TeX provenance.
- `ParsedPaper` records title, sections, equations, bibliography, raw text, and
  assembled TeX.
- `ResearchAtom` replaces `ClaimUnit`; an atom can be a definition, assumption,
  theorem, lemma, proposition, construction, algorithm, bound, limitation,
  technique, related-work claim, or assertion.
- Each `ResearchAtom` carries `SourceSpan` grounding plus linked
  `EquationBlock` and `CitationEntry` objects when available.
- `ResearchGraph` replaces the old claim DAG and uses typed edges. Edge
  direction is `source_id -> target_id`, meaning source depends on target.
- `CheckResult` replaces old verification-tier output.
- `Challenge` and `Rebuttal` replace the old attacker/defender free-form
  payloads.
- `AtomVerdict` replaces `ClaimVerdict`.
- `ReviewReport` is the final JSON + markdown audit bundle.

### Active review agents/services

- `ingestion/arxiv.py`
- `ingestion/tex_parser.py`
- `agents/atom_extractor.py`
- `agents/graph_builder.py`
- `checks/algebraic_sanity.py`
- `checks/numeric_probe.py`
- `checks/citation_probe.py`
- `agents/challenge_agent.py`
- `agents/defense_agent.py`
- `agents/verdict_aggregator.py`
- `agents/cascade.py`
- `agents/report_agent.py`

### Active API

- `POST /review/arxiv`
- `POST /review`
- `GET /review/{job_id}/status`
- `GET /review/{job_id}/dag`
- `GET /review/{job_id}/atoms/{atom_id}`
- `GET /review/{job_id}/stream`
- `GET /review/{job_id}/report`
- `GET /review/{job_id}/report/markdown`

Reader, PoC, and Research Mode remain mostly stubbed and should be updated to
the atom schema when those modes are implemented.

---

## Archive: Pre-Revamp Claim-Centric PRD

The sections below are retained as product-history context only. They describe
the old claim-centric design and may mention `ClaimUnit`, `ClaimExtractorAgent`,
`DAGBuilderAgent`, `SymbolicVerifierAgent`, `NumericAdversaryAgent`,
`AttackerAgent`, or `DefenderAgent`. Those names are archived and are not the
active backend contract.

---

## 1. Overview

### 1.1 Product Summary

PaperCourt is a multi-agent system for engaging deeply with research papers across four modes. **Review Mode** deploys adversarial agent swarms to verify and attack claims in a submitted paper, producing a verdict report with confidence scores and cascade failure propagation. **Reader Mode** turns the same dependency graph into a personalized study map — generating layered explanations, prerequisite links, glossary entries, and interactive exercises for each claim. **PoC Mode** operationalizes the paper's empirically testable claims into a runnable proof-of-concept: generating success/failure metrics, an implementation scaffold, and a reproducibility report mapping your experiment results back to the original claims. **Research Mode** wraps all three into a fully autonomous research loop: given a question or topic, the system retrieves relevant literature, builds a cross-paper knowledge graph, detects open problems, generates and attempts to prove conjectures, and self-reviews its output using the adversarial core.

All four modes are intended to share the same foundational infrastructure. The implemented review path now uses arXiv source ingestion, deterministic TeX parsing, source-grounded research atom extraction, and a typed dependency graph rendered live in the browser via SSE.

### 1.2 Problem Statement

Engaging with research papers is hard at every level. For **researchers**, peer review is slow and errors in foundational claims propagate undetected for years. For **students and non-specialists**, dense notation and assumed prerequisites create a wall that flat summaries don't solve. For **practitioners** who want to implement a paper's ideas, there is no structured path from "I read this paper" to "I have a working implementation with the right success criteria." For **research explorers**, surveying a field, finding open problems, and generating novel directions requires hours of manual synthesis across dozens of papers.

No existing tool spans all four: adversarial claim verification, dependency-aware guided reading, reproducibility scaffolding, and autonomous hypothesis generation.

### 1.3 Solution

PaperCourt addresses all four use cases on a shared backend:

- **Shared core:** arXiv source ingestion → TeX parsing → research atom extraction → typed dependency graph → live graph visualization via SSE
- **Review Mode:** check services + challenge/defense agents → per-atom verdicts with cascade propagation
- **Reader Mode:** explanation generation at multiple levels + prerequisite mapping + glossary + interactive exercises + Socratic tutor per claim
- **PoC Mode:** empirically testable claim filtering → success/failure metric extraction → implementation scaffold generation → experiment result ingestion → reproducibility report
- **Research Mode:** literature retrieval → cross-paper knowledge graph → gap detection → hypothesis generation → proof attempts → self-review via the adversarial core → structured research note output

### 1.4 Target Users

| Mode | Primary Users |
|---|---|
| **Review Mode** | Researchers submitting preprints, journal editors, AI safety/technical audit teams, graduate students stress-testing proofs |
| **Reader Mode** | Students reading papers above their level, ML engineers parsing theory papers, non-specialists exploring adjacent fields |
| **PoC Mode** | ML engineers implementing papers, research engineers validating ideas from literature, hackathon teams building on published methods, anyone who wants to go from "I read this" to "I built this" |
| **Research Mode** | Graduate researchers surveying a field, teams identifying open problems, advanced users wanting autonomous literature synthesis |

---

## 2. Goals & Non-Goals

### 2.1 Goals

**Shared core (all modes)**
- Ingest arXiv source bundles and extract atomic claim units from TeX
- Build a proof-theoretic dependency DAG with topological traversal
- Stream live DAG state updates to a browser UI via SSE

**Review Mode**
- Run multi-tier verification (symbolic, numeric, semantic) per claim
- Deploy adversarial attacker/defender agent pairs per claim in parallel
- Emit per-claim verdicts (`SUPPORTED | CONTESTED | REFUTED`) with confidence scores and cascade propagation
- Generate a structured JSON + markdown audit report

**Reader Mode**
- Generate per-claim explanations at layperson, undergraduate, and graduate levels
- Identify external prerequisite concepts per claim with curated resource links
- Generate a glossary of non-standard terms per claim
- Produce 2–3 interactive exercises per claim with graded responses
- Support freeform "convince me" Socratic Q&A scoped to individual nodes
- Track and visualize user comprehension progress through the DAG

**PoC Mode**
- Filter the claim DAG to surface only empirically testable claims (performance bounds, accuracy numbers, algorithmic complexity, convergence results, benchmark comparisons)
- Extract precise quantitative success and failure criteria from each testable claim
- Generate a runnable Python implementation scaffold based on the paper's described method
- Generate a test harness with pre-written assertions matching the paper's reported results
- Accept experiment results from the user and map them back to individual claim nodes
- Produce a reproducibility report: which claims reproduced, which diverged, delta analysis, and possible explanations for gaps

**Research Mode**
- Accept a research question or topic as input (no PDF required)
- Retrieve and rank relevant papers via Semantic Scholar / arXiv APIs
- Build a cross-paper knowledge graph of claims and their relationships
- Detect gaps, open problems, and contested results in the knowledge graph
- Generate falsifiable, scoped hypotheses from detected gaps
- Attempt symbolic and numeric proof or disproof of generated hypotheses
- Maintain working memory of tried hypotheses, dead ends, and retrieved papers across iterations
- Self-review generated research notes using the full adversarial core
- Output a structured research note with supporting evidence

### 2.2 Non-Goals (v1)

- Full formal proof verification (Lean 4 export is a stretch goal only)
- Real-time collaborative multi-user sessions (all modes are single-session)
- Support for non-arXiv input sources
- Integration with journal submission systems
- Fully autonomous Research Mode loop with no human checkpoint (v1 requires human approval after hypothesis generation)
- PoC Mode: automatic execution of generated scaffold code (user runs the code; system only ingests results)

---

## 3. Functional Requirements

### 3.1 Ingestion & Parsing

| ID | Requirement |
|---|---|
| F-01 | System shall accept an arXiv URL or bare article id as input |
| F-02 | TexParserAgent shall extract raw text, LaTeX equations, section structure, and bibliography from assembled TeX |
| F-03 | ClaimExtractorAgent shall segment parsed content into atomic claim units: theorems, lemmas, corollaries, propositions, and key intermediate assertions |
| F-04 | Each claim unit shall carry: claim text, claim type, section location, and attached equation strings |

### 3.2 Dependency DAG

| ID | Requirement |
|---|---|
| F-05 | DAGBuilderAgent shall infer logical dependency edges between claim units |
| F-06 | The DAG shall be a strict directed acyclic graph; cycles shall raise a validation error |
| F-07 | Claims with no upstream dependencies shall be marked as root nodes and processed first |
| F-08 | The DAG shall support topological traversal for ordered claim processing |

### 3.3 Verification Tiers

| ID | Requirement |
|---|---|
| F-09 | SymbolicVerifierAgent shall use SymPy to check algebraic consistency of equations attached to each claim |
| F-10 | NumericAdversaryAgent shall use SciPy optimization to search for counterexamples to universally quantified claims |
| F-11 | RAGRetrievalAgent shall embed each claim and retrieve top-k contradicting or supporting passages from a reference corpus |
| F-12 | Each tier shall emit a structured result: `{tier, status, evidence, confidence}` |

### 3.4 Adversarial Agent Swarm

| ID | Requirement |
|---|---|
| F-13 | AttackerAgent shall generate targeted challenges against each claim using LLM reasoning, seeded by verification tier outputs |
| F-14 | AttackerAgent shall spawn CounterexampleSearchAgent for universally quantified claims |
| F-15 | AttackerAgent shall spawn CitationGapAgent to verify that cited sources support the claims they are attached to |
| F-16 | DefenderAgent shall generate rebuttals to each attacker challenge |
| F-17 | Attacker and Defender agents shall run in parallel per claim via `asyncio.gather` |

### 3.5 Verdict Aggregation & Cascade

| ID | Requirement |
|---|---|
| F-18 | VerdictAggregatorAgent shall weigh attacker challenges, defender rebuttals, and tier scores to emit a per-claim verdict |
| F-19 | Verdicts shall be one of: `SUPPORTED`, `CONTESTED`, or `REFUTED`, with a confidence score in [0, 1] |
| F-20 | CascadeAgent shall propagate `REFUTED` verdicts to all downstream dependent claims in topological order |
| F-21 | Cascaded refutations shall be distinguished from direct refutations in the output |

### 3.6 Report Generation

| ID | Requirement |
|---|---|
| F-22 | ReportAgent shall emit a structured JSON object containing all claim verdicts, confidence scores, challenges, rebuttals, and tier evidence |
| F-23 | ReportAgent shall emit a markdown summary report highlighting refuted claims, cascade failures, and contested nodes |
| F-24 | The report shall include a DAG summary showing the propagation path of each failure |

### 3.7 Live DAG Visualization

| ID | Requirement |
|---|---|
| F-25 | The backend shall emit `DAGEvent` objects over a Server-Sent Events (SSE) stream at `GET /review/{job_id}/stream` as each agent completes work |
| F-26 | Events shall be emitted at every state transition: claim node created, verification tier completed, attacker challenge issued, defender rebuttal issued, verdict emitted, cascade propagated |
| F-27 | The frontend shall render the DAG as a directed graph with a hierarchical layout, nodes = claims, edges = dependencies |
| F-28 | Each node shall display: claim ID, claim type badge, current processing status, and final verdict with confidence score |
| F-29 | Node color shall reflect live state: **grey** = pending, **blue** = processing, **green** = SUPPORTED, **yellow** = CONTESTED, **red** = REFUTED, **dark red** = REFUTED via cascade |
| F-30 | Active nodes shall display an animated pulse ring while agents are running against them |
| F-31 | Edges involved in a cascade failure shall be highlighted in red with a directional animation showing failure propagation |
| F-32 | Clicking a node shall open a side panel showing: claim text, tier results, all attacker challenges, all defender rebuttals, and the final verdict rationale |
| F-33 | A live activity feed alongside the DAG shall log agent events in real time (e.g. "AttackerAgent raised counterexample on Lemma 3") |
| F-34 | A summary bar at the top shall show live running counts: total claims, pending, processing, supported, contested, refuted |
| F-35 | The DAG view shall be the primary interface — arXiv submission and live review visualization on a single page |

### 3.8 Lean 4 Export (Stretch)

| ID | Requirement |
|---|---|
| F-36 | Lean4ExporterAgent shall accept contested or refuted claims and export them as Lean 4 proof obligations |
| F-37 | The exporter shall attempt autoformalization and return either a proof term or a countermodel |

---

### 3.9 Reader Mode

| ID | Requirement |
|---|---|
| F-38 | System shall accept a user-selected comprehension level at session start: `layperson`, `undergraduate`, `graduate`, `expert` |
| F-39 | ExplainerAgent shall generate a per-claim explanation at the user's chosen level; user may override level per node |
| F-40 | ExplainerAgent explanations shall include: intuitive summary, formal restatement at level, worked example where applicable |
| F-41 | PrerequisiteMapperAgent shall identify concepts external to the paper required to understand each claim (e.g. measure theory, Fourier analysis) |
| F-42 | PrerequisiteMapperAgent shall surface each external prerequisite with at least one curated resource link (Wikipedia, YouTube, textbook section via OpenAlex) |
| F-43 | A concept glossary shall be auto-generated for every non-standard term within each claim, displayed inline in the node detail panel |
| F-44 | ExerciseGeneratorAgent shall produce 2–3 practice problems per claim: at least one conceptual, one computational, one "which of these is a counterexample" format |
| F-45 | Exercises shall be gradable: the system evaluates free-text answers and returns pass/fail with explanation |
| F-46 | Each node detail panel shall include a "Convince me" text input; SocraticTutorAgent shall respond to freeform objections or questions scoped to that claim only |
| F-47 | Users shall be able to mark nodes as `understood`, `in progress`, or `flagged`; the DAG shall visually reflect comprehension state |
| F-48 | The system shall identify root nodes with fewest external prerequisites and highlight them as "start here" entry points |
| F-49 | Upon session completion, Reader Mode shall export a structured study guide: claim map with user annotations, all explanations at the user's level, exercises with answers, and an ordered prerequisite reading list |

### 3.10 Research Mode

| ID | Requirement |
|---|---|
| F-50 | System shall accept a research question, topic, or conjecture as freeform text input; paper input is optional |
| F-51 | LiteratureSearchAgent shall query Semantic Scholar and arXiv APIs to retrieve and rank the top-k relevant papers |
| F-52 | KnowledgeGraphAgent shall extract claims from all retrieved papers and merge them into a single cross-paper knowledge graph, with source paper tracked per node |
| F-53 | KnowledgeGraphAgent shall detect cross-paper contradictions (same claim, conflicting verdicts across papers) and flag them as contested nodes |
| F-54 | GapDetectorAgent shall identify open problems, underexplored directions, and unresolved contradictions in the knowledge graph |
| F-55 | HypothesisGeneratorAgent shall propose candidate conjectures scoped to detected gaps; each hypothesis shall be falsifiable and bounded enough for the verification tier to evaluate |
| F-56 | The system shall present generated hypotheses to the user for approval before proceeding; user may accept, reject, or edit each hypothesis |
| F-57 | ProofStrategyAgent shall select a proof approach for accepted hypotheses (induction, construction, contradiction) and scaffold a structured attempt |
| F-58 | ProofStrategyAgent shall invoke SymbolicVerifierAgent and NumericAdversaryAgent from the existing verification tier to test each hypothesis |
| F-59 | ResearchMemoryAgent shall maintain a persistent working memory per session: tried hypotheses, failure reasons, retrieved papers, dead ends |
| F-60 | The research loop shall run a maximum of 5 hypothesis-proof cycles before surfacing results to the user, regardless of outcome |
| F-61 | Accepted hypotheses (confidence > 0.80 from verification) shall be passed to DraftWriterAgent for research note generation |
| F-62 | DraftWriterAgent shall produce a structured research note: background, hypothesis statement, proof sketch, supporting evidence, limitations |
| F-63 | SelfReviewAgent shall invoke the full PaperCourt adversarial review loop against the generated research note before output |
| F-64 | Final output shall include the research note, its self-review verdict, the full knowledge graph snapshot, and the list of source papers |

### 3.11 PoC Mode

| ID | Requirement |
|---|---|
| F-65 | ClaimFilterAgent shall analyze all ClaimUnits in the DAG and classify each as `testable` or `theoretical`; only testable claims proceed through PoC Mode |
| F-66 | A claim is classified as testable if it contains at least one of: a quantitative performance bound, an accuracy or error rate, an algorithmic complexity assertion, a convergence result, or a benchmark comparison against a named baseline |
| F-67 | MetricExtractorAgent shall extract from each testable claim: a precise success criterion (the condition that counts as reproduction), a failure criterion (the condition that counts as non-reproduction), the specific numeric threshold from the paper, and the required experimental conditions (dataset, hyperparameters, hardware assumptions if stated) |
| F-68 | ScaffoldGeneratorAgent shall generate a runnable Python project for each testable claim: an implementation file based on the paper's described method/pseudocode, a test harness file with pre-written assertions using the extracted success criteria, and a results logger that captures metrics in structured JSON |
| F-69 | The generated scaffold shall include inline comments referencing the specific paper section and claim ID each code block corresponds to |
| F-70 | The scaffold shall be downloadable as a `.zip` file containing all generated files with a `README.md` explaining how to run it |
| F-71 | The user shall be able to upload a results JSON file (output of the results logger) back to the system after running the scaffold |
| F-72 | ResultsAnalyzerAgent shall ingest the uploaded results JSON and map each metric to its corresponding claim node in the DAG |
| F-73 | ResultsAnalyzerAgent shall assign a reproduction status to each claim: `REPRODUCED` (result within tolerance of paper's reported value), `PARTIAL` (result in the right direction but outside tolerance), or `FAILED` (result diverges or experiment errored) |
| F-74 | ResultsAnalyzerAgent shall generate a gap analysis for each non-reproduced claim: list of possible explanations (dataset mismatch, missing hyperparameter, implementation gap, hardware difference) ranked by likelihood |
| F-75 | The DAG in PoC Mode shall color nodes by reproduction status: **green** = REPRODUCED, **amber** = PARTIAL, **red** = FAILED, **grey** = theoretical (not testable), **blue** = pending (scaffold generated but not yet run) |
| F-76 | ReproducibilityReportAgent shall generate a structured report: overall reproduction rate, per-claim status table, delta analysis (paper value vs. your value), gap analysis, and a "what to try next" section for failed claims |
| F-77 | Clicking a testable claim node shall open a side panel showing: the extracted success criterion, the generated scaffold code (syntax-highlighted), the experiment results if uploaded, and the gap analysis if applicable |

---

## 4. Agent Specifications

### 4.1 Agent Hierarchy

#### Shared Core (all modes)
```
TexParserAgent
ClaimExtractorAgent
DAGBuilderAgent
```

#### Review Mode
```
ReviewOrchestrator
└── [per claim, parallel]
    ├── SymbolicVerifierAgent
    ├── NumericAdversaryAgent
    ├── RAGRetrievalAgent
    ├── AttackerAgent
    │   ├── CounterexampleSearchAgent
    │   └── CitationGapAgent
    ├── DefenderAgent
    └── VerdictAggregatorAgent
        └── [after all claims]
            ├── CascadeAgent
            └── ReportAgent
```

#### Reader Mode
```
ReaderOrchestrator
└── [per claim, on user click]
    ├── ExplainerAgent          (level-appropriate explanation)
    ├── PrerequisiteMapperAgent (external concept + resource links)
    ├── GlossaryAgent           (inline term definitions)
    ├── ExerciseGeneratorAgent  (2–3 practice problems + grader)
    └── SocraticTutorAgent      (on-demand, freeform Q&A per node)
```

#### PoC Mode
```
PoCOrchestrator
├── ClaimFilterAgent            (testable vs theoretical classification)
├── MetricExtractorAgent        (success/failure criteria per testable claim)
├── ScaffoldGeneratorAgent      (implementation + test harness code generation)
├── ResultsAnalyzerAgent        (maps uploaded experiment results to claim nodes)
└── ReproducibilityReportAgent  (reproduction rate, delta analysis, gap analysis)
```

#### Research Mode
```
ResearchDirectorAgent           (outer loop controller, max 5 iterations)
├── LiteratureSearchAgent       (Semantic Scholar + arXiv retrieval)
├── KnowledgeGraphAgent         (cross-paper claim graph builder)
├── GapDetectorAgent            (open problems + contradictions)
├── HypothesisGeneratorAgent    (conjecture proposals)
├── ResearchMemoryAgent         (session-scoped working memory)
├── ProofStrategyAgent
│   ├── SymbolicVerifierAgent   (re-used from Review Mode)
│   └── NumericAdversaryAgent   (re-used from Review Mode)
├── DraftWriterAgent            (research note generation)
└── SelfReviewAgent
    └── [full Review Mode inner loop against draft]
```

### 4.2 Agent Interface Contract

Every agent shall implement the following base interface:

```python
class BaseAgent:
    agent_id: str
    claim_id: Optional[str]

    async def run(self, context: AgentContext) -> AgentResult:
        ...
```

`AgentResult` shall carry: `agent_id`, `claim_id`, `status`, `output`, `confidence`, `error`.

### 4.3 Agent Execution Rules

**Shared core:** TexParserAgent → ClaimExtractorAgent → DAGBuilderAgent (always sequential)

**Review Mode:** Verification tier agents + Attacker + Defender run in parallel per claim via `asyncio.gather`; CascadeAgent → ReportAgent run sequentially after all claims are resolved

**Reader Mode:** ExplainerAgent, PrerequisiteMapperAgent, GlossaryAgent, ExerciseGeneratorAgent run in parallel on node click; SocraticTutorAgent runs on-demand per user query

**PoC Mode:** ClaimFilterAgent → MetricExtractorAgent run sequentially on pipeline output; ScaffoldGeneratorAgent runs in parallel across all testable claims; ResultsAnalyzerAgent and ReproducibilityReportAgent run sequentially after user uploads results

**Research Mode:** Outer loop is sequential (Search → Graph → Gap → Hypothesis → [human checkpoint] → Proof → Draft → SelfReview); inner loop (ProofStrategy's verification calls, SelfReview's adversarial loop) follows Review Mode parallelism rules; ResearchMemoryAgent is always live and updated after each step

---

## 5. Data Models

### 5.1 ClaimUnit

```python
class ClaimUnit(BaseModel):
    claim_id: str
    text: str
    claim_type: Literal["theorem", "lemma", "corollary", "proposition", "assertion"]
    section: str
    equations: List[str]
    citations: List[str]
    dependencies: List[str]   # claim_ids this claim depends on
```

### 5.2 VerificationResult

```python
class VerificationResult(BaseModel):
    tier: Literal["symbolic", "numeric", "semantic"]
    status: Literal["passed", "failed", "inconclusive"]
    evidence: str
    confidence: float
```

### 5.3 Challenge / Rebuttal

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

### 5.4 ClaimVerdict

```python
class ClaimVerdict(BaseModel):
    claim_id: str
    verdict: Literal["SUPPORTED", "CONTESTED", "REFUTED"]
    confidence: float
    is_cascaded: bool
    cascade_source: Optional[str]   # claim_id that triggered cascade
    challenges: List[Challenge]
    rebuttals: List[Rebuttal]
    verification_results: List[VerificationResult]
```

### 5.5 ClaimAnnotation (Reader Mode)

```python
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
    user_answer: Optional[str]
    graded: Optional[bool]

class ClaimAnnotation(BaseModel):
    claim_id: str
    level: ComprehensionLevel
    explanation: str
    glossary: Dict[str, str]          # term → definition
    prerequisites: List[Prerequisite]
    exercises: List[Exercise]
    comprehension_status: ComprehensionStatus
```

### 5.6 ResearchSession (Research Mode)

```python
class Hypothesis(BaseModel):
    hypothesis_id: str
    text: str
    source_gap: str
    proof_approach: Optional[Literal["induction", "construction", "contradiction", "numeric"]]
    verification_result: Optional[VerificationResult]
    status: Literal["proposed", "approved", "rejected", "proven", "disproven", "inconclusive"]
    user_approved: bool

class KnowledgeNode(BaseModel):
    node_id: str
    claim_text: str
    source_paper: str           # arXiv ID or DOI
    related_nodes: List[str]    # node_ids with supporting relationship
    contradicting_nodes: List[str]

class ResearchSession(BaseModel):
    session_id: str
    query: str
    retrieved_papers: List[str]
    knowledge_graph: List[KnowledgeNode]
    detected_gaps: List[str]
    hypotheses: List[Hypothesis]
    iteration_count: int
    working_memory: Dict[str, Any]  # dead ends, tried approaches
    research_note: Optional[str]    # markdown output
    self_review_verdict: Optional[ReviewReport]
```

### 5.7 PoC Mode Models

```python
class ClaimTestability(str, Enum):
    TESTABLE    = "testable"
    THEORETICAL = "theoretical"

class ReproductionStatus(str, Enum):
    REPRODUCED = "REPRODUCED"
    PARTIAL    = "PARTIAL"
    FAILED     = "FAILED"
    PENDING    = "PENDING"    # scaffold generated, not yet run

class MetricCriterion(BaseModel):
    metric_name: str
    paper_reported_value: str       # as stated in paper, e.g. "94.3% accuracy"
    numeric_threshold: Optional[float]
    tolerance: float                # e.g. 0.02 for ±2%
    comparison: Literal["gte", "lte", "eq", "within_tolerance"]
    experimental_conditions: Dict[str, str]  # dataset, hyperparams, etc.

class PoCSpec(BaseModel):
    spec_id: str
    claim_id: str
    testability: ClaimTestability
    success_criteria: List[MetricCriterion]
    failure_criteria: List[MetricCriterion]
    scaffold_files: Dict[str, str]  # filename → file content
    readme: str

class ExperimentResult(BaseModel):
    claim_id: str
    metric_name: str
    achieved_value: float
    status: ReproductionStatus
    delta: Optional[float]          # achieved - threshold
    error_message: Optional[str]    # if experiment errored

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
    reproduction_rate: float        # reproduced / total_testable
    results: List[ExperimentResult]
    gap_analyses: List[GapAnalysisEntry]
    what_to_try_next: List[str]
    markdown_report: str
```

### 5.8 DAGEvent

```python
class DAGEventType(str, Enum):
    NODE_CREATED      = "node_created"
    TIER_COMPLETE     = "tier_complete"
    CHALLENGE_ISSUED  = "challenge_issued"
    REBUTTAL_ISSUED   = "rebuttal_issued"
    VERDICT_EMITTED   = "verdict_emitted"
    CASCADE_TRIGGERED = "cascade_triggered"
    REVIEW_COMPLETE   = "review_complete"

class DAGEvent(BaseModel):
    event_id: str
    job_id: str
    event_type: DAGEventType
    claim_id: Optional[str]
    payload: Dict[str, Any]   # event-specific data
    timestamp: datetime
```

SSE stream format:
```
event: dag_update
data: {"event_type": "verdict_emitted", "claim_id": "lemma_3", "payload": {"verdict": "REFUTED", "confidence": 0.87}}
```

### 5.9 ReviewReport

```python
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
    dag_summary: Dict[str, List[str]]
    markdown_report: str
```

---

## 6. API Specification

### 6.1 Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/review` | Submit an arXiv URL/id for Review Mode; returns `job_id` |
| `GET` | `/review/{job_id}/status` | Poll job status |
| `GET` | `/review/{job_id}/stream` | **SSE stream** — emits `DAGEvent` objects in real time |
| `GET` | `/review/{job_id}/report` | Retrieve completed `ReviewReport` JSON |
| `GET` | `/review/{job_id}/report/markdown` | Retrieve markdown summary |
| `GET` | `/review/{job_id}/dag` | Retrieve full DAG snapshot (nodes + edges + current verdicts) |
| `POST` | `/read` | Submit an arXiv URL/id for Reader Mode with comprehension level; returns `session_id` |
| `GET` | `/read/{session_id}/claim/{claim_id}` | Fetch full `ClaimAnnotation` for a node (triggers agent generation if not cached) |
| `POST` | `/read/{session_id}/claim/{claim_id}/tutor` | Submit a "convince me" query; returns SocraticTutorAgent response |
| `POST` | `/read/{session_id}/claim/{claim_id}/grade` | Submit exercise answer; returns graded result |
| `PATCH` | `/read/{session_id}/claim/{claim_id}/status` | Update comprehension status for a node |
| `GET` | `/read/{session_id}/study-guide` | Export complete study guide for the session |
| `POST` | `/research` | Start a Research Mode session with a query; returns `session_id` |
| `GET` | `/research/{session_id}/stream` | **SSE stream** — emits research loop events in real time |
| `GET` | `/research/{session_id}/hypotheses` | Retrieve generated hypotheses pending user approval |
| `POST` | `/research/{session_id}/hypotheses/{hypothesis_id}/approve` | Approve a hypothesis to proceed to proof attempt |
| `POST` | `/research/{session_id}/hypotheses/{hypothesis_id}/reject` | Reject a hypothesis; loop continues to next gap |
| `GET` | `/research/{session_id}/note` | Retrieve the final research note and self-review report |
| `GET` | `/research/{session_id}/knowledge-graph` | Retrieve the full cross-paper knowledge graph snapshot |
| `POST` | `/poc` | Submit an arXiv URL/id for PoC Mode; returns `session_id` |
| `GET` | `/poc/{session_id}/claims` | List all claims with testability classification |
| `GET` | `/poc/{session_id}/claim/{claim_id}/spec` | Retrieve full `PoCSpec` for a testable claim |
| `GET` | `/poc/{session_id}/scaffold.zip` | Download generated scaffold as a zip file |
| `POST` | `/poc/{session_id}/results` | Upload experiment results JSON; triggers ResultsAnalyzerAgent |
| `GET` | `/poc/{session_id}/report` | Retrieve completed `ReproducibilityReport` JSON |
| `GET` | `/poc/{session_id}/report/markdown` | Retrieve markdown reproducibility report |
| `GET` | `/poc/{session_id}/dag` | DAG snapshot with reproduction status overlay per node |

### 6.2 `POST /review` Request

```json
{
  "arxiv_url": "https://arxiv.org/abs/1706.03762",
  "options": {
    "enable_lean4_export": false,
    "rag_corpus": "arxiv_math",
    "max_parallel_claims": 10
  }
}
```

### 6.3 `POST /review` Response

```json
{
  "job_id": "uuid-v4",
  "status": "queued",
  "estimated_duration_seconds": 120
}
```

---

## 7. Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11+ |
| API framework | FastAPI |
| Data validation | Pydantic v2 |
| Async orchestration | asyncio, asyncio.gather |
| SSE streaming | FastAPI `EventSourceResponse` (sse-starlette) |
| Symbolic verification | SymPy |
| Numeric adversary | SciPy (optimize, minimize) |
| TeX ingestion | arXiv e-print source download + safe TeX assembly |
| LLM calls | OpenAI API (GPT-4o) |
| Embeddings | sentence-transformers |
| Vector store | ChromaDB (local) or Pinecone (remote) |
| **PoC scaffold generation** | **GPT-4o with code-generation system prompt** |
| **Results ingestion** | **JSON file upload + Pydantic validation** |
| **Scaffold packaging** | **Python `zipfile` stdlib** |
| **Syntax highlighting (frontend)** | **react-syntax-highlighter** |
| Literature retrieval | Semantic Scholar API, arXiv API |
| **Knowledge graph store** | **NetworkX (in-memory); Neo4j (persistent, stretch)** |
| **Exercise grading** | **GPT-4o with rubric-based system prompt** |
| **Resource link resolution** | **OpenAlex API** |
| Frontend framework | React + Vite |
| DAG rendering | React Flow |
| SSE client | EventSource API (native browser) |
| Styling | Tailwind CSS |
| Lean 4 export *(stretch)* | Lean 4 + Mathlib |
| Server | uvicorn |

---

## 8. Live DAG UI Specification

### 8.1 Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [PaperCourt]          [arXiv URL]     Summary: 12✓ 3? 2✗ 3⟳   │
├───────────────────────────────────────┬─────────────────────────┤
│                                       │                         │
│           DAG Canvas                  │    Activity Feed        │
│     (React Flow, fills viewport)      │  ─────────────────────  │
│                                       │  ⟳ Processing Thm 4    │
│   [Lemma 1]──►[Theorem 2]──►[Cor 5]  │  ✗ Lemma 3 REFUTED     │
│       │                               │  ⚔ Attacker: boundary  │
│       ▼                               │    violation found      │
│   [Lemma 3]──►[Theorem 4]            │  🛡 Defender: rebuttal  │
│   (pulsing)    (pending)              │    issued               │
│                                       │  ✓ Lemma 1 SUPPORTED   │
├───────────────────────────────────────┴─────────────────────────┤
│  [Minimap]    Layout: Hierarchical ▾    Zoom: [─────●───]       │
└─────────────────────────────────────────────────────────────────┘
```

When a node is clicked, the DAG canvas shifts left and a side panel opens:

```
┌────────────────────────────────┬────────────────────────────────┐
│        DAG Canvas              │       Node Detail Panel        │
│        (60% width)             │       (40% width)              │
│                                │  Lemma 3 · REFUTED · 0.87     │
│                                │  ─────────────────────────     │
│                                │  Claim text...                 │
│                                │                                │
│                                │  Tier Results                  │
│                                │  Symbolic: FAILED              │
│                                │  Numeric:  FAILED              │
│                                │  Semantic: inconclusive        │
│                                │                                │
│                                │  Challenges (2)                │
│                                │  ├ Counterexample at x=0       │
│                                │  └ Citation [14] mismatch      │
│                                │                                │
│                                │  Rebuttals (1)                 │
│                                │  └ Scope restricted to x>0     │
│                                │                                │
│                                │  Verdict rationale...          │
└────────────────────────────────┴────────────────────────────────┘
```

### 8.2 Node Visual States

| State | Color | Animation |
|---|---|---|
| Pending | Grey `#6B7280` | None |
| Processing | Blue `#3B82F6` | Pulsing ring |
| SUPPORTED | Green `#22C55E` | None |
| CONTESTED | Yellow `#EAB308` | None |
| REFUTED (direct) | Red `#EF4444` | None |
| REFUTED (cascade) | Dark red `#7F1D1D` | Cascade sweep animation along incoming edge |

### 8.3 SSE Event → UI State Machine

```
DAGEventType          UI Action
─────────────────     ──────────────────────────────────────────────
node_created        → Add grey node to canvas; add to summary count
tier_complete       → Update node tooltip with tier badge
challenge_issued    → Append to activity feed; flash node border
rebuttal_issued     → Append to activity feed
verdict_emitted     → Recolor node; update summary bar counts
cascade_triggered   → Recolor node dark red; animate edge red sweep
review_complete     → Show "Review complete" banner; enable report download
```

### 8.4 Activity Feed Format

Each feed entry is a single line with an icon, agent name, and short description:

```
⟳  ReviewOrchestrator   Starting review — 14 claims found
⚙  SymbolicVerifier     Lemma 1 · symbolic check passed
⚔  AttackerAgent        Theorem 2 · counterexample search launched
🛡  DefenderAgent        Theorem 2 · rebuttal: domain restriction applies
✗  VerdictAggregator    Lemma 3 · REFUTED (confidence 0.87)
⚡  CascadeAgent         Theorem 4, Corollary 5 · cascaded from Lemma 3
✓  VerdictAggregator    Theorem 2 · SUPPORTED (confidence 0.91)
```

---

## 9. Non-Functional Requirements

| Requirement | Target |
|---|---|
| PoC Mode: scaffold generation latency (per claim) | < 20s |
| PoC Mode: results analysis after upload | < 10s |
| Review Mode: claim processing latency (p50) | < 30s per claim |
| Review Mode: full paper (20 claims) end-to-end | < 10 minutes |
| Reader Mode: per-node annotation generation latency | < 15s on click |
| Research Mode: literature retrieval (top-20 papers) | < 30s |
| Research Mode: full loop (5 iterations) | < 20 minutes |
| API uptime | 99% during demo/evaluation windows |
| Concurrent jobs | At least 3 simultaneous sessions across all modes |
| Structured output contract | 100% Pydantic-validated; no raw dict outputs |

---

## 10. Milestones

| Milestone | Deliverable | Target |
|---|---|---|
| M0 | PRD + agent taxonomy finalized | Week 1 |
| M1 | FastAPI skeleton + all agent stubs + Pydantic models + SSE event bus | Week 1 |
| M2 | Parser + ClaimExtractor + DAGBuilder working end-to-end | Week 2 |
| M3 | SymPy + SciPy verification tiers live | Week 2 |
| M4 | Attacker + Defender agent loop with LLM calls (Review Mode core) | Week 3 |
| M5 | RAG retrieval + VerdictAggregator + CascadeAgent + ReportAgent | Week 3 |
| M6 | React frontend: DAG render + SSE consumer + node side panel (Review Mode UI) | Week 4 |
| M7 | Reader Mode: ExplainerAgent + PrerequisiteMapper + GlossaryAgent + ExerciseGenerator | Week 5 |
| M8 | Reader Mode: SocraticTutorAgent + comprehension tracking + study guide export | Week 5 |
| M9 | Reader Mode UI: comprehension state overlay on DAG + node detail panel extended | Week 6 |
| M10 | Research Mode: LiteratureSearch + KnowledgeGraph + GapDetector + HypothesisGenerator | Week 7 |
| M11 | Research Mode: ProofStrategy + ResearchMemory + DraftWriter + SelfReview loop | Week 8 |
| M12 | Research Mode UI: research loop SSE feed + hypothesis approval panel + knowledge graph view | Week 8 |
| M13 | PoC Mode: ClaimFilter + MetricExtractor + ScaffoldGenerator + API routes | Week 10 |
| M14 | PoC Mode: ResultsAnalyzer + ReproducibilityReport + UI | Week 10 |
| M15 | End-to-end test across all four modes on real arXiv papers | Week 11 |
| M16 | Lean 4 exporter *(stretch)* | Post-MVP |

---

## 11. Open Questions

1. **Claim extraction accuracy:** How do we handle informal assertions that are not labeled as theorems/lemmas but are still load-bearing? Heuristic detection vs. LLM extraction?
2. **RAG corpus scope:** Start with arXiv abstracts only, or include full-text? Full-text dramatically increases index size.
3. **Equation parsing:** How much TeX macro expansion is needed before symbolic verification becomes reliable across arXiv source styles?
4. **Attacker budget:** How many challenges should AttackerAgent generate per claim before we cap it? Uncapped challenges blow up cost.
5. **Verdict weighting:** How do we weight tier scores vs. LLM agent debate outcomes in VerdictAggregatorAgent? Needs an explicit scoring rubric.
6. **Lean 4 scope:** Autoformalization of arbitrary math is unsolved. Should Lean 4 export be scoped to algebraic identities only for v1?
7. **DAG layout algorithm:** Hierarchical layout is semantically correct but can become very wide for large papers — do we need zoom/pan and minimap from day one?
8. **SSE reconnection:** If a client drops mid-review, does the stream replay all prior events from a buffer, or does the client fetch a `/dag` snapshot and re-subscribe from current state?
9. **Reader Mode: exercise quality bar:** How do we ensure exercises are actually pedagogically useful and not trivial? Do we need a human review pass on generated exercises for v1?
10. **Reader Mode: prerequisite link quality:** OpenAlex covers textbooks sparsely — do we fall back to Google Scholar links or curated static resource lists for common prerequisites?
11. **Research Mode: knowledge graph persistence:** Does the cross-paper graph persist across sessions (growing database) or is it rebuilt fresh each session? Persistent is more powerful but adds infra complexity for v1.
12. **Research Mode: domain scope:** Review and Reader Mode work on arXiv papers. Research Mode's literature retrieval is currently Semantic Scholar + arXiv — does this scope the product to academic research only, or do we want a broader corpus path?
13. **Research Mode: hypothesis quality gate:** What makes a generated hypothesis "good enough" to show the user? We need a pre-filter before the human checkpoint to avoid surfacing trivially false or already-proven conjectures.
14. **PoC Mode: testability classification accuracy:** GPT-4o may misclassify purely theoretical claims as testable (e.g. existence proofs that state a bound without specifying how to compute it). Do we need a human confirmation step before scaffold generation?
15. **PoC Mode: scaffold quality for novel architectures:** Generated scaffolds will be better for standard ML tasks (classification accuracy, loss curves) than for novel architectures or domain-specific metrics. Should we scope PoC Mode to ML/systems papers only for v1?
16. **PoC Mode: tolerance defaults:** What default tolerance should we use when the paper doesn't specify one? ±2% for accuracy metrics seems reasonable but needs validation across paper types.

---

## 12. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM hallucinations in claim extraction | High | High | Validate extracted claims against source text; human-readable diff |
| SymPy fails on non-algebraic claims | High | Medium | Tier 1 emits `inconclusive` gracefully; does not block pipeline |
| Cost blowup from parallel LLM calls | Medium | High | Per-claim attacker challenge cap; token budget guardrails |
| DAG cycle detection edge cases | Low | High | Strict cycle check at build time; fail fast with clear error |
| arXiv source ingestion failures | Medium | Medium | Surface clear source errors and keep failed jobs inspectable |
| SSE stream dropped mid-review | Medium | Medium | Backend buffers all `DAGEvent`s per job; client can re-subscribe and replay from last `event_id` |
| React Flow performance on large DAGs (50+ nodes) | Low | Medium | Enable virtualization; add minimap + zoom controls; cap visible detail at small zoom levels |
| Reader Mode exercises are trivial or wrong | Medium | Medium | GPT-4o with strict rubric prompt; sample eval set to validate quality before shipping |
| Research Mode loop diverges or cycles on unproductive hypotheses | Medium | High | Hard cap of 5 iterations; ResearchMemory explicitly blocks re-trying rejected hypotheses |
| Semantic Scholar / arXiv API rate limits disrupt Research Mode | Medium | Medium | Cache all retrieved papers per session; exponential backoff; graceful degradation to fewer papers |
| Research Mode produces unfalsifiable hypotheses that pass the human checkpoint | Low | High | Pre-filter: HypothesisGeneratorAgent must include a proposed falsification strategy; show it to user at checkpoint |
| PoC scaffold generates unrunnable code | High | Medium | Always include a `validate_scaffold.py` script that does a dry-run import check; flag syntax errors before packaging |
| MetricExtractor misreads paper's reported numbers | Medium | High | Show extracted values to user before scaffold generation with a "confirm these values" step |
| User uploads malformed results JSON | Medium | Low | Strict Pydantic validation on upload; return clear field-level error messages |

---

*PaperCourt: adversarial review, guided reading, reproducibility scaffolding, and autonomous research — on one shared graph.*
