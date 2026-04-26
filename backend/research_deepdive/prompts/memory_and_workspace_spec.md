# Memory And Workspace Specification

The filesystem is the durable memory layer. Hidden conversation context is not
authoritative. Every agent must write enough markdown that another agent can
resume without seeing the original chat.

## Workspace Ownership

- A subagent may write only inside its own subfolder.
- An investigator may write inside its investigator folder and read all child
  subagent folders after they finish.
- Critique agents may write only inside their critique subfolder and read final
  shared artifacts and investigator syntheses.
- The finalizer may write only inside the final folder and read all prior
  artifacts.
- Shared read-only artifacts live under `shared/`.

## Required Subagent Files

Each subagent folder should contain:

- `system_prompt.md`: exact prompt used for the agent.
- `memory.md`: running durable memory.
- `queries.md`: queries attempted, API/tool parameters, and result counts.
- `papers.md`: candidate papers with IDs, relation labels, and evidence notes.
- `findings.md`: distilled findings, each tied to evidence.
- `proposal_seeds.md`: in `novelty_ideation`, raw research ideas derived from
  evidence claims.
- `handoff.md`: final summary for the investigator.

## `memory.md` Structure

Use these headings:

- `Stable Facts`: facts repeatedly supported by sources.
- `Search Threads`: active and exhausted search strategies.
- `Candidate Papers`: papers worth revisiting.
- `Open Questions`: unresolved questions and why they remain unresolved.
- `Contradictions`: evidence conflicts.
- `Hand-Off Summary`: concise summary for the investigator.

## Finding Format

Each important finding should include:

```markdown
## Finding: <short name>

- Claim: <one sentence>
- Confidence: low|medium|high
- Evidence:
  - <paper id/title/year/url/source bucket>
  - <paper id/title/year/url/source bucket>
- Why it matters: <novelty, gap, limitation, background, follow-up, etc.>
- Caveat: <what could make this wrong>
```

## Proposal Seed Format

In `novelty_ideation`, subagents must write proposal seeds to
`proposal_seeds.md` using:

```markdown
## Proposal Seed: <title>

- Status: raw|promising|weak|probably already done
- Originating taste:
- Seed-paper hook:
- Evidence trigger:
- Candidate novelty:
- Technical mechanism:
- Closest prior-work collision:
- Closest future-work collision:
- Minimum validation:
- Falsification risk:
- Why this is not generic:
- Confidence: low|medium|high
- Required next search:
```

`findings.md` is for evidence claims. `proposal_seeds.md` is for research ideas
derived from those claims.

## Completion Boundary

Subagents stop when one of these occurs:

- configured max tool-call budget is reached;
- the investigator-specified objective is fully answered with evidence;
- a hard error blocks progress.

When a subagent stops, it must write `handoff.md`. The investigator should not
perform synthesis until every sibling subagent has reached a completion boundary.
