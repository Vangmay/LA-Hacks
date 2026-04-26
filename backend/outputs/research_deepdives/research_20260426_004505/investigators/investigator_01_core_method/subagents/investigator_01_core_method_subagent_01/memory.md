# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Starting research by resolving the seed paper: Attention is All You Need (arXiv:1706.03762).


## Step 2: append_workspace_markdown

Repaired papers.md by recording the seed paper metadata.


## Step 3: get_references

Querying references of the seed paper to identify its intellectual ancestors (RNNs, CNNs, and early attention mechanisms).


## Step 4: append_workspace_markdown

Recorded the MoE paper (Shazeer et al., 2017) as a foundational reference for conditional computation.


## Step 5: append_workspace_markdown

Recorded the first finding regarding the architectural transition from RNN/CNN to pure attention based on analyzed references.


## Step 6: append_workspace_markdown

Created a speculative proposal seed in proposal_seeds.md targeting the quadratic attention scaling bottleneck by combining Transformer attention with MoE-style conditional computation.


## Step 7: paper_relevance_search

Performing a collision search for the proposal seed 'Sparse-Gated Attention via Conditional Computation' by searching for the recombination of sparse attention and mixture of experts.


## Step 8: append_workspace_markdown

Recorded MoE-DiffuSeq (2025) as a direct collision for the sparse-gated attention proposal seed.


## Step 9: append_workspace_markdown

Recorded DeepSeek-V2 (2024) as a highly relevant neighbor that addresses efficiency via latent attention (MLA) and MoE.


## Step 10: paper_relevance_search

Refining the proposal seed by searching for more specific collisions: 'mixture of attention experts' or 'routing queries to attention experts' to distinguish from simple pipeline combinations of sparse attention and MoE.


## Step 11: paper_relevance_search

The previous specific query returned no results, which is promising for novelty. Now searching for variants like 'mixture of attention heads' or 'moe attention' to see if the concept is being addressed under different nomenclature.


## Step 12: append_workspace_markdown

Recorded MoSA (2025) as a highly relevant collision that uses expert-choice routing to select tokens for sparse attention.


## Step 13: append_workspace_markdown

Recorded the MoA (2022) paper as a direct collision for the 'mixture of attention heads' concept.


## Step 14: append_workspace_markdown

Recorded findings from collision searches, noting that both head-selection (MoA) and token-selection (MoSA) are established paths, requiring a pivot for true novelty.


## Step 15: paper_relevance_search

Attempting to pivot the proposal seed by searching for more advanced recombination: routing between different *types* of attention mechanisms (e.g., sliding window vs global) or different attention resolutions, rather than just head/token selection.


## Step 16: append_workspace_markdown

Recorded ASSENet (2024) as evidence that routing between different attention mechanisms (local vs non-local) is used in specialized domains like speech.


## Step 17: paper_relevance_search

Attempting to pivot the proposal towards a 'Mixture of Attention Complexities' (e.g., routing between sparse and dense attention mechanisms) to find if this hybrid approach is already a known LLM optimization strategy.


## Step 18: append_workspace_markdown

Recorded Mixture-of-Transformers (2024) as a neighbor that applies MoE to modality-specific parameter decoupling.
