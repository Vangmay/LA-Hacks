# Findings



## Finding: Benchmark Gap for Hierarchical Reasoning in Efficient Transformers

- Claim: Current evaluations of efficient (sparse, linearized, low-rank) Transformers lack specific benchmarks for hierarchical reasoning on long-range sequences and key phrase extraction.
- Confidence: high
- Evidence:
  - `f8224bfd21a9c1f3d763a22c9a4d3d24e8676a2e` / 'A Comprehensive Survey On Efficient Transformers' / 2023 / surveys
- Why it matters: Efficiency metrics (FLOPs, memory) often mask the loss of complex reasoning capabilities. If sparse mechanisms selectively drop information to achieve O(n) or O(n log n) complexity, they may fail at tasks requiring deep semantic hierarchies that the original Transformer handles via O(n^2) global attention.
- Caveat: Identifying the gap is the first step; the 'Long Range Arena' (LRA) exists, but this evidence suggests the specific 'hierarchical reasoning' component remains under-evaluated.


## Finding: Dynamic Hub-Spoke Reassignment as a Sparsity Mechanism

- Claim: Hub-and-spoke models with adaptive reassignment allow transformers to maintain O(n) complexity while increasing the expressivity of global communication nodes.
- Confidence: medium
- Evidence:
  - `593edb51e3f96e1d6624f91f99ee88e767187f45` / 'ReHub: Linear Complexity Graph Transformers with Adaptive Hub-Spoke Reassignment' / 2024 / recent_followups
- Why it matters: In contrast to fixed global markers (like BERT's [CLS] or BigBird's global tokens), the ReHub mechanism uses hub-hub similarity to avoid expensive node-hub computations. This provides a template for 'dynamic sparsity' where the attention mask isn't just a fixed pattern but data-dependent at the cluster level.
- Caveat: Currently proven in graph transformers; the 'hub' semantics may not perfectly map to the sequence-position semantics of standard LLMs without additional structure.


## Finding: Coarse-to-Fine Gating for Sparse Attention Efficiency

- Claim: Filtering key-value pairs at a coarse-grained level before performing fine-grained self-attention preserves performance while reducing computational overhead.
- Confidence: high
- Evidence:
  - `478c30abad8d886ddb4fe14683ba8ebb205e311c` / 'Multi-scale Dynamic Sparse Attention UNet' / 2025 / recent_followups
  - `593edb51e3f96e1d6624f91f99ee88e767187f45` / 'ReHub' / 2024 / recent_followups
- Why it matters: This indicates a convergent trend across different domains (medical imaging and graphs) toward 2025: instead of applying a static sparse mask (like Dilated or Strided attention), modern architectures are using a dynamic 'pre-selection' phase. This supports the feasibility of a hierarchical reasoning benchmark (H-REAST) because we can now technically pinpoint the 'coarse gate' as the potential failure point for long-range logic.
- Caveat: The computational overhead of the gating mechanism itself must stay below the savings of the sparse attention for this to remain linear O(n).


## Finding: Load Imbalance Bottleneck in Dynamic Token Pruning

- Claim: Token-based dataflow in dynamic sparse attention leads to severe hardware load imbalance after pruning, which can be mitigated by dimension-based dataflow.
- Confidence: high
- Evidence:
  - `6955f5609bb3a1d8bad8367c7db5ed63c88b28b2` / 'SADIMM' / 2025 / hardware_benchmarks
- Why it matters: This finding provides the 'novelty pressure' for my SOHRA proposal. Most dynamic sparsity methods focus on *what* to prune (semantic/logic) but ignore the *execution* cost. As of 2025, if a dynamic mechanism disrupts the balanced compute grid of a GPU, the efficiency gains from sparsity are lost to latency. Any novel dynamic proposal must therefore include a load-balancing reassignment layer.
- Caveat: Primarily addresses near-memory processing (NMP) but the software load-imbalance claim holds for any SIMD architecture.
