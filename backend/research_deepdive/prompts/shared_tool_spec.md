# Shared Tool Specification

Every investigator, subagent, critique agent, and finalizer sees the same core
tool surface unless the orchestrator explicitly narrows it. Different agents
should differ by research taste, hypotheses, evidence priorities, and search
strategy, not by artificial tool poverty.

This document gives operating rules. The concrete tool registry injected below
this document gives the exact tool names, endpoints or implementation source,
input schemas, output schemas, examples, fallback tools, and special notes. Use
the concrete registry as the authoritative calling contract.

## Tool-Use Principles

1. Prefer structured literature APIs before general web search.
2. Use Semantic Scholar paper IDs after resolving an arXiv URL.
3. Treat Semantic Scholar Recommendations as optional. Empty recommendations are
   a valid non-error result and must trigger citation/reference/search fallback.
4. Use citations for future work and descendants.
5. Use references for past work and intellectual ancestry.
6. Use bulk search for high-recall candidate generation.
7. Use relevance search for small, precision-oriented checks.
8. Use snippets for direct mentions of limitations, failure modes, claims, and
   benchmark/reproducibility evidence.
9. Use SerpApi / Google Scholar as corroboration or discovery when Semantic
   Scholar coverage is thin.
10. Write durable knowledge to markdown files. Do not rely on hidden chat memory.

## Required Literature Buckets

When researching a section or claim, fill as many buckets as evidence supports:

- `seed_metadata`: title, abstract, authors, year, venue, fields, TLDR, IDs.
- `foundational_references`: older high-impact papers the seed cites.
- `closest_prior_work`: technically closest papers before or at seed year.
- `near_publication_competitors`: contemporaneous work around seed year.
- `direct_followups`: papers that cite and extend the seed.
- `recent_followups`: current papers from the last few years.
- `same_task_competitors`: papers solving the same problem differently.
- `same_author_prior`: author lineage before the seed.
- `same_author_followup`: what the authors did after the seed.
- `surveys`: surveys, tutorials, reviews, taxonomies.
- `benchmarks_reproductions`: benchmarks, replications, ablations, stress tests.
- `critiques_limitations`: limitations, robustness failures, negative results.
- `non_citing_similar`: semantically or lexically related papers that do not cite
  the seed.
- `research_gaps`: supported gaps, each tied to concrete evidence.
- `spinoff_novelty_proposals`: only for `novelty_ideation`; concrete project
  ideas derived from supported gaps, contradictions, failures, missing
  mechanisms, or modern follow-up pressure.

## Objective-Specific Output Rule

`literature_review` is exhaustive evidence synthesis. Do not invent project
ideas in that mode; identify what is known, unknown, weakly supported, or still
needs searching.

`novelty_ideation` is evidence-grounded proposal generation. In that mode,
novelty generation is the final product and the literature review is the
justification layer. Every proposal must trace back to papers, gaps, negative
evidence, or unresolved contradictions.

## Search Query Families

Generate several query families instead of one query:

- exact title query;
- method-name query;
- task/problem query;
- dataset/benchmark query;
- key-claim query;
- survey/review/taxonomy query;
- critique/limitation/failure-mode query;
- reproducibility/replication/ablation query;
- synonym/acronym/older-name query;
- future-work/open-problem query.

## Evidence Quality Rules

- Label every candidate paper by why it matters: `reference`, `citation`,
  `bulk_search`, `relevance_search`, `snippet`, `same_author`, `serpapi`,
  `embedding_rerank`, or `manual_followup`.
- Preserve paper IDs, URLs, years, citation counts, and query strings.
- Distinguish "paper is popular" from "paper is technically close."
- Distinguish "paper cites seed" from "paper extends seed."
- Distinguish lexical overlap from shared mechanism.
- If evidence is weak, write that plainly instead of filling the gap with prose.

## SPECTER2 Usage

SPECTER2 embeddings are paper-level representations. Use them as rerankers after
candidate generation, not as the only retrieval method.

Good uses:

- nearest prior work before seed publication;
- non-citing related work;
- clustering candidate papers into themes;
- reranking noisy bulk-search results.

Bad uses:

- proving math correctness;
- verifying exact experimental claims;
- replacing source reading;
- deciding novelty without dates and relation labels.

Request `embedding.specter_v2` only when needed because it increases payloads.

## Concrete Tool Registry

The orchestrator injects the complete registry after this heading. If a tool's
API call fails or returns empty results, follow that tool's listed fallback
tools and preserve the failed parameters in memory.
