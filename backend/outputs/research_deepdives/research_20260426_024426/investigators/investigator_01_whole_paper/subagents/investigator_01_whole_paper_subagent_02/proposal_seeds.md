# Proposal Seeds



## Proposal Seed: Efficient Long-Range Dependency Modeling

- Status: raw
- Originating taste: Research-Gap Miner
- Seed-paper hook: Attention is All you Need (2017)
- Evidence trigger: The $O(N^2)$ computational and memory complexity of the self-attention mechanism relative to sequence length $N$.
- Candidate novelty: Exploring non-quadratic mechanisms (e.g., state-space models, sparse/structured attention, or hybrid recurrence) that preserve the parallelizability of Transformers while scaling linearly with sequence length.
- Technical mechanism: Potential use of kernel-based approximations, structured sparsity, or linearized recurrence.
- Closest prior-work collision: Linformer, Performer, Reformer, and more recently, State Space Models (SSMs) like Mamba.
- Closest future-work collision: Hybrids of SSMs and Transformers.
- Minimum validation: Comparison on the Long Range Arena (LRA) benchmark.
- Falsification risk: If linear-time alternatives fail to capture complex dependencies compared to full self-attention in standard NLP tasks.
- Why this is not generic: It specifically targets the quadratic scaling bottleneck inherent in the Transformer architecture.
- Confidence: medium
- Required next search: 'survey of efficient transformer architectures', 'linear attention vs state space models'
