# Queries



## Query: resolve_arxiv_paper 1 - https://arxiv.org/abs/1706.03762

- Tool: `resolve_arxiv_paper`
- Arguments: `{"arxiv_url": "https://arxiv.org/abs/1706.03762", "fields": "paperId,externalIds,url,title,abstract,year,authors,venue,citationCount,referenceCount,tldr"}`
- Result count: `1`
- Top result IDs: 204e3073870fae3d05bcbc2f6a8e263d9b72e776, ARXIV:1706.03762
- Why this query was run: selected by the agent as research step 1 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: resolve_arxiv_paper 1 - https://arxiv.org/abs/1706.03762

- Tool: `resolve_arxiv_paper`
- Arguments: `{"arxiv_url": "https://arxiv.org/abs/1706.03762", "fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf"}`
- Result count: `1`
- Top result IDs: 204e3073870fae3d05bcbc2f6a8e263d9b72e776, ARXIV:1706.03762
- Why this query was run: selected by the agent as research step 1 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 2 - sub-quadratic sequence modeling state space models VRAM efficiency 2024 2025

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,citationCount,tldr,authors", "limit": 15, "query": "sub-quadratic sequence modeling state space models VRAM efficiency 2024 2025"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 2 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 2 - limitations of efficient transformers sub-quadratic complexity linear attention

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 10, "query": "limitations of efficient transformers sub-quadratic complexity linear attention"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 2 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: google_scholar_search 3 - SSM vs Transformer VRAM bottleneck long context analysis 2024

- Tool: `google_scholar_search`
- Arguments: `{"as_ylo": 2024, "num": 10, "query": "SSM vs Transformer VRAM bottleneck long context analysis 2024"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 3 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 3 - Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention Ka

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,abstract,year,authors,citationCount,referenceCount", "limit": 5, "query": "Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention Katharopoulos"}`
- Result count: `1`
- Top result IDs: 6f68e1bb253925d8431588555d3010419f322e04
- Why this query was run: selected by the agent as research step 3 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: get_citations 10 - 6f68e1bb253925d8431588555d3010419f322e04

- Tool: `get_citations`
- Arguments: `{"fields": "citingPaper.paperId,citingPaper.title,citingPaper.year,citingPaper.abstract,citingPaper.citationCount,citingPaper.tldr", "limit": 50, "paper_id": "6f68e1bb253925d8431588555d3010419f322e04"}`
- Result count: `failed (HTTPStatusError)`
- Top result IDs: 6f68e1bb253925d8431588555d3010419f322e04
- Why this query was run: selected by the agent as research step 10 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 4 - limitations of linear attention kernel approximation Gated Linear Attention Mamb

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 10, "query": "limitations of linear attention kernel approximation Gated Linear Attention Mamba"}`
- Result count: `2`
- Top result IDs: d3944893325ad2906c09870ceef1d2bdb3935229, ARXIV:2604.21100, bf1bef2ac78d20efa5c1f57ff5d503ebdb66ad95, ARXIV:2506.02475, DOI:10.48550/arXiv.2506.02475
- Why this query was run: selected by the agent as research step 4 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 5 - VRAM overhead preconditioned linear attention vs FlashAttention memory bottlenec

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,externalIds,url,title,abstract,year,publicationDate,authors,venue,publicationTypes,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,s2FieldsOfStudy,tldr,openAccessPdf", "limit": 10, "query": "VRAM overhead preconditioned linear attention vs FlashAttention memory bottleneck"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 5 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 6 - "Mamba-2" versus "FlashAttention" VRAM memory benchmark comparison

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,abstract,year,authors,citationCount,tldr", "limit": 10, "query": "\"Mamba-2\" versus \"FlashAttention\" VRAM memory benchmark comparison"}`
- Result count: `1`
- Top result IDs: d514a6cddf5b2da9d4c8f1288c8f79fc5a6ba972
- Why this query was run: selected by the agent as research step 6 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.
