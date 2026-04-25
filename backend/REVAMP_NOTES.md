# PaperCourt v0.4 Revamp Notes

## What Changed

The review backend no longer uses `ClaimUnit` as its central object. It now
uses `ResearchAtom`, a source-grounded unit that can be a theorem, lemma,
definition, assumption, algorithm, bound, limitation, technique, or assertion.

Every atom carries:

- source span with paper id, section, TeX/raw offsets where available, and
  excerpt text
- attached equations from `EquationBlock`
- attached citations from `CitationEntry`
- type, importance, extraction confidence, and paper role

## Central Pipeline

```text
backend/ingestion/arxiv.py
  parse/fetch arXiv e-print source and safely assemble TeX

backend/ingestion/tex_parser.py
  TeX -> ParsedPaper with sections, equations, bibliography, raw text

backend/agents/atom_extractor.py
  deterministic TeX environment pass + batched LLM extraction over sections

backend/core/equation_linker.py
backend/core/citation_linker.py
backend/core/span_resolver.py
  source grounding helpers

backend/agents/graph_builder.py
  typed ResearchGraph edges with cycle removal on dependency edges

backend/checks/
  algebraic_sanity, numeric_probe, citation_probe -> CheckResult

backend/agents/challenge_agent.py
backend/agents/defense_agent.py
  typed Challenge and Rebuttal outputs

backend/agents/verdict_aggregator.py
backend/agents/cascade.py
backend/agents/report_agent.py
  AtomVerdict, cascade propagation, ReviewReport JSON + markdown
```

## Removed Legacy Path

Deleted/stale names should not be restored:

- `models.claim.ClaimUnit`
- `models.verification.VerificationResult`
- `agents.claim_extractor`
- `agents.dag_builder`
- `agents.tex_parser`
- `agents.symbolic_verifier`
- `agents.numeric_adversary`
- `agents.attacker`
- `agents.defender`
- `utils.arxiv`

Scripts and docs have been rewritten to use the v0.4 surface.

## API Contract

Use `POST /review/arxiv` for JSON submissions:

```json
{ "arxiv_url": "https://arxiv.org/abs/1706.03762" }
```

Progress uses atom counters:

```json
{
  "status": "processing",
  "completed_atoms": 4,
  "total_atoms": 12
}
```

The graph endpoint returns frontend-ready nodes and edges using atom ids.

## Extraction Quality Checks

The live script writes complete pipeline JSON under `backend/outputs/`:

```bash
python backend/scripts/test_pipeline.py --papers-file good_papers.txt
```

Review these fields for each paper:

- `parser.sections`, `parser.equations`, `parser.bibliography`
- `atoms[*].atom_type`
- `atoms[*].section_heading`
- `atoms[*].source_span.raw_excerpt`
- attached `equations` and `citations`
- graph `roots`, `edges`, and warnings
- report summary and high-risk atom ids

The expected behavior is not "extract every sentence." It is to capture the
paper's discrete research units with enough source grounding that review,
graphing, and reports are auditable.
