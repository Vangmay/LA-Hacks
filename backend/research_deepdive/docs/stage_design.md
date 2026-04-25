# Research Deep-Dive Stage Design

## Stage 1: Bootstrap

Resolve the arXiv URL, prepare the run workspace, write run metadata, and make
the shared tool/memory specs available.

The request has two separate mode axes:

- execution mode: `dry_run` or `live`;
- research objective: `literature_review` or `novelty_ideation`.

`literature_review` means the final product is deep evidence synthesis:
coverage, buckets, closest prior work, critiques, and next searches.

`novelty_ideation` means the literature review is the evidence base for actual
spinoff proposal generation. The final report must include concrete proposal
ideas, their mechanism or hypothesis, closest-prior-work risk, validation
experiment, falsification risk, and supporting papers.

## Stage 2: Investigator Planning

Create one investigator per selected section or claim cluster. Each investigator
gets a section-specific prompt and must spawn distinct subagents.

Important rule: subagents differ by research taste, not by access to tools.
The deterministic scaffold uses `personas.py` to infer a section zone, prefer
that zone's `_ZONE_TO_ARCHETYPE_HINTS`, and choose a configurable number of
complementary archetypes. Live investigator agents may regenerate the roster,
but they must preserve meaningful complementarity and the configured bounds.

## Stage 3: Subagent Research

All subagents run asynchronously subject to configured parallelism. Each subagent
uses tools and writes durable markdown memory until one completion boundary:

- max tool-call budget reached;
- objective answered;
- hard error.

For the user-requested model, the normal orchestration boundary is:

```text
spawn sibling subagents
-> async wait for every sibling to reach configured max tool-call boundary
-> reinvoke investigator synthesis
```

## Stage 4: Investigator Synthesis

The investigator reads all child subagent folders and writes `synthesis.md`.
It should reconcile taste-driven perspectives into one section-level literature
view. In `novelty_ideation`, it should also convert supported gaps into
proposal candidates; in `literature_review`, it should avoid inventing projects.

## Stage 5: Cross-Investigator Deep Dive

Compare investigator syntheses for overlap, contradictions, missing buckets,
shared candidate papers, and cross-section research gaps. In
`novelty_ideation`, also identify cross-section proposal families.

## Stage 6: Critique

Critique agents are agents with narrow review lenses. They can use tools, but
their default job is to attack the generated research artifacts rather than redo
the entire search.

Recommended static critique lenses:

- coverage and recall;
- novelty and closest prior work;
- evidence/source grounding;
- skepticism about overclaiming and contradictions.

## Stage 7: Finalization

The finalizer reads all prior artifacts and produces the final deep-dive report.
It must preserve uncertainty and critique objections. In `literature_review`,
it stops at deep evidence synthesis and recommended next searches. In
`novelty_ideation`, it must include a spinoff novelty proposal section and a
proposal triage matrix.
