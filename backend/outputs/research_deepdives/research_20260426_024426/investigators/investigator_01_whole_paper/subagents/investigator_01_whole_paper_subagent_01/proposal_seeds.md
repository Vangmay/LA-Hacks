# Proposal Seeds



## Proposal Seed: Linear-Complexity Attention Mechanisms

- Status: raw
- Originating taste: Cartographer (finding structural bottlenecks)
- Seed-paper hook: Attention is All you Need (2017)
- Evidence trigger: The quadratic $O(n^2)$ computational and memory complexity of the self-attention mechanism relative to sequence length.
- Candidate novelty: Developing attention-like mechanisms that achieve linear $O(n)$ or near-linear complexity without sacrificing the modeling power of global dependencies.
- Technical mechanism: Kernel-based approximations, sparse attention patterns, or integration of state-space models (SSMs).
- Closest prior-work collision: Existing sparse attention (e.g., Longformer) and linearized attention (e.g., Performer).
- Closest future-work collision: Recent advances in State Space Models (e.g., Mamba).
- Minimum validation: Benchmarking on long-context tasks (e.g., Long Range Arena) against standard Transformer and existing linear-time models.
- Falsification risk: Linear approximations may fail to capture fine-grained, high-resolution dependencies required for certain complex reasoning tasks.
- Why this is not generic: Focuses specifically on the architectural scaling bottleneck of the Transformer's core mechanism.
- Confidence: medium
- Required next search: Search for 'linear attention' and 'state space models' to map the current landscape of $O(n)$ sequence modeling.
