# Remaining Deep-Dive Orchestration Work

## Active Implementation Checklist

- [x] Stabilize the current dirty diff before adding new orchestration layers.
- [x] Finish `LiveAgentRunner` split budgets:
  research/API calls, workspace calls, and LLM steps must be counted separately.
- [x] Keep workspace-finalization alive after research/API budget exhaustion.
- [x] Reject malformed JSON action schemas without spending either budget.
- [x] Record budget counters and rejected actions in `tool_calls.jsonl`.
- [x] Add focused offline tests for split budgets, finalization, malformed
  action rejection, and Gemma high-reasoning defaults.
- [x] Build subagent context packets that include handoff/findings/papers/
  queries/memory/tool trace summaries.
- [x] Use context packets in investigator synthesis and finalizer bundles.
- [x] Replace the live cross-investigator placeholder with a thinking-model
  synthesis stage that writes the four shared artifacts.
- [x] Add optional dynamic roster planning with explicit validation and
  deterministic fallback metadata.
- [x] Update prompts, docs, and CLI flags so the runtime contract is clear.
- [x] Run offline verification commands.
- [ ] Run the monitored live Gemma novelty E2E: arXiv `1706.03762`, objective
  `novelty_ideation`, 3 investigators, 3 subagents each.
- [ ] Commit code in coherent chunks and leave generated live artifacts
  untracked.

## Active Review Notes

- Started from an already dirty worktree on 2026-04-25. Existing local edits
  included Gemma defaults, partial artifact-status feedback, partial split
  budget accounting, generated deep-dive outputs, and task/lesson edits.

## Goal

Finish the research deep-dive orchestration so live novelty-ideation runs produce
rich, durable markdown artifacts and an extensive final report. The core
principle is that research/search budgets, workspace-writing budgets, synthesis
context, and finalization context must be designed around how a real research
agent works:

- searching is budgeted because it spends external API calls and time;
- writing is not the scarce resource and should be encouraged heavily;
- agents need a dedicated post-research documentation phase;
- investigator, cross-investigator, critique, and finalizer stages need the
  evidence artifacts, not only thin summaries;
- final output for `novelty_ideation` must include concrete spinoff novelty
  proposals backed by literature evidence.

## Current Known Problems

### 1. Single Tool Budget Punishes Documentation

Current behavior in `LiveAgentRunner.run_subagent` effectively treats every tool
call as spending the same budget:

- `resolve_arxiv_paper`
- `get_references`
- `get_citations`
- `paper_bulk_search`
- `paper_relevance_search`
- `batch_get_papers`
- `rank_candidates_by_specter2_similarity`
- `google_scholar_search`
- `read_workspace_markdown`
- `write_workspace_markdown`
- `append_workspace_markdown`

This is wrong. It forces the model to trade off:

- one more search/API call;
- versus documenting queries, papers, findings, and memory.

Observed symptom in old run:

- `findings.md` mostly empty;
- `queries.md` mostly empty;
- many `papers.md` files only headers;
- `handoff.md` contains most of the useful information.

Root cause: writing spent the same scarce budget as searching.

### 2. Immediate Stop After Search Budget Exhaustion

Current behavior stops the subagent as soon as the budget boundary is reached.
If the final allowed call was a search, the model does not get a normal next
turn to digest the result and update:

- `queries.md`
- `papers.md`
- `findings.md`
- `memory.md`
- `handoff.md`

The forced handoff asks for final markdown but does not allow a proper
workspace-write phase.

### 3. System Prompt Alone Is Not Enough

The system prompt tells subagents to document properly, but live traces showed
that agents still leave markdown artifacts empty or underfilled. The model gets
the same system prompt in conversation history, but it does not reliably track
artifact state unless the runtime feeds back the current state and enforces a
workspace-finalization phase.

Artifact-status feedback has been partially implemented locally, but it is not
enough by itself. It needs to be paired with separate budgets and a finalization
phase.

### 4. Investigator Synthesis Reads Too Little Context

`_synthesize_investigator_live` currently reads only `handoff.md` from each
subagent result. That loses details intended to live in:

- `memory.md`
- `queries.md`
- `papers.md`
- `findings.md`
- `tool_calls.jsonl`

