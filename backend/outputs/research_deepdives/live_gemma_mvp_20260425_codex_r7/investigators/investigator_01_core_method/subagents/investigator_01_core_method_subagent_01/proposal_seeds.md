# Proposal Seeds



## Proposal Seed: Linearized or Sparse Attention for Long-Context Scaling

- Status: raw
- Originating taste: Lineage Cartographer
- Seed-paper hook: Vaswani et al. (2017) Transformer architecture based on multi-head attention.
- Evidence trigger: The quadratic O(L^2) complexity of the self-attention mechanism relative to sequence length L identified as a primary scaling bottleneck.
- Candidate novelty: Transitioning from dense quadratic attention to a linearized or sparse approximation that maintains the structural benefits of the Transformer while achieving O(L) or O(L log L) complexity.
- Technical mechanism: Implementation of kernel-based linear attention, sparse attention patterns (fixed or learnable), or low-rank approximations of the attention matrix.
- Closest prior-work collision: Longformer, Reformer, Linformer, Performer.
- Closest future-work collision: FlashAttention (optimizes implementation but keeps O(L^2) complexity), State Space Models (Mamba).
- Minimum validation: Perplexity and retrieval performance on long-context benchmarks (e.g., LongBench, Needle In A Haystack) compared to a dense baseline.
- Falsification risk: The approximation fails to preserve the precise dependency modeling required for complex reasoning or high-fidelity retrieval.
- Why this is not generic: It specifically addresses the fundamental algorithmic complexity constraint inherent in the original Transformer design.
- Confidence: medium
- Required next search: Search for recent (2023-2024) advances in 'linear attention', 'sparse attention', and 'efficient sequence transduction' to map the current SOTA landscape and avoid immediate collisions.


## Proposal Seed: Differentiable Information-Theoretic Admission (DITA) for Linear Attention

- Status: promising
- Originating taste: Lineage Cartographer
- Seed-paper hook: Vaswani et al. (2017) Transformer; Ji et al. (2023) Information Density.
- Evidence trigger: The finding that current attention gating (e.g., SAGA, CRiTIC) is highly domain-specific and lacks a generalized, information-theoretic foundation for LLM sequence transduction. Additionally, the known 'forgetfulness' and 'precision degradation' in linear attention models.
- Candidate novelty: Moving from heuristic-based or domain-specific gating to a principled, end-to-end trainable mechanism that uses token surprisal or entropy as a proxy for information utility to decide which tokens are admitted into the linear attention recurrent state.
- Technical mechanism: A lightweight, differentiable 'Surprisal Estimator' module that calculates a token's information density (e.g., via a single-layer predictor or local entropy) and uses this to compute a gating coefficient $\alpha \in [0, 1]$ for the KV update in the linear attention formulation $S_t = \alpha_t (k_t v_t^T) + S_{t-1}$.
- Closest prior-work collision: KV Admission (WG-KV) - uses utility prediction but is focused on KV cache admission/eviction for standard Transformers, not the internal recurrent state of linear attention. SAGA - uses input-adaptive gates but is optimized for vision/rank-deficiency rather than information-theoretic utility.
- Closest future-work collision: Advanced State Space Models (SSMs) that might integrate similar gating natively.
- Minimum validation: Compare DITA-equipped linear attention models against standard linear attention (e.g., Mamba, RetNet) on long-context retrieval tasks (Needle In A Haystack) and perplexity on long-form text, specifically looking for improved retention of high-surprisal 'key' tokens.
- Falsification risk: The computational overhead of the surprisal estimator offsets the gains of the reduced state, or the surprisal metric does not correlate well with long-term semantic importance in autoregressive generation.
- Why this is not generic: It targets the specific intersection of information theory and the architectural weakness (forgetfulness) of linear attention models.
- Confidence: medium
- Required next search: Search for 'differentiable entropy estimation' and 'token surprisal in LLMs' to find efficient ways to implement the estimator without adding significant latency.
