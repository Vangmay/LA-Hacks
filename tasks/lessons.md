# Lessons

- Formalization dashboard state cannot rely on event-only metadata. Anything
  needed by Overview or Context after refresh, late SSE connection, or dashboard
  reopen must be persisted in the run snapshot, especially atom text/type,
  importance, queue position, section, and context summary counts.
- Do not demonstrate the AXLE formalization loop with tiny caps and present the
  result as representative. The point of the feature is iterative repair:
  AXLE feedback must be fed back to the agent repeatedly until the spec
  compiles, the proof verifies, or a very high operational guard is exhausted.
- Do not allow `formalized_only` unless AXLE has actually returned `okay=true`
  for a faithful spec. Recorded Lean text alone is not enough.
- AXLE compiles syntactic Lean. It cannot tell whether a proof is *faithful*
  to the paper claim. The model can satisfy `axle_check` + `axle_verify_proof`
  with vacuous encodings: `theorem T : ∃ x : Type, True := ⟨Unit, trivial⟩`,
  `def isFoo := False; theorem ¬ isFoo := by simp`, or
  `def x = expr; theorem x = expr := by rfl`. The system prompt now bans these
  patterns explicitly; without that, "fully_verified" silently means nothing.
- For multi-atom runs, OpenAI's per-organization TPM (30k for gpt-4o on the
  default tier) is the bottleneck, not Lean. With `parallelism=3`, two atoms
  out of fourteen got killed by 429s on the VAE paper. Drop to `parallelism=2`
  and bump the agent's rate-limit retry cap to ≥16 with jittered delays.
- When running long Python jobs in the background, redirect to a file with
  `python -u` (or `PYTHONUNBUFFERED=1`) so stdout flushes per-line; otherwise
  the file lags behind real progress and `tail -F` makes more sense than
  `grep` on the file.
- Never launch a long backend script via Bash with `&` inside
  `run_in_background: true`. The shell exits immediately and the worker dies.
  Use `run_in_background: true` with a plain redirect, no `&`.

## Research Deep-Dive Agent Design

- LLM-generated atom headers need a deterministic final grammar gate after all
  model cleanup passes. Prompt rules and critic decisions are not enough:
  headers ending in dangling conjunctions like `because`, unfinished clauses, or
  TeX-derived symbol fragments such as `bphi`/`qPhi` must be repaired from the
  grounded source excerpt or dropped before they reach the UI.
- Atom display statements and graph labels are different surfaces. Never solve
  graph compactness by truncating the stored atom statement; keep a complete
  clean-English statement, use compact labels only in constrained graph/list UI,
  and expose long statements through an expandable inspector.

- Dynamic subagents should differ by research taste, not by tool access. Give
  them the same complete tool surface, then force diversity through complementary
  archetypes, evidence preferences, and failure modes.
- Persona selection must not be a shallow fixed list. Use zone-aware hints and
  configurable diversity constraints so each investigator can pick complementary
  constructive, skeptical, prior-work, and recent/future-work lenses when useful.
- Tool prompts are part of the product surface. Agent-visible tool specs need
  exact purpose, inputs, outputs, endpoint behavior, examples, and fallback
  guidance, not just tool names.
- Deep-dive orchestration must separate reasoning roles from search/helper
  roles in config. Thinking models should own Director, Investigator, Critique,
  Revision, and Finalization; lightweight models should own tool-heavy search,
  extraction, dedupe, formatting, and metadata classification.
- Live pipeline tests should expose provider/tool/schema problems directly.
  Do not hide those issues behind silent fallback models, skipped stages, or
  best-effort placeholder artifacts.
- Live JSON action protocols should minimize nested control fields. Prefer
  `action=<tool_name>` over `action=tool` plus a separate `tool_name`; weaker
  providers otherwise confuse the schema under pressure.
- Endpoint-specific Semantic Scholar constraints belong in the executable tool
  runtime, not in agent discretion. For example, bulk search owns its safe
  fields and sort normalization because `/paper/search/bulk` rejects `tldr` and
  only supports selected sort fields.
- Model-role routing must be swappable at runtime. If the lightweight model
  repeatedly emits malformed action JSON, route search subagents through the
  thinking profile and pace requests rather than accepting low-quality traces.
- Final research reports must distinguish passive `research_gaps` from active
  `spinoff novelty proposals`. If the user wants novelty generation, prompts
  need an explicit section requiring concrete new project ideas, novelty
  mechanism, supporting evidence, falsification risks, and next experiments.
- Final reports and critique artifacts need explicit configurable depth
  contracts. Section names alone invite short summaries; prompts must require
  extensive synthesis, proposal-level fields, evidence counts, critique
  integration, and clear evidence bottlenecks when depth is not possible.
- Before launching expensive live model-orchestration runs, make a tiny
  provider preflight with the exact configured model, base URL, API-key env var,
  and reasoning-effort setting. This catches SDK-signature problems and provider
  quota blocks before a long multi-agent run begins.
