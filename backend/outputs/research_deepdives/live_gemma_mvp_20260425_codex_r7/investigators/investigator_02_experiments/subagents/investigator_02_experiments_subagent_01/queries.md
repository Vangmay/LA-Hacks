# Queries



## Query: resolve_arxiv_paper 1 - https://arxiv.org/abs/1706.03762

- Tool: `resolve_arxiv_paper`
- Arguments: `{"arxiv_url": "https://arxiv.org/abs/1706.03762"}`
- Result count: `1`
- Top result IDs: 204e3073870fae3d05bcbc2f6a8e263d9b72e776, ARXIV:1706.03762
- Why this query was run: selected by the agent as research step 1 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: get_references 2 - 204e3073870fae3d05bcbc2f6a8e263d9b72e776

- Tool: `get_references`
- Arguments: `{"fields": "citedPaper.paperId,citedPaper.title,citedPaper.year,citedPaper.citationCount,citedPaper.url", "limit": 50, "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 2 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: get_citations 3 - 204e3073870fae3d05bcbc2f6a8e263d9b72e776

- Tool: `get_citations`
- Arguments: `{"fields": "citingPaper.paperId,citingPaper.title,citingPaper.year,citingPaper.citationCount,citingPaper.abstract", "limit": 50, "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 3 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_bulk_search 4 - "Attention is All you Need"

- Tool: `paper_bulk_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,authors,abstract", "limit": 50, "query": "\"Attention is All you Need\"", "sort": "citationCount:desc", "year": "2017-2019"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 4 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 5 - linear attention transformer kernel approximation

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract,url", "limit": 15, "query": "linear attention transformer kernel approximation"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 5 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 6 - state space model mamba transformer efficiency comparison

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "state space model mamba transformer efficiency comparison"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 6 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 7 - hybrid transformer mamba architecture

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "hybrid transformer mamba architecture"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 7 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 8 - dynamic routing between transformer and state space models mamba

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "dynamic routing between transformer and state space models mamba"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 8 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 9 - token-level routing adaptive computation hybrid Transformer Mamba

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "token-level routing adaptive computation hybrid Transformer Mamba"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 9 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 10 - adaptive token routing between transformer and state space models

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "adaptive token routing between transformer and state space models"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 10 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 11 - continuous soft routing hybrid transformer mamba architectures

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "continuous soft routing hybrid transformer mamba architectures"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 11 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.


## Query: paper_relevance_search 12 - "soft routing" OR "continuous blending" OR "differentiable architecture" Transfo

- Tool: `paper_relevance_search`
- Arguments: `{"fields": "paperId,title,year,citationCount,abstract", "limit": 15, "query": "\"soft routing\" OR \"continuous blending\" OR \"differentiable architecture\" Transformer Mamba"}`
- Result count: `0`
- Top result IDs: (none extracted)
- Why this query was run: selected by the agent as research step 12 for its assigned taste and open questions.
- Follow-up: promote relevant papers into `papers.md`, distill evidence into `findings.md`, and update `memory.md` with state, open questions, or contradictions.
