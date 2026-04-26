# Findings



## Finding: Scaling Limits of Efficient Transformer Variants

- Claim: Sparse and Linear Transformer variants often fail to provide theoretical efficiency guarantees for complex reasoning tasks (Dynamic Programming) without scaling model size proportional to problem size.
- Confidence: High (Supported by ICML 2024 theoretical analysis)
- Evidence:
  - `50503f1de00c567dec1ca8b2fa9d81e822bbed5f` (Do Efficient Transformers Really Save Computation?, 2024)
- Why it matters: This contradicts the common 'quadratic-to-linear' marketing of sparse attention. If model size must scale with problem size to maintain reasoning depth, the 'efficiency' is effectively a tradeoff, not a free win. This provides a direct 'novelty pressure' point to investigate hybrid dense-sparse mechanisms that stabilize this scaling.
- Caveat: The finding is specific to DP-modeled reasoning tasks; it may not hold for simple sequence memorization or low-depth retrieval tasks.


## Finding: Adaptive Reasoning Compute Gains

- Claim: Difficulty-aware compute allocation (adaptive reasoning) can reduce token costs by upwards of 60% on simple tasks while maintaining or improving accuracy on complex tasks through more deliberative rollouts.
- Confidence: High (Supported by 2026 work on adaptive reasoning policies)
- Evidence:
  - `bcc5304b13840cc407025d72d1bd45b0abe99ebc` (CODA: Difficulty-Aware Compute Allocation for Adaptive Reasoning, 2026)
- Why it matters: Establishes a concrete performance ceiling/floor for dynamic computation. Any new sparse mechanism must justify its own overhead against these 'adaptive depth' or 'adaptive rollout' baselines. It suggests that the bottleneck in scaling is not just the attention matrix size, but the lack of a 'halting' or 'density-switching' signal aligned with task difficulty.
- Caveat: Current methods primarily focus on token counts or layer halting; the intersection of task difficulty with *fine-grained sparse attention patterns* remains underexplored.
