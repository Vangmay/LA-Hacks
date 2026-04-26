# Proposal Seeds



## Proposal Seed: Linearized or Sparse Self-Attention for Long-Sequence Scaling

- Status: raw
- Originating taste: Lineage Architect
- Seed-paper hook: The Transformer (Vaswani et al., 2017) achieves parallelization by removing recurrence but introduces a quadratic $O(n^2)$ complexity bottleneck relative to sequence length.
- Evidence trigger: Finding 'Shift from Recurrent to Pure Attention Architectures' identifies the $O(n^2)$ complexity as the primary trade-off for parallelization.
- Candidate novelty: Developing a mechanism that achieves $O(n)$ or $O(n \log n)$ complexity while maintaining the global receptive field properties that define the Transformer's advantage over RNNs.
- Technical mechanism: Investigation of kernel-based approximations (e.g., approximating the softmax kernel) or structured sparsity patterns (e.g., local window + global anchors) to linearize the attention computation.
- Closest prior-work collision: Sparse Transformers, Linformer, Performer, Reformer.
- Closest future-work collision: FlashAttention (focuses on IO/memory efficiency rather than algorithmic complexity reduction).
- Minimum validation: Implementation of a linearized attention module in a standard Transformer architecture and evaluation on the WMT translation task with varying sequence lengths to measure the complexity-performance tradeoff.
- Falsification risk: The approximation may fail to capture the high-precision dependencies required for complex language tasks, leading to significant performance degradation compared to dense attention.
- Why this is not generic: It targets the specific complexity bottleneck identified as the fundamental consequence of the transition from recurrent to pure-attention architectures.
- Confidence: medium
- Required next search: 'survey of efficient transformer architectures', 'linear attention vs sparse attention performance'


## Proposal Seed: Continuous or Hierarchical Hybridization of Transformers and SSMs

- Status: raw
- Originating taste: Lineage Architect
- Seed-paper hook: MambaFormer (8a3ee6b06695a444b63e79d9ff542d1c7c7b947a) implements hard, token-level routing between Transformer and SSM experts based on sequence length and complexity.
- Evidence trigger: Collision with MambaFormer identifies that 'binary expert routing' is already a documented approach.
- Candidate novelty: Moving from discrete/hard routing (Expert A or Expert B) to continuous, differentiable 'soft' blending of attention and state-space operations, or hierarchical routing where tokens pass through a spectrum of computational densities (e.g., sparse SSM -> dense Transformer).
- Technical mechanism: Implementation of a 'Soft-Switch' layer that computes a weighted combination of the attention output and the SSM state update, where weights are determined by a continuous, learnable gating function. Alternatively, a hierarchical scheme where tokens are first processed by a low-cost SSM and only 'complex' residuals are passed to a Transformer block.
- Closest prior-work collision: MambaFormer (hard routing), Jamba (interleaved/static), A2Mamba (structural mixing).
- Closest future-work collision: Highly optimized MoE-based hybrids.
- Minimum validation: Compare a 'Soft-Switch' hybrid against MambaFormer and Jamba on a standard long-context benchmark (e.g., LongBench), measuring the trade-off between routing granularity and inference latency.
- Falsification risk: The 'soft' blending might negate the efficiency gains of the SSM by forcing the computation of both branches, or the continuous weights might become unstable during training.
- Why this is not generic: It specifically addresses the granularity of the hybrid decision-making process, moving from 'which expert' to 'how much of each architecture'.
- Confidence: low
- Required next search: 'continuous mixture of experts transformer', 'soft routing architectures', 'differentiable architectural switching'