If `handoff.md` is shallow, the investigator synthesis becomes shallow even if
the subagent found useful papers.

### 5. Finalizer Receives Too Little Context

`_finalize_live` currently receives investigator synthesis artifacts and
critique artifacts. It does not directly receive:

- all subagent `handoff.md`;
- all subagent `findings.md`;
- all subagent `papers.md`;
- all subagent `queries.md`;
- selected tool trace summaries;
- `shared/cross_investigator_deep_dive.md`;
- seed metadata / paper brief artifacts.

If synthesis is thin, finalization is doomed to be thin.

### 6. Cross-Investigator Deep Dive Is A Placeholder

`_write_cross_investigator_deep_dive` currently writes a static summary. It does
not call a thinking-model agent.

Conceptually, this stage should be one of the most important synthesis stages.
It should compare all investigator syntheses and selected subagent artifacts to
identify:

- overlapping papers;
- contradictory findings;
- repeated gaps;
- weak proposals;
- cross-section spinoff opportunities;
- evidence bottlenecks;
- global novelty-risk patterns.

### 7. JSON Action Fragility Under Long Context

Gemma high-reasoning preflight passed, but long live runs exposed schema drift:

- oversized workspace append payloads got cut off mid-JSON;
- top-level `query` appeared instead of `arguments.query`;
- raw quotes inside markdown strings produced invalid JSON;
- the model sometimes ignored advisory artifact-status messages.

Mitigation should be structural:

- keep tool-result snippets focused;
- repeat strict valid/invalid action examples;
- keep all tool parameters inside `arguments`;
- allow many smaller workspace writes rather than huge payloads;
- separate writing from search budget so the model does not compress notes.

## Required Design Changes

### A. Split Tool Budgets

Implement separate counters and limits:

- `research_tool_calls_used`
- `workspace_tool_calls_used`
- `llm_steps_used`

Research/API tools count against `max_research_tool_calls`:

- `resolve_arxiv_paper`
- `get_paper_metadata`
- `get_paper_tldr`
- `get_paper_embedding`
- `get_references`
- `get_citations`
- `paper_bulk_search`
- `paper_relevance_search`
- `batch_get_papers`
- `rank_candidates_by_specter2_similarity`
- `google_scholar_search`

Workspace tools count against a separate high cap:

- `read_workspace_file`
- `read_workspace_markdown`
- `write_workspace_markdown`
- `append_workspace_markdown`
- `patch_workspace_file`

Recommended config names:

- `DEEPDIVE_SUBAGENT_MAX_RESEARCH_TOOL_CALLS`
- `DEEPDIVE_SUBAGENT_MAX_WORKSPACE_TOOL_CALLS`
- keep backward compatibility internally by mapping old
  `deepdive_subagent_max_tool_calls` to research calls only, or rename cleanly
  and update all callers/tests/docs.

Recommended defaults:

- research/API calls: configurable, around 18 to 24 for live tests;
- workspace calls: very high, e.g. 1000;
- LLM steps: high enough to allow search plus documentation, e.g. 80 to 120.

Acceptance criteria:

- workspace writes do not reduce remaining research/API calls;
- trace entries include both counters;
- `AgentRunResult` records both counters;
- tests verify workspace tools are effectively independent from research budget.

### B. Add Post-Research Workspace Finalization Phase

When `research_tool_calls_used >= max_research_tool_calls`, do not break.
Instead transition the subagent into a finalization phase:

```text
Research phase:
  allowed: research/API tools + workspace tools + final

Workspace-finalization phase:
  allowed: workspace tools + final
  forbidden: research/API tools
```

Runtime should append a user message:

```text
Research/API tool budget is exhausted.
Search/API tools are now forbidden.
You still have a large workspace-writing budget.
Update queries.md, papers.md, findings.md, memory.md, and handoff.md using
workspace tools, then return final.
```

During finalization phase, if the model tries a research/API tool, reject that
action without executing it and remind it to use workspace tools.

Acceptance criteria:

- if the last research call is a search, the model still gets turns to digest
  that result;
- `queries.md`, `papers.md`, `findings.md`, and `memory.md` can be updated
  after research budget exhaustion;
