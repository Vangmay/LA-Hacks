# Proposal Seeds



## Proposal Seed: Compositional Transformer Augmentation via External State

- Status: raw
- Originating taste: Research-Gap Miner
- Seed-paper hook: Peng et al. (2024) show Transformers struggle with function composition in large domains.
- Evidence trigger: Theoretical proof using Communication Complexity in 'On Limitations of the Transformer Architecture'.
- Candidate novelty: Moving beyond parameter scaling to structural changes that explicitly manage intermediate functional state.
- Technical mechanism: Integrating a structured, external state-tracking mechanism (e.g., a differentiable scratchpad or a hierarchical state-space layer) that explicitly preserves and passes intermediate function outputs, thereby reducing the communication load on the self-attention mechanism.
- Closest prior-work collision: Memory-Augmented Neural Networks (MANN), Chain-of-Thought (CoT) prompting, and State Space Models (SSMs).
- Closest future-work collision: Universal scaling laws for compositional tasks.
- Minimum validation: Benchmarking on symbolic reasoning tasks with high nesting depth (e.g., deep tree traversal or complex logical deductions) where domain size scales.
- Falsification risk: If the bottleneck is actually training-time optimization or general representational capacity rather than communication complexity, a structured state may not improve performance.
- Why this is not generic: It specifically targets the *compositionality gap* identified by Peng et al. through a mechanism aimed at reducing communication complexity.
- Confidence: low
- Required next search: Search for 'architectural solutions to function composition in neural networks' or 'external memory for symbolic reasoning in Transformers'.
