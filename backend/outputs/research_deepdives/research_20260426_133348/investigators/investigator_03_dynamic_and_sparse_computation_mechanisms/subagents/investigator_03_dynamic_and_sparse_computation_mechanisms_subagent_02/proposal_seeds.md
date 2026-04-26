# Proposal Seeds



## Proposal Seed: Hierarchical Reasoning Benchmark for Sparse Transformers (H-REAST)

- Status: raw
- Originating taste: miner_gap_synthesis_02 (Opportunity-Focused Gap Synthesizer)
- Seed-paper hook: The original Transformer (1706.03762) establishes O(n^2) global dependency modeling which supports nested/hierarchical structures.
- Evidence trigger: 'A Comprehensive Survey On Efficient Transformers' (f8224bfd21a9c1f3d763a22c9a4d3d24e8676a2e) explicitly states a gap in benchmarks tailored to evaluating hierarchical reasoning on long-range sequences for efficient models.
- Candidate novelty: Formalization of a 'reasoning-density' metric that measures the capability of sparse attention masks (e.g., BigBird, Longformer) to preserve multi-hop logical chains compared to full attention.
- Technical mechanism: Create a synthetic or semi-synthetic benchmark where answer retrieval requires traversing a tree-path of information across a 32k+ token context, specifically stressing 'hub' vs 'spoke' nodes in sparse systems.
- Closest prior-work collision: Long Range Arena (LRA) - however, LRA tends to focus on classification/retrieval rather than deep logical hierarchy traversal.
- Closest future-work collision: Ruler (2024), which tests long-context recall but lacks specific hierarchical logic stress tests.
- Minimum validation: Evaluate FlashAttention (Full) vs BigBird (Sparse) on the new benchmark to determine where the reasoning breakdown occurs as context grows.
- Falsification risk: If existing sparse models already perform perfectly on hierarchical tasks, the 'gap' is purely an evaluation formality, not a performance bottleneck.
- Why this is not generic: It points to a specific failure to measure *quality of reasoning* rather than just *recall* or *efficiency*.
- Confidence: medium
- Required next search: Search for 'hierarchical reasoning benchmarks' or 'logic-gated long context tasks' to ensure a direct collision doesn't already exist in the 2024-2025 literature.


## Proposal Seed: Self-Organizing Hubs for Reasoning-Aware Sparse Attention (SOHRA)

- Status: promising
- Originating taste: miner_gap_synthesis_02 (Opportunity-Focused Gap Synthesizer)
- Seed-paper hook: The original Transformer (1706.03762) uses global attention; subsequent 'global token' models (BigBird, Longformer) use fixed placeholders like [CLS].
- Evidence trigger: ReHub (593edb51e3f96e1d6624f91f99ee88e767187f45, 2024) shows that dynamic hub-spoke reassignment via hub-hub similarity maintains linear complexity while improving graph reasoning. MDSA-UNet (478c30abad8d886ddb4fe14683ba8ebb205e311c, 2025) supports a 'coarse-to-fine' filtering mechanism.
- Candidate novelty: Replacing static global tokens in long-context models with 'dynamic latent hubs' that self-organize based on semantic clustering of the context, rather than fixed sequence positions or static slots.
- Technical mechanism: Implement a k-means or soft-clustering layer (similar to ReHub's adaptive reassignment) that gathers 'spoke' tokens into semantically consistent 'hubs' at layer N, allowing global reasoning at layer N+1 to happen only between hubs. This avoids the noise and redundancy of fixed-stride sparse masks.
- Closest prior-work collision: Cluster-Former (2020) and Reformer (LSH). However, SOHRA specifically targets the *reassignment* logic using hub-hub similarity to avoid the O(n*H) hub-selection bottleneck.
- Closest future-work collision: Late 2024 work on 'Token Merging' or 'Dynamic Pruning', which usually discards tokens rather than reorganizing them into global communication nodes.
- Minimum validation: Comparison against BigBird on the proposed H-REAST benchmark (hierarchical reasoning across 64k tokens).
- Falsification risk: The clustering overhead may exceed the quadratic savings if the number of hubs is too high, or the gradients through the discrete selection phase may be too unstable.
- Why this is not generic: It moves away from *positional* sparsity toward *semantic* sparsity, grounded in hardware-efficient 'coarse-to-fine' gating trends identified in 2024-2025 literature.
- Confidence: high
- Required next search: Ablation search for 'clustering overhead in dynamic sparse transformers'.