- forced handoff is only a last-resort fallback, not the normal documentation
  mechanism.

### C. Make Artifact Status Feedback Strong But Not Content-Limiting

Continue showing artifact status after each tool result:

```text
- memory.md: has content; N meaningful chars
- queries.md: empty/has content; N meaningful chars
- papers.md: empty/has content; N meaningful chars
- findings.md: empty/has content; N meaningful chars
- handoff.md: missing/has content; N meaningful chars
```

Important nuance:

- do not cap the final markdown detail;
- per-action content budgets are only JSON safety boundaries;
- agents should write many detailed chunks, not tiny summaries;
- each markdown file has a different purpose and should be substantively filled.

Suggested artifact expectations:

- `queries.md`: exact queries, parameters, filters, result counts, why query was
  run, which follow-up query it suggested.
- `papers.md`: seed paper, references, citations, recent work, critique papers,
  benchmark/reproducibility papers, same-task competitors, and relevance notes.
- `findings.md`: evidence-backed conclusions, contradictions, novelty-risk
  claims, gap candidates, proposal seeds, uncertainty.
- `memory.md`: durable running state: stable facts, search threads, open
  questions, contradictions, handoff preparation.
- `handoff.md`: concise but complete final digest, not the only useful artifact.

Acceptance criteria:

- a successful live subagent should not end with only `handoff.md` populated;
- `findings.md` should contain real findings, not just headers;
- `queries.md` should contain actual query logs;
- `papers.md` should contain actual paper records;
- tests or validation scripts check meaningful character counts after live runs.

### D. Build Subagent Context Packets For Investigator Synthesis

Add helper:

```python
def build_subagent_context_packet(path: Path) -> str:
    return f"""
    # Subagent: {path.name}

    ## Handoff
    {read("handoff.md")}

    ## Findings
    {read("findings.md")}

    ## Papers
    {read("papers.md")}

    ## Queries
    {read("queries.md")}

    ## Memory
    {read("memory.md")}

    ## Tool Trace Summary
    {summarize_tool_calls("tool_calls.jsonl")}
    """
```

The packet should be compact enough for LLM context, but it must preserve
evidence. Avoid only passing handoff.

Tool trace summary should include:

- tool counts;
- search queries;
- paper IDs from results when cheaply extractable;
- tool errors;
- whether workspace files were updated.

Acceptance criteria:

- `_synthesize_investigator_live` uses context packets, not only handoffs;
- investigator synthesis mentions papers/findings that appear in subagent
  `papers.md` / `findings.md`;
- tests verify `findings.md`, `papers.md`, and `queries.md` are included in
  synthesis input.

### E. Expand Finalizer Artifact Bundle

Finalizer should receive evidence, not only syntheses and critiques.

At minimum include:

- `shared/seed_metadata.json` if available;
- `shared/paper_brief.md` if available;
- `shared/cross_investigator_deep_dive.md`;
- `shared/proposal_families.md`;
- `shared/global_evidence_map.md`;
- `shared/unresolved_conflicts.md`;
- all investigator `synthesis.md`;
- all critique `critique.md`;
- all subagent `handoff.md`;
- all subagent `findings.md`;
- all subagent `papers.md`;
- all subagent `queries.md`;
- optionally compact tool-trace summaries.

Implementation options:

1. Make investigator synthesis extremely complete and finalizer mostly reads
   synthesis plus critique.
2. Preferably: finalizer receives both synthesis and a fuller artifact bundle,
   with truncation/summarization as needed.

Acceptance criteria:

- `_finalize_live` includes cross-investigator outputs and subagent artifact
  packets;
- final report can cite concrete papers and findings even if an investigator
  synthesis is thin;
- final novelty proposals include evidence items traceable back to subagent
  artifacts.

### F. Replace Placeholder Cross-Investigator Stage With Real Agent

Add a real thinking-model cross-investigator stage.

Inputs:

- investigator syntheses;
- selected subagent context packets;
- critique may come after this, so cross-investigator should not depend on
  critique artifacts;
- objective directive for `novelty_ideation` or `literature_review`.

Outputs under `shared/`:

- `cross_investigator_deep_dive.md`
- `proposal_families.md`
- `global_evidence_map.md`
- `unresolved_conflicts.md`

