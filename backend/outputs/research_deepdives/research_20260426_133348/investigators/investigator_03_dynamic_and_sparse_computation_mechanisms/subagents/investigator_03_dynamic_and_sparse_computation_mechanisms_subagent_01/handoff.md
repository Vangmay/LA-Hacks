# Hand-Off: Dynamic and Sparse Computation Mechanisms

## Overview
The investigation centered on the transition from the dense quadratic attention of the Transformer seed paper to modern dynamic sparse mechanisms. The 'Skeptical Forensic' lens focused on identifying where speedup claims fail theoretical reasoning requirements.

## Top Papers
- **Do Efficient Transformers Really Save Computation? (2024)**: Foundational critique at ICML showing that sparse models require larger sizes to solve Dynamic Programming (DP) tasks, negating simple efficiency gains.
- **CODA: Difficulty-Aware Compute Allocation (2026)**: Establishes a 60% token reduction ceiling through difficulty-aware gating, but primarily at the token/layer level.
- **Sparse Growing Transformer (2026)**: Validates 'attention entropy' as a robust proxy for identifying where extra computation/depth is useful.

## Key Findings
1. **Reasoning-Sparsity Tradeoff**: Sparse transformers are technically inconsistent; they save FLOPs on retrieval but 'lose' the reasoning depth found in the dense seed unless scaled upward, creating a size-overhead trap.
2. **Entropy-Guided Utility**: Attention entropy is no longer just a metric but is being operationalized as a signal to gate compute resources correctly.

## Proposal Seeds
- **Semantic Density Gating (SDG)**: A dynamic sparsity mechanism that uses a first-layer difficulty predictor (distilled from attention entropy) to toggle between local-sparse and global-dense attention patterns. Unlike CODA (which skips layers), SDG optimizes the *internal density* of the attention matrix.

## Uncertainty and Next Steps
- **Uncertainty**: The exact correlation between early-layer entropy and late-layer logic-depth requirements is empirical, not yet theoretically proven across all reasoning tasks.
- **Next Steps**: Investigator should prioritize validating the SDG mechanism on the DP benchmarks identified in the Yang et al. (2024) critique to see if density-switching resolves the model-scaling trap.