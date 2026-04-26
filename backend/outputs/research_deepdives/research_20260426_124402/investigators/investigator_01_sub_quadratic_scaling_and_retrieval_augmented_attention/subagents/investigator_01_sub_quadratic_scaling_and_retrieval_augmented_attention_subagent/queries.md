# Queries



## Query: resolve_arxiv_paper 1 - https://arxiv.org/abs/1706.03762

- Tool: `resolve_arxiv_paper`
- Arguments: `{"arxiv_url": "https://arxiv.org/abs/1706.03762", "fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf"}`
- Result count: `1`
- Top result IDs: 204e3073870fae3d05bcbc2f6a8e263d9b72e776, ARXIV:1706.03762
- Why this query was run: selected by the agent as research step 1 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: resolve_arxiv_paper 1 - https://arxiv.org/abs/1706.03762

- Tool: `resolve_arxiv_paper`
- Arguments: `{"arxiv_url": "https://arxiv.org/abs/1706.03762", "fields": "paperId,externalIds,url,title,abstract,year,authors,citationCount,referenceCount,tldr"}`
- Result count: `1`
- Top result IDs: 204e3073870fae3d05bcbc2f6a8e263d9b72e776, ARXIV:1706.03762
- Why this query was run: selected by the agent as research step 1 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: get_references 2 - 204e3073870fae3d05bcbc2f6a8e263d9b72e776

- Tool: `get_references`
- Arguments: `{"fields": "citedPaper.paperId,citedPaper.title,citedPaper.year,citedPaper.abstract,citedPaper.citationCount,citedPaper.authors", "limit": 50, "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 2 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 2 - sub-quadratic scaling retrieval-augmented attention transformer

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 10, "query": "sub-quadratic scaling retrieval-augmented attention transformer"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 2 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 3 - mathematical equivalence linear attention RNN fast weights

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,abstract,authors,citationCount", "limit": 10, "query": "mathematical equivalence linear attention RNN fast weights"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 3 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 3 - sub-quadratic transformer failure on non-local long-range dependencies

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 10, "query": "sub-quadratic transformer failure on non-local long-range dependencies"}`
- Result count: `1`
- Top result IDs: a55e4328ab68f186386d74155ac31e0a3cf39089, DOI:10.1016/j.jbi.2025.104969
- Why this query was run: selected by the agent as research step 3 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_bulk_search 4 - "sub-quadratic" "retrieval" failure OR bottleneck OR limitation

- Tool: `paper_bulk_search`
- Arguments: `{"limit": 50, "query": "\"sub-quadratic\" \"retrieval\" failure OR bottleneck OR limitation", "year": "2023-"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 4 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 5 - "sub-quadratic" transformer long-context NIAH "needle in a haystack" failure

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 20, "query": "\"sub-quadratic\" transformer long-context NIAH \"needle in a haystack\" failure"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 5 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 4 - "retrieval-augmented" attention sub-quadratic scaling k-nearest neighbors

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,abstract,authors,citationCount", "limit": 10, "query": "\"retrieval-augmented\" attention sub-quadratic scaling k-nearest neighbors"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 4 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 6 - "efficient transformer" OR "linear attention" OR "state space model" failure "ne

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 20, "query": "\"efficient transformer\" OR \"linear attention\" OR \"state space model\" failure \"needle in a haystack\""}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 6 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: google_scholar_search 7 - "Mamba" vs "Transformer" "needle in a haystack" limitation OR failure

- Tool: `google_scholar_search`
- Arguments: `{"num": 10, "query": "\"Mamba\" vs \"Transformer\" \"needle in a haystack\" limitation OR failure"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 7 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 8 - Huang "How Well Can a Long Sequence Model Model Long Sequences" NIAH Mamba

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr", "limit": 1, "query": "Huang \"How Well Can a Long Sequence Model Model Long Sequences\" NIAH Mamba"}`
- Result count: `290`
- Top result IDs: fa2f8963df88d8684b38c33aa59cc3ae0927561b, ARXIV:2407.08112
- Why this query was run: selected by the agent as research step 8 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 9 - "latent state retrieval" OR "SSM state checkpointing" OR "addressable recurrence

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,abstract,year,citationCount", "limit": 10, "query": "\"latent state retrieval\" OR \"SSM state checkpointing\" OR \"addressable recurrence\" memory augmented"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 9 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.
