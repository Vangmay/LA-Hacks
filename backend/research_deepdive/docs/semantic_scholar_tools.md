# Semantic Scholar Tool Notes

These notes are implementation guidance for concrete tools that will conform to
`backend/research_deepdive/tools.py`.

Official docs:

- API overview: https://www.semanticscholar.org/product/api
- Tutorial: https://www.semanticscholar.org/product/api/tutorial
- API reference: https://api.semanticscholar.org/api-docs/

## Mental Model

Semantic Scholar is the primary structured literature graph. Use it for paper
metadata, references, citations, authors, search, snippets, datasets, and
SPECTER2 embeddings.

The docs split the API into:

- Academic Graph: papers, authors, citations, references, venues, embeddings.
- Recommendations: similar papers, optional and allowed to return empty.
- Datasets: downloadable snapshots for local large-scale graph work.

## Core Endpoints

Use these first:

- `GET /graph/v1/paper/{paper_id}`
- `POST /graph/v1/paper/batch`
- `GET /graph/v1/paper/{paper_id}/references`
- `GET /graph/v1/paper/{paper_id}/citations`
- `GET /graph/v1/paper/search/bulk`
- `GET /graph/v1/paper/search`
- `GET /graph/v1/snippet/search`
- `GET /graph/v1/author/search`
- `GET /graph/v1/author/{author_id}`
- `GET /graph/v1/author/{author_id}/papers`
- `POST /graph/v1/author/batch`
- `GET /graph/v1/paper/autocomplete`
- `GET /datasets/v1/release`
- `GET /datasets/v1/release/{release_id}`
- `GET /datasets/v1/release/{release_id}/dataset/{dataset_name}`

Optional:

- `GET /recommendations/v1/papers/forpaper/{paper_id}`
- `POST /recommendations/v1/papers`

If Recommendations returns `{"recommendedPapers": []}`, treat it as a successful
empty result and fall back to citations, references, and search.

## Fields To Request

Common paper fields:

```text
paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,
publicationTypes,citationCount,influentialCitationCount,referenceCount,
fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf
```

Embedding fields:

```text
embedding.specter_v2
```

Nested citation fields:

```text
citingPaper.paperId,citingPaper.title,citingPaper.abstract,citingPaper.year,
citingPaper.authors,citingPaper.citationCount,citingPaper.influentialCitationCount,
citingPaper.url,citingPaper.venue,citingPaper.tldr,citingPaper.openAccessPdf
```

Nested reference fields:

```text
citedPaper.paperId,citedPaper.title,citedPaper.abstract,citedPaper.year,
citedPaper.authors,citedPaper.citationCount,citedPaper.influentialCitationCount,
citedPaper.url,citedPaper.venue,citedPaper.tldr,citedPaper.openAccessPdf
```

## Search Strategy

Use `paper/search/bulk` for most candidate generation. It supports query syntax,
filters, sorting, and token pagination. Use `paper/search` when a small,
high-precision result set is more useful than recall.

Useful query families:

- exact title;
- method name;
- task/problem;
- dataset/benchmark;
- key technical claim;
- survey/review/tutorial/taxonomy;
- limitations/failure modes/robustness;
- reproducibility/replication/ablation;
- synonyms/acronyms/older terminology.

Useful bulk-search filters:

- `year`
- `publicationDateOrYear`
- `venue`
- `fieldsOfStudy`
- `publicationTypes`
- `openAccessPdf`
- `minCitationCount`
- `sort=publicationDate:desc`
- `sort=citationCount:desc`

## SPECTER2 Pipeline

1. Resolve the seed paper to canonical `paperId`.
2. Fetch the seed with `embedding.specter_v2`.
3. Generate candidates from references, citations, bulk search, snippets, and
   author papers.
4. Batch-fetch candidates with `embedding.specter_v2`.
5. Compute cosine similarity.
6. Rerank inside buckets. Do not collapse all buckets into one global list.

Good buckets for embedding rerank:

- closest prior work before seed year;
- non-citing similar work;
- recent related work;
- noisy bulk-search candidates;
- cluster labels for a literature map.

Do not use SPECTER2 to verify formulas, theorem correctness, or exact empirical
claims. It is paper-level similarity, not proof checking.

## Agent-Visible Tool Surface

`backend/research_deepdive/tools.py` exposes the full planned surface as typed
contracts. The raw API tools are intentionally small:

- paper resolver/details/TLDR/embedding;
- references and citations;
- bulk and relevance search;
- snippets;
- authors and author papers;
- batch paper/author lookup;
- autocomplete;
- datasets.

Most high-level tools are wrappers over those primitives:

- high-impact/recent references;
- influential/recent citations;
- generated query search;
- method/task/dataset/survey/critique/reproducibility searches;
- same-author prior/follow-up work;
- SPECTER2 reranking, non-citing-neighbor search, novelty-neighbor search, and
  clustering;
- literature context packs, role classification, gap extraction, novelty tables,
  graph relationship scoring, field/venue distributions, and time-window search.

The prompts do not require agents to remember this document. The orchestrator
injects each concrete tool's name, endpoint or implementation source, input
schema, output schema, example input, example output, fallback tools, and notes
directly into every investigator, subagent, critic, and finalizer system prompt.

## Rate Limits And Keys

Use the `x-api-key` header when configured. Keep limits configurable. Prefer
batch and bulk endpoints for large candidate sets.
