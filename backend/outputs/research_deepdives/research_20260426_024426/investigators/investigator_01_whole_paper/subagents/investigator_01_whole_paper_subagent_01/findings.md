# Findings



## Finding: Transition from Recurrent to Attention-based Architectures

- Claim: The Transformer architecture represents a fundamental shift by dispensing with the recurrence and convolutions used in prior sequence transduction models in favor of pure attention mechanisms.
- Confidence: high
- Evidence:
  - Attention is All you Need (2017) [Seed]
  - Long Short-Term Memory (1997) [Foundational Ancestor]
- Why it matters: This shift addressed the sequential processing bottleneck of RNNs/LSTMs, enabling massive parallelization and training on significantly larger datasets.
- Caveat: While solving the parallelization issue, it introduces a quadratic complexity cost relative to sequence length due to the self-attention mechanism.


## Finding: The Efficiency-Expressiveness Tension in Sequence Modeling

- Claim: The current frontier of sequence modeling is characterized by a fundamental trade-off between the high expressiveness and global dependency modeling of Attention-based Transformers and the linear-time computational efficiency of State Space Models (SSMs).
- Confidence: high
- Evidence:
  - Attention is All you Need (2017) [Seed: high expressiveness, quadratic cost]
  - Mamba-360 (2024) [Survey: SSMs as efficient alternatives]
  - FLASepformer (2025) [Application: using linear attention to solve complexity issues]
- Why it matters: This tension is driving the next wave of architectural innovation, leading to two main research directions: (1) optimizing attention to be linear, and (2) developing SSMs that can match the representational power of attention.
- Caveat: The relative 'superiority' of one over the other often depends heavily on the specific task (e.g., long-context vs. short-context) and the hardware optimization available.
