# Hand-Off: Dynamic and Sparse Computation Mechanisms

## Search Summary
- Resolved the root seed: **Attention is All you Need (2017)**.
- Investigated 2023 surveys to identify missing taxonomies: found a gap in **hierarchical reasoning benchmarks** for long contexts.
- Targeted 2024-2025 papers for mechanistic innovation: identified **hub-and-spoke reassignment** (ReHub) and **coarse-to-fine dynamic gating** (MDSA-UNet).
- Examined hardware feasibility: uncovered the **load imbalance bottleneck** in token-based dataflows for sparse models (SADIMM, 2025).

## Key Papers
- **[1706.03762] Attention is All you Need**: Root seed; establishes the O(n^2) global attention baseline.
- **[f8224bfd...] A Comprehensive Survey On Efficient Transformers (2023)**: Evidence source for the hierarchical reasoning benchmark gap.
- **[593edb51...] ReHub (2024)**: Introduces adaptive hub-spoke reassignment for linear complexity.
- **[6955f560...] SADIMM (2025)**: Highlights the performance failure of token-based sparse dataflows on hardware due to load imbalance.

## Findings
- **Benchmark Gap**: Efficient Transformers are rarely tested for hierarchical reasoning density, only for recall/efficiency.
- **Convergent Evolution**: Sparsity is moving from static masks to dynamic 'pre-selection' or 'gating' phases (Coarse-to-Fine).
- **Hardware Conflict**: Dynamic pruning disrupts GPU load balancing unless 'dimension-based dataflow' is employed.

## Proposal Seeds

### 1. H-REAST (Hierarchical Reasoning Benchmark for Sparse Transformers)
- **Core Idea**: Synthetic/semi-synthetic tasks requiring multi-hop logical traversal across 32k+ tokens to measure 'reasoning-density' of sparse masks.
- **Evidence**: Explicitly called for in the 2023 'Efficient Transformers' survey.
- **Confidence**: Medium.

### 2. SOHRA (Self-Organizing Hubs for Reasoning-Aware Sparse Attention)
- **Core Idea**: Replaces static [CLS] tokens with dynamic semantic clusters that use the ReHub mechanism for reassignment and SADIMM's dimension-based dataflow for hardware efficiency.
- **Novelty**: Semantic-based sparsity rather than positional sparsity, grounded in hardware-load-balancing work.
- **Confidence**: High.

## Next Steps
- Investigator should merge H-REAST and SOHRA into a unified 'hierarchical efficiency' proposal.
- Critically evaluate if the clustering overhead for SOHRA negates the sparsity gains on non-NMP hardware.