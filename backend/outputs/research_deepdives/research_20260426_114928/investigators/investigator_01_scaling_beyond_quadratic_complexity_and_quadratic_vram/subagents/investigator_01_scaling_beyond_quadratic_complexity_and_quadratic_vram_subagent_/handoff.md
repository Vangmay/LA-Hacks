# Hand-Off: Scaling Beyond Quadratic Complexity

## Overview
This investigation pursued the pedigree and limitations of sub-quadratic mechanisms, moving from the foundational O(N^2) bottleneck of the Transformer (Vaswani et al., 2017) to the emerging 'Test-Time Regression' (TTR) framework and curvature-aware recurrences (2026). 

## Search Threads & Key Papers
- **Foundational Lineage**: Resolved the seed paper and its primary linear-attention ancestor, *Transformers are RNNs* (Katharopoulos et al., 2020). Identified that the initial optimism for pure kernel-based linear attention was curtailed by precision failures on fine-grained retrieval tasks.
- **Modern Hybrid Architectures**: Identified *SCOUT* (2025) and *LAWCAT* (2025), which signal a retreat from purely linear states toward 'segment compression' and 'hybrid quadratic-linear' systems. These methods re-introduce sparse quadratic attention to 'refresh' the hidden state, counteracting information decay.
- **Theoretical Scaling Frontier**: Discovered *Preconditioned DeltaNet* (2026), which formalizes the 'curvature neglect' in prior linear models. It interprets linear recurrences as online least-squares optimization, suggesting that 'preconditioning' is the mathematical bridge to matching Transformer expressivity.

## Strongest Findings
1. **Information Decay in Pure Linear Models**: Purely linear models (Mamba, etc.) risk performance degradation on long sequences because they struggle to retain detailed information from distant tokens compared to quadratic attention, driving the need for hybrid 'refresh' mechanisms (Finding 1).
2. **TTR Framework as Unified Theory**: Successful sub-quadratic models are essentially performing Test-Time Regression. The performance gap between linear and quadratic attention is largely attributed to ignoring the curvature of the least-squares loss, a gap that 2026-era preconditioning aims to close (Finding 3).
3. **The VRAM Rubric**: Real-world deployment of 'linear' models is increasingly evaluated not just on O(N) complexity but on factual calibration and stability across sequence lengths (Evidence from 2025 medical benchmarking study).

## Proposal Seeds
- **Proposal Seed: Dynamic Kernels**: A method to recover long-range expressivity by adaptively shifting kernel feature maps based on localized entropy.
- **Proposal Seed: Adaptive Curvature Preconditioning**: (Speculative) Building on *Preconditioned DeltaNet*, this idea proposes a dynamic preconditioning factor that scales with the information density of the context window to maximize VRAM efficiency without sacrificing second-order optimization precision.

## Next Steps for Investigator
- **Collision Search**: Verify if 'Adaptive Preconditioning' exists in the very latest 2026-2027 preprints.
- **Ablation Focus**: Investigate if the 'segment compression' in SCOUT can be combined with 'preconditioning' from DeltaNet to create a hierarchical linear recurrence.
- **Hardware Audit**: Test if the chunkwise parallel algorithms described in the 2026 papers actually outperform FlashAttention-3 on Blackwell/equivalent hardware.