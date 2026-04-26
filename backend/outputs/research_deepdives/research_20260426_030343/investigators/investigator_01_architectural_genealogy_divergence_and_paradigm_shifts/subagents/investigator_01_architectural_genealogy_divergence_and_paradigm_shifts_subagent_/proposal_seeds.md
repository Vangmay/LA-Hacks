# Proposal Seeds



## Proposal Seed: Lineage-based Architectural Analysis

- Status: raw
- Seed-paper hook: Attention is All you Need (2017)
- Evidence trigger: The shift from recurrent/convolutional to attention-only architectures suggests a recombination of existing attention primitives.
- Candidate novelty: Mapping the specific topological shifts from RNN/CNN primitives to pure attention mechanisms.
- Technical mechanism: Comparative structural analysis of sequence transduction primitives.
- Closest prior-work collision: General architectural surveys of deep learning.
- Closest future-work collision: Mechanistic interpretability studies of attention.
- Minimum validation: Systematic identification of inherited vs. novel primitives in Transformer variants.
- Falsification risk: The architecture might be a complete paradigm break rather than a reconfiguration.
- Why this is not generic: It focuses specifically on the inheritance and divergence of architectural primitives in the sequence transduction lineage.
- Confidence: low
- Required next search: Foundational papers for sequence transduction models (RNNs/CNNs) prior to 2017.


## Research Direction: Scaling Self-Attention Complexity

- Status: research_direction
- Seed-paper hook: Attention is All You Need (2017)
- Evidence trigger: The inherent $O(L^2)$ computational and memory complexity of the self-attention mechanism with respect to sequence length $L$.
- Candidate novelty: Investigating architectural variations that achieve sub-quadratic or linear complexity while preserving the global dependency modeling capability of the original Transformer.
- Technical mechanism: Sparse attention patterns, kernel-based approximations (e.g., Performer), or integration of State Space Models (SSMs).
- Closest prior-work collision: Linformer, Reformer, Performer, and more recently, Mamba (SSM-based).
- Closest future-work collision: Emerging hybrid architectures combining attention with recurrent or convolutional components.
- Minimum validation: Comparative analysis of perplexity and training/inference throughput on long-context benchmarks like Long Range Arena (LRA).
- Falsification risk: Efficiency gains might be offset by significant loss in modeling precision or increased implementation complexity on modern hardware.
- Why this is not generic: Specifically targets the scaling bottleneck of the core attention mechanism identified in the seed architecture.
- Confidence: high
- Required next search: 'sub-quadratic attention mechanisms' and 'linear complexity transformers'
