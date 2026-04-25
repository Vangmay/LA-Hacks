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
