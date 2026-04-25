# Lessons

## Research Deep-Dive Agent Design

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
- Novelty mode needs its own artifact and prompt spine. Treat `proposal_seeds.md`
  as the raw idea layer, force proposal collision checks, reject vague future
  work, and have investigators/critics/finalizer transform evidence into
  pressure-tested proposal candidates rather than passive gap summaries.