- For this project, search/tool subagents are not necessarily "light" in model
  quality. If the user asks for thinking-only execution, keep the routing bucket
  but point every profile at the thinking-capable model and verify the generated
  action JSON under live tool pressure.
- A one-time system prompt telling agents to document is not enough. The live
  loop must feed back artifact status after tool results so the next action can
  see whether `queries.md`, `papers.md`, or `findings.md` is still empty and
  repair the documentation gap.
- Long tool-result contexts make weaker JSON-action adherence worse. Keep tool
  result snippets focused, repeat that every parameter belongs inside
  `arguments`, and show both valid and invalid action examples in the live loop.
- Research/API tool budgets and workspace-writing budgets must be separate.
  Writing detailed markdown is core agent work, not a scarce external API
  action. Exhausting search budget should transition the agent into a
  workspace-only finalization phase, not immediately force a handoff.
- Higher-level synthesis agents need evidence bundles, not only summaries.
  Investigator synthesis, cross-investigator synthesis, critique, and finalizer
  stages should receive subagent findings/papers/queries/memory/handoffs and
  selected trace summaries so thin handoffs cannot collapse the final report.
- Prompting an investigator to "dynamically generate" subagents is not the same
  as implementing dynamic roster planning. If subagent prompts and folders are
  created before any planner LLM call, the system is deterministic even if the
  prompt describes a dynamic architecture. Live planning must happen before
  subagent creation, with schema validation and explicit deterministic fallback.
- Do not use crude character-count thresholds as the primary quality signal for
  deep-dive artifacts. Runtime enforcement should encode artifact-specific
  content obligations: queries need query/parameters/result-count/rationale;
  papers need IDs/titles/years/source/relevance; findings need evidence,
  uncertainty, and proposal implications; memory needs durable running state.
  Minimal length checks are only a backstop against empty placeholders.
- Documentation repair must be evidence-stage-aware. Do not require
  `papers.md`, `findings.md`, or proposal artifacts before searches have
  produced the evidence needed to populate them; otherwise the runtime pressures
  agents into fake or placeholder prose. Obligations should unlock from the
  trace: search result -> query entry, paper-producing result -> paper records,
  enough candidate papers -> findings, findings in novelty mode -> proposal
  seeds, final -> repair every due artifact or mark the handoff incomplete.
- For Gemma-backed deep-dive runs, do not make LLM turns or workspace markdown
  writes the scarce resource. Keep tight budgets on external research APIs, but
  use generous step counts, workspace tool budgets, and per-write character
  budgets so agents can document, repair, and finalize thoroughly.
- MVP live defaults should enable the important orchestration features, not
  require the operator to remember extra flags. Dynamic roster planning should
  be on by default, with explicit opt-out flags, and Gemma-oriented time,
  interval, output-token, step, and workspace budgets should default high while
  external search APIs remain deliberately budgeted.
- A CLI option named `subagents_per_investigator` must be an exact execution
  contract for live E2E runs. Dynamic roster planning can choose the personas,
  but it should not silently expand the requested 3x3 topology into a larger
  run unless there is a separate explicit expansion flag.
- Live demo E2E runs must isolate failures at the smallest useful boundary.
  Malformed model JSON should become a rejected action and repair prompt; an
  unrecoverable subagent/tool failure should write an explicit error handoff and
  let sibling subagents, investigators, critique, and finalization continue.
- Individual live tool execution failures should usually be recoverable inside
  the action loop. Log the failed call in `tool_calls.jsonl` and
  `raw_tool_results.jsonl`, add a structured failed-query entry when it was a
  research/API tool, then prompt the agent to retry with corrected arguments or
  use a fallback tool instead of crashing the subagent.
- Provider-level JSON parsing should not impose one schema on every caller.
  Dynamic roster planning may legitimately return a top-level JSON array, while
  subagent action loops require a JSON object and should reject non-object JSON
  locally as a recoverable action-protocol error.
- Dynamic roster parsing should accept common wrapper variants from Gemma, such
  as a top-level list containing one object with a nested `tastes` or
  `subagents` array. Validate the resulting roster count/diversity after
  unwrapping rather than falling back before the semantic parser sees it.
- Novelty mode needs its own artifact and prompt spine. Treat `proposal_seeds.md`
  as the raw idea layer, force proposal collision checks, reject vague future
  work, and have investigators/critics/finalizer transform evidence into
  pressure-tested proposal candidates rather than passive gap summaries.
- A finalizer prompt contract is not enough for novelty-mode MVP quality.
  Validate the generated final report structurally before accepting it: require
  the configured number of detailed `Spinoff Proposal:` sections, required
  per-proposal subsections, high-confidence/speculative split, and a triage
  matrix. If the first report is thin, run a repair finalization pass against
  the same evidence bundle instead of treating `status=success` as sufficient.
