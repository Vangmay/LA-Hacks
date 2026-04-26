# Proposal Seeds



## Proposal Seed: Sparse-Gated Attention via Conditional Computation

- Status: raw
- Originating taste: Citation-Ancestry Cartographer
- Seed-paper hook: Transformer's $O(n^2)$ quadratic attention complexity vs. the MoE conditional computation principle (Shazeer et al., 2017).
- Evidence trigger: The identified limitation of quadratic scaling in the Transformer architecture and the presence of MoE in its immediate citation ancestry.
- Candidate novelty: Using a gating mechanism to select a sparse subset of keys/values (experts) for each query, rather than attending to the entire sequence, to alleviate $O(n^2)$ costs.
- Technical mechanism: A trainable gating network that predicts which segments or 'expert' clusters of the sequence are most relevant to a given query, effectively implementing a Mixture-of-Experts layer within the attention mechanism itself.
- Closest prior-work collision: Sparse Transformers (Child et al., 2019), Reformer (Kitaev et al., 2020).
- Closest future-work collision: Efficient Attention (e.g., FlashAttention) which focuses on IO-awareness rather than sparsity.
- Minimum validation: Compare training/inference time and memory usage of a 'Gated-Attention' model against a standard Transformer on long-sequence benchmarks (e.g., Long Range Arena).
- Falsification risk: The computational overhead of the gating network might negate the savings from sparsity.
- Why this is not generic: It specifically proposes a recombination of the 2017 MoE concept with the attention mechanism to solve the scaling bottleneck identified in the seed paper.
- Confidence: low
- Required next search: Search for 'sparse attention mixture of experts' and 'gated attention mechanism' to check for existing implementation collisions.
