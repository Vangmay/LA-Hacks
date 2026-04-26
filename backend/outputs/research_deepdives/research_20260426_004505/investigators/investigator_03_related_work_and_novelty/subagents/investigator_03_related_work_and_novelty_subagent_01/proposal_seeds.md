# Proposal Seeds



## Proposal Seed: Linear-Complexity Attention Scaling

- Status: speculative
- Originating taste: Citation-Ancestry Cartographer
- Seed-paper hook: Transformer's quadratic scaling bottleneck (arXiv:1706.03762)
- Evidence trigger: The inherent $O(L^2)$ complexity of the scaled dot-product attention mechanism as $L$ (sequence length) increases.
- Candidate novelty: Identifying or constructing attention approximations that achieve sub-quadratic (ideally linear) complexity without the representational collapse seen in early sparse methods.
- Technical mechanism: Kernel-based approximations (e.g., Performer), sparse/local attention patterns (e.g., Reformer), or integration with State Space Models (SSMs).
- Closest prior-work collision: Linformer, Performer, Reformer.
- Closest future-work collision: FlashAttention (IO-aware), Mamba/S6 (State Space Models).
- Minimum validation: Empirical comparison of training throughput and perplexity/accuracy across increasing sequence lengths ($L=1k$ to $L=100k$).
- Falsification risk: Linear approximations may fail to capture high-frequency or extremely long-range dependencies required for complex reasoning.
- Why this is not generic: It directly addresses the specific architectural trade-off identified in the Transformer's foundational paper (parallelism vs. complexity).
- Confidence: low
- Required next search: 'linear attention mechanisms', 'efficient transformer architectures', 'sub-quadratic attention'


## Proposal Seed: Latent Coordinate Anchors (LCA)

- Status: promising
- Originating taste: Citation-Ancestry Cartographer
- Seed-paper hook: Geometric interpretation of attention sinks (Ruscio et al., 2025) and the 'Registers' solution (Darcet et al., 2023).
- Evidence trigger: The conflict between attention sinks being a 'geometric necessity' for stable coordinate systems and the view that they are 'artifacts' that must be absorbed by register tokens.
- Candidate novelty: Moving from *reactive* absorption (adding extra tokens to catch the 'sink' energy) to *proactive* anchoring (designing a dedicated, structural mechanism that provides the reference frame).
- Technical mechanism: Instead of adding extra input tokens, introduce a lightweight, parallel 'Anchor Module' (possibly a small set of learnable parameter vectors) that serves as an explicit coordinate manifold. Transformer layers would query these anchors via a constrained cross-attention or a specialized gating mechanism to stabilize representational spaces without the noise of high-norm artifact tokens.
- Closest prior-work collision: Darcet et al. (Registers), Jiang et al. (Test-time registers), and the 'Visual Attention Redistribution' (VAR) method.
- Closest future-work collision: State Space Models (SSMs) which handle global context through continuous state updates.
- Minimum validation: 1) Qualitative: compare attention map smoothness and energy distribution in LCA vs. standard ViT/Register-ViT. 2) Quantitative: performance on dense visual prediction tasks and long-context language modeling.
- Falsification risk: The LCA might add significant architectural complexity/overhead without providing a stability gain proportional to its cost.
- Why this is not generic: It directly addresses the fundamental geometric hypothesis of the attention sink phenomenon by providing a structural solution rather than a heuristic token-based one.
- Confidence: medium
- Required next search: 'geometric inductive bias in transformers', 'learnable coordinate systems for neural networks', 'explicit reference frame in attention mechanisms'