Responsibilities:

- identify repeated papers and why multiple agents found them;
- merge overlapping proposal seeds;
- separate literature-backed gaps from speculative gaps;
- detect contradictions between investigators;
- highlight missing search buckets;
- group spinoff proposals into families;
- pressure-test novelty against closest prior/future work;
- prepare a global evidence map for the finalizer.

Acceptance criteria:

- `_write_cross_investigator_deep_dive` becomes async/live LLM-backed, or a new
  `_run_cross_investigator_deep_dive_live` is added;
- dry-run can remain deterministic placeholder, but live mode must call the
  thinking model;
- finalizer receives all four shared cross-investigator artifacts;
- tests verify live prompt construction includes syntheses plus subagent
  artifacts.

### G. Implement Optional Live Dynamic Subagent Roster Planning

The intended architecture says each investigator dynamically generates a
distinct set of subagents with complementary research tastes. The current code
does not actually do that yet.

Current behavior:

- `_plan_investigators()` deterministically creates investigation zones.
- `generate_research_tastes(...)` deterministically assigns subagent archetypes.
- subagent folders and prompts are created before any investigator LLM call.
- prompts say the live investigator may replace or refine the roster, but no
  live investigator is invoked at that point to return a new roster.

This means:

- dynamic persona generation exists as a prompt concept;
- actual orchestration is deterministic persona selection;
- the large `personas.py` library and `_ZONE_TO_ARCHETYPE_HINTS` can guide
  deterministic diversity, but they are not yet being used as a live planning
  substrate.

This deterministic behavior is acceptable as a stability fallback, but it does
not match the intended architecture. The system should support real live
subagent roster generation while preserving deterministic fallback for
debugging, offline tests, and provider failure.

Required design:

```text
DirectorAgent
  reads seed metadata, paper brief, objective, requested scale, and config
  proposes investigation zones

InvestigatorPlannerAgent for each zone
  reads the zone, paper brief, objective, persona library summary,
  zone archetype hints, diversity constraints, and available tools
  returns structured JSON subagent taste specs

Orchestrator
  validates the roster
  repairs only structurally invalid issues through explicit model retry or
  deterministic fallback
  creates subagent folders and prompts from the validated live roster
```

Planner output schema should be explicit and testable:

```json
{
  "zone_id": "investigator_01_core_method",
  "zone_title": "Core method and mechanism",
  "subagents": [
    {
      "subagent_id": "investigator_01_core_method_subagent_01",
      "archetype_id": "historical_lineage_mapper",
      "display_name": "Historical Lineage Mapper",
      "research_taste": "Prior-work heavy, lineage-sensitive, citation-graph first.",
      "constructive_or_skeptical_bias": "skeptical",
      "temporal_bias": "old_prior_work",
      "primary_evidence_preferences": [
        "references",
        "closest prior work",
        "same-author prior papers",
        "non-citing similar work"
      ],
      "blind_spots_to_counteract": [
        "may underweight current frontier papers",
        "may overvalue canonical high-citation papers"
      ],
      "required_search_threads": [
        "exact method-name prior work",
        "task-level competitors before seed publication",
        "same-author prehistory"
      ],
      "required_markdown_outputs": [
        "queries.md",
        "papers.md",
        "findings.md",
        "memory.md",
        "handoff.md"
      ]
    }
  ]
}
```

Roster diversity requirements should be configurable, not hardcoded. Suggested
config fields:

- `DEEPDIVE_DYNAMIC_ROSTER_ENABLED`
- `DEEPDIVE_DYNAMIC_ROSTER_FALLBACK_TO_DETERMINISTIC`
- `DEEPDIVE_MIN_SUBAGENTS_PER_INVESTIGATOR`
- `DEEPDIVE_MAX_SUBAGENTS_PER_INVESTIGATOR`
- `DEEPDIVE_MIN_CONSTRUCTIVE_ARCHETYPES`
- `DEEPDIVE_MIN_SKEPTICAL_ARCHETYPES`
- `DEEPDIVE_MIN_PRIOR_WORK_ARCHETYPES`
- `DEEPDIVE_MIN_RECENT_FUTURE_ARCHETYPES`
- `DEEPDIVE_MAX_DUPLICATE_ARCHETYPE_FUNCTIONS`
- `DEEPDIVE_DYNAMIC_ROSTER_MODEL_PROFILE`

