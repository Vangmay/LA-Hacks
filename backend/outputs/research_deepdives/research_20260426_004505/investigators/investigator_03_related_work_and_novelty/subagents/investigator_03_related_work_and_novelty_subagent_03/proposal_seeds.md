# Proposal Seeds



## Proposal Seed: Structurally-Constrained Self-Attention

- Status: raw
- Originating taste: gap_miner
- Seed-paper hook: Structured Attention Networks (13d9323a8716131911bfda048a40e2cde1a76a46)
- Evidence trigger: Standard Transformer attention relies on 'soft' dot-product selection, which lacks the explicit structural priors (like trees or graphs) discussed in 'Structured Attention Networks' as being useful for modeling richer dependencies.
- Candidate novelty: Integrating explicit structural inductive biases (e.g., tree-structured or graph-structured constraints) directly into the parallelizable Transformer attention mechanism, moving beyond purely data-driven soft selection.
- Technical mechanism: Implement an attention mask or a bias term derived from a structural prior (e.g., a dependency tree) that modulates the attention weights without breaking the parallel computation flow.
- Closest prior-work collision: Structured Attention Networks (pre-Transformer, less parallel); standard Graph Transformers.
- Closest future-work collision: Hierarchical/Tree-structured Transformers.
- Minimum validation: Evaluate a 'Tree-Masked Transformer' against the vanilla Transformer on syntactic parsing and logical reasoning benchmarks.
- Falsification risk: Explicit structural constraints might restrict the model's ability to discover latent dependencies, leading to performance degradation on non-structured datasets.
- Why this is not generic: It targets the specific tension between the 'flat' nature of self-attention and the known benefits of structural inductive biases.
- Confidence: low
- Required next search: 'Graph Transformer structural inductive bias', 'Transformer attention structural constraints', 'hierarchical attention vs self-attention'.


## Proposal Seed: Injective-Local Linear Attention (IL-LA)

- Status: promising
- Originating taste: gap_miner
- Seed-paper hook: Bridging the Divide: Reconsidering Softmax and Linear Attention (3c0c526d88d0eaa4df75fe0663c7c900fc47c02e)
- Evidence trigger: Linear attention lacks the 'injective property' (leading to semantic confusion where different queries produce identical outputs) and 'effective local modeling' compared to Softmax attention.
- Candidate novelty: A hybrid attention mechanism that decoupling the global context (linear complexity) from local structural precision (injective/sharp) without reverting to $O(N^2)$ complexity.
- Technical mechanism: Implement a dual-stream attention: 1) A global stream using a feature-mapped linear attention designed for higher injectivity (e.g., using non-monotonic feature mappings); 2) A local stream using a highly localized, sharp mechanism (e.g., a sliding-window convolution or a localized kernel) that preserves high-frequency/local structural information.
- Closest prior-work collision: FLatten Transformer (uses focused linear attention); Log-Linear Attention (uses growing hidden states).
- Closest future-work collision: Hybrid SSM-Transformer models (Mamba-style).
- Minimum validation: Compare IL-LA against vanilla Linear Attention and Softmax Attention on tasks requiring both global context and high local precision (e.g., high-resolution image segmentation or long-document parsing).
- Falsification risk: The overhead of the dual-stream or the complexity of the feature mapping might negate the efficiency gains of linear attention.
- Why this is not generic: It directly addresses the specific mathematical failures (injectivity and local modeling) identified as the cause of the linear-softmax performance gap.
- Confidence: medium
- Required next search: 'injective feature maps for linear attention', 'local-global hybrid attention mechanisms', 'non-monotonic kernel attention'
