# Proposal Seeds



## Proposal Seed: Dynamic Reasoning-Aware Sparsity (DRAS)

- Status: raw
- Originating taste: Conflict-Oriented Citation Analyst
- Seed-paper hook: Attention is All You Need (quad complexity bottleneck)
- Evidence trigger: Yang et al. (2024) claim that sparse transformers require model size to scale with problem size for reasoning (DP) tasks.
- Candidate novelty: A mechanism that dynamically adjusts sparsity levels based on the 'reasoning depth' required by the current context rather than a fixed global sparsity pattern.
- Technical mechanism: Implement a secondary 'depth-check' head that estimates the recursion/DP depth required for a sequence segment and scales active attention density to match, theoretically preventing the need for the entire model size to scale linearly.
- Closest prior-work collision: Standard Sparse Transformers (fixed patterns) and Mixture of Experts (routing based on identity rather than complexity).
- Closest future-work collision: DynaX (2025) which does dynamic pruning, but focuses on hardware regularity rather than maintaining reasoning capability.
- Minimum validation: Compare DRAS vs standard Sparse Transformers on the 'Chain-of-Thought as DP' benchmark proposed by Yang et al. (2024).
- Falsification risk: Dynamic depth-checking might introduce more overhead than the attention savings it provides, leading to a net loss in throughput.
- Why this is not generic: It specifically targets the *reasoning-capacity* failure mode identified in recent critiques, moving beyond simple speed benchmarks to 'reasoning/computation' ratios.
- Confidence: low
- Required next search: Search for 'dynamic compute allocation based on complexity' or 'depth-stochastic transformers' to see if reasoning-depth sparsity has been attempted.


## Proposal Seed: Semantic Density Gating (SDG) for Sparse Attention

- Status: promising
- Originating taste: Conflict-Oriented Citation Analyst
- Seed-paper hook: Attention is All You Need (Fixed dense attention overhead)
- Evidence trigger: Yang et al. (2024) show that sparse transformers lose reasoning depth unless model size scales. CODA (2026) shows efficiency gains from difficulty-aware token counts but doesn't optimize attention sparsity specifically.
- Candidate novelty: Bridging the gap between 'adaptive depth' (layers/tokens) and 'adaptive sparsity' (attention patterns). Instead of just skipping layers or tokens, SDG dynamically compresses the KV-cache and attention mask density based on a per-token 'complexity gradient' at the first layer.
- Technical mechanism: A lightweight 'Difficulty Predictor' head attached to the embedding layer (trained via distillation from a larger model's attention entropy) to determine the sparsity ratio for subsequent layers. High-entropy (complex) tokens trigger dense global attention; low-entropy (simple) tokens trigger constrained local-only or sparse-random attention.
- Closest prior-work collision: DynaX (2025) which uses dynamic X:M pruning, but for hardware regularity. Sparse Transformers (2019) use fixed patterns. CODA (2026) uses adaptive counts but not adaptive attention patterns.
- Closest future-work collision: ANIRA (2026) uses per-token variable depth but focuses on recurrence rather than fine-grained sparsity modulation.
- Minimum validation: Test on the 'Chain-of-Thought as DP' task (Yang et al., 2024). Measure Accuracy vs. Attention FLOPs compared to fixed Sparse Transformers and CODA.
- Falsification risk: Simple complexity metrics (like entropy) might not correlate with DP-task reasoning requirements, or the overhead of the 'Difficulty Predictor' might exceed the attention savings on short sequences.
- Why this is not generic: It specifically addresses the limitation that sparse models fail on complex reasoning by selectively 'turning density back on' when the data warrants it.
- Confidence: medium
- Required next search: Search for 'attention entropy as a proxy for task difficulty' or 'KV-cache compression via semantic importance'.