The user’s preferred version is not a rigid fixed 4-rule checklist. The planner
should be told to maximize complementarity and should normally include:

- at least one constructive taste;
- at least one skeptical taste;
- at least one old/prior-work taste;
- at least one recent/future-work taste;
- no duplicate archetypes that mainly perform the same function.

But the exact numbers should come from config and should scale with requested
subagent count. For example, with only 3 subagents, one archetype can satisfy
multiple constraints; with 7 subagents, the roster should cover more specialized
research tastes.

The planner must have access to a concise persona library summary, not the full
huge `personas.py` pasted blindly into every prompt. Implementation should add a
runtime helper that extracts:

- archetype id;
- title/display name;
- section/category;
- constructive/skeptical/neutral tendency;
- temporal tendency: prior, current, future, all-period;
- evidence preferences;
- failure mode/blind spot;
- best-fit investigation zones;
- function tags used for duplicate detection.

Validation should be deterministic:

- JSON schema valid;
- subagent count within config min/max;
- unique `subagent_id`;
- unique or sufficiently distinct archetype/function tags;
- required diversity constraints satisfied;
- every selected archetype exists in the persona registry unless planner
  intentionally defines a custom archetype with full fields;
- every subagent receives the full shared tool surface;
- every subagent has a distinct research taste, not a distinct tool set.

If validation fails:

- first ask the planner once to repair the roster using the validation errors;
- if still invalid and fallback is enabled, use deterministic
  `generate_research_tastes(...)`;
- record the fallback reason in run metadata and `shared/planning_trace.md`;
- do not silently pretend deterministic rosters were dynamically generated.

Prompt requirements for `InvestigatorPlannerAgent`:

- explicitly state that the goal is complementary research tastes, not random
  personalities;
- every subagent gets the same complete tool catalog;
- tool differences are not the mechanism of diversity;
- diversity comes from priors, search instincts, skepticism/constructiveness,
  temporal orientation, evidence standards, and failure modes;
- if two subagents would search the same things in the same way, the roster is
  bad;
- the planner should use `_ZONE_TO_ARCHETYPE_HINTS` as hints, not a cage;
- the planner should prefer archetypes that make sense for the section/zone;
- the planner should produce specific required search threads and markdown
  writing obligations for each subagent.

Artifacts to write:

- `shared/director_plan.md`
- `shared/investigation_zones.json`
- `investigators/<zone>/planner_roster.json`
- `investigators/<zone>/planner_rationale.md`
- `shared/planning_trace.md`

Acceptance criteria:

- with `DEEPDIVE_DYNAMIC_ROSTER_ENABLED=true`, live mode calls the planner before
  subagent folders/prompts are created;
- subagent prompts reflect planner-generated research tastes;
- all subagents keep the same tool catalog;
- validation rejects duplicate-function rosters;
- fallback is explicit and recorded, not hidden;
- offline tests cover planner validation without making live API calls;
- live E2E metadata proves whether each roster was dynamic or deterministic.

### H. Keep Gemma Thinking For All Agents

Current user preference:

- use `gemma-4-26b-a4b-it`;
- use thinking/high reasoning for all agent roles;
- do not route search subagents to a weak/light model.

Implementation detail:

- keep `thinking_profile` and `light_profile` as routing buckets;
- both should default to `gemma-4-26b-a4b-it`;
- both should default to `reasoning_effort=high`;
- both should use `GEMMA_API_KEY`;
- retain CLI/config overrides.

Acceptance criteria:

- smoke tests assert both profiles are Gemma high-reasoning;
- live result metadata confirms subagents and thinking stages use the same
  model and high reasoning setting.

### I. JSON Action Robustness

Keep strict JSON action protocol:

```json
{"action":"paper_bulk_search","arguments":{"query":"...","limit":20}}
```

Invalid:

```json
{"action":"paper_bulk_search","query":"...","limit":20}
```

Important design:

- do not silently repair malformed tool schemas if that hides provider weakness;
- it is acceptable to reject bad actions and ask the model to re-emit correctly
  without spending a tool call;
