# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Resolving seed paper arXiv:1706.03762 to establish canonical ID.


## Step 2: append_workspace_markdown

Repaired papers.md by adding the seed paper record.


## Step 3: get_references

Fetching references to map the technical ancestry and identify the recurrent/convolutional paradigms the Transformer aims to replace.


## Step 4: append_workspace_markdown

Recording ResNet as a key architectural ancestor for residual connections.


## Step 5: append_workspace_markdown

Recorded the finding regarding the shift from RNN/CNN to attention-only architectures.


## Step 8: append_workspace_markdown

Created a raw proposal seed addressing the quadratic complexity bottleneck of the Transformer architecture.


## Step 9: paper_bulk_search

Starting adversarial collision search for the 'Linearized/Sparse Attention' proposal seed by querying recent (2023+) literature on linear and sparse attention mechanisms.


## Step 10: append_workspace_markdown

Recorded MSF-DET as a non-LLM example of linear attention application.


## Step 11: append_workspace_markdown

Recorded IRIS as a hybrid retrieval + linear attention approach for long-context processing.


## Step 12: append_workspace_markdown

Recorded MSA as a significant collision for the 'Linearized/Sparse Attention' seed, targeting extremely long context (100M tokens).


## Step 13: paper_relevance_search

Investigating the specific failure mode of 'precision degradation' in linear and sparse attention models to identify a more specific novelty path.


## Step 14: append_workspace_markdown

Recorded SLA as a hybrid sparse-linear attention mechanism that classifies weights by rank/importance.


## Step 15: append_workspace_markdown

Recorded He et al. (2025) as a direct attempt to solve 'forgetfulness' in linear attention using learnable token eviction.


## Step 16: append_workspace_markdown

Recorded LoLA as a multi-tier memory approach combining sliding windows, sparse caches, and recurrent states to solve associative recall in linear attention.


## Step 17: paper_relevance_search

Searching for explicit critiques and identified failure modes in sparse/linear attention literature to find a high-value gap for a more sophisticated proposal seed.


## Step 18: append_workspace_markdown

Recorded Bai (2024) as a survey providing a taxonomy (global, local, hybrid) for sparse attention strategies.


## Step 19: paper_relevance_search

Refining the research focus toward the specific failure of 'associative recall' in linear attention models, a known weakness that distinguishes them from full attention.


## Step 20: append_workspace_markdown

Recorded Nichani et al. (2024) as a paper providing theoretical insights into the capacity of linear/MLP associative memories for factual recall.


## Step 21: paper_relevance_search

Searching for differentiable or learning-based memory management/caching mechanisms in linear attention to see if the 'decision' of what to store in associative memory can be optimized via gradients rather than heuristics.


## Step 22: append_workspace_markdown

Recorded KV Admission (2025) as a key recent work demonstrating proactive, learned admission control for KV caches to solve long-context efficiency issues.


## Step 23: paper_relevance_search

Searching for rank-aware or information-density-based gating mechanisms in linear attention to see if the 'admission' decision can be mathematically tied to the rank/utility of the token's features.


## Step 24: append_workspace_markdown

Recorded SAGA (2025) as a key work using input-adaptive learnable gates to combat the low-rank bottleneck in linear attention.


## Step 25: paper_relevance_search

Searching for differentiable or information-density-based selection mechanisms to see if the 'decision' of which attention mode to use can be learned based on local sequence characteristics, potentially providing a more nuanced departure from existing fixed or simple-gated methods.


## Step 27: append_workspace_markdown

Recorded DFTopK (2025) as a relevant technical precedent for O(n) differentiable Top-K selection, which could be used to implement efficient, rank-aware attention gating.


## Step 28: append_workspace_markdown

Recorded Ji et al. (2023) as providing a theoretical basis for using information density (surprisal, entropy) for token selection in long documents.


## Step 29: paper_relevance_search

Searching for specific implementations of information-density-based gating in attention to identify if a 'differentiable information-theoretic admission' mechanism is truly a novel direction or already explored.


## Step 30: append_workspace_markdown

Identified a research gap: current attention gating is highly domain-specific (driving, emotion). There is an opportunity to develop a general-purpose, information-theoretic gating mechanism for linear attention.


## Step 31: append_workspace_markdown

Created a second, more refined proposal seed: DITA, focusing on using information-theoretic surprisal as a differentiable gating mechanism for the linear attention recurrent state.