- do not execute guessed/ambiguous tool calls.

Prompt reminders should include:

- all parameters inside `arguments`;
- workspace tools need `arguments.path`;
- write/append tools need `arguments.content`;
- avoid raw unescaped double quotes inside markdown strings;
- use multiple append actions for detailed markdown.

Acceptance criteria:

- invalid schema action is rejected without spending research/API or workspace
  budget;
- trace records rejection/retry messages;
- tests cover top-level `query` rejection and workspace missing `path`
  rejection.

### J. Live E2E Validation

After implementation, run a real E2E on:

- `https://arxiv.org/abs/1706.03762`
- objective: `novelty_ideation`
- 3 investigators
- 3 subagents per investigator
- 9 personalities total
- Semantic Scholar rate limit: at least 1.2 seconds between requests
- SerpAPI cap: max 50, preferably much less
- Gemma high reasoning for all roles

Validation checks:

- all 9 subagents ran;
- every subagent has non-empty:
  - `queries.md`
  - `papers.md`
  - `findings.md`
  - `memory.md`
  - `handoff.md`
- each investigator has a substantive `synthesis.md`;
- shared cross-investigator artifacts exist and are substantive:
  - `cross_investigator_deep_dive.md`
  - `proposal_families.md`
  - `global_evidence_map.md`
  - `unresolved_conflicts.md`
- final report exists and is extensive;
- final report contains at least configured number of spinoff novelty proposals;
- each proposal has:
  - title;
  - novelty claim;
  - mechanism;
  - closest prior/future collision risks;
  - supporting evidence items;
  - validation path;
  - falsification criteria;
  - confidence/uncertainty.

### K. Offline Verification

Run:

```bash
python backend/scripts/test_research_deepdive.py
PYTHONPATH=backend python -m compileall -q -x 'backend/.venv|backend/outputs' backend
PYTHONPATH=backend python -c "import main; import api.review; import api.research; import research_deepdive; from research_deepdive import DeepDiveOrchestrator, DeepDiveConfig, DeepDiveRunRequest; print('imports ok')"
python backend/scripts/test_tex_ingestion.py
python backend/scripts/test_tex_parser.py
python backend/scripts/test_numeric.py
python backend/scripts/test_dag_builder.py
python backend/scripts/test_defender.py
python backend/scripts/test_prompt_2_agents.py
python backend/scripts/test_review_tex_flow.py
git diff --check
```

Add/update focused tests for:

- Gemma high-reasoning defaults for both profiles;
- separate research/workspace budget accounting;
- workspace tools not spending research budget;
- research budget exhaustion entering workspace-finalization mode;
- subagent context packet includes handoff/findings/papers/queries/memory;
- finalizer artifact bundle includes subagent artifacts and shared
  cross-investigator artifacts;
- live action prompt contains valid/invalid examples and artifact-status rules.

## Implementation Order

1. Finish budget split cleanly in `LiveAgentRunner`.
2. Add workspace-finalization phase after research/API budget exhaustion.
3. Fix `AgentRunResult` counters and artifacts list.
4. Add config fields and CLI flags for workspace budget and research budget.
5. Add context packet builder for subagents.
6. Update investigator synthesis to use context packets.
7. Expand finalizer artifact bundle.
8. Replace cross-investigator placeholder with a real thinking-model stage.
9. Implement optional live dynamic subagent roster planning.
10. Update prompts/docs/tests.
11. Run offline verification.
12. Run live E2E and inspect artifacts.
13. Commit code changes only; leave live output artifacts untracked.

## Current Partial Local Changes To Review Before Continuing

There are in-progress local edits from the interrupted implementation:

- Gemma defaults are set in `backend/config.py`.
- Some artifact-status feedback exists in `backend/research_deepdive/agent_runner.py`.
- A partial budget split was started but needs cleanup before tests will pass.
- `AgentRunResult` was started with separate counters.
- `tasks/lessons.md` has new correction notes.
- Several failed live run output folders exist under
  `backend/outputs/research_deepdives/`; do not commit them.

Before continuing, inspect the current diff and complete the budget split
carefully rather than layering more patches on a half-finished state.
