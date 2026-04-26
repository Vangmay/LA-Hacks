# Hand-Off: Dynamic and Sparse Computation Mechanisms

## Overview
I performed a literature deep dive into the origins and descendants of sparsity in the Transformer architecture. My research confirms that many 'novel' modern mechanisms are sophisticated rediscoveries of 1980s and 1990s principles from numerical analysis and statistical routing.

## Top Papers and Impact
- **Vaswani et al. (2017) [Seed]**: Identified the $O(n^2)$ attention bottleneck that drives all subsequent sparsity research.
- **Jordan & Xu (1993)**: Foundational Mixture-of-Experts work showing that routing was originally a discrete statistical (EM) problem, not the continuous relaxation used today.
- **Nguyen et al. (2021) [Fmmformer]**: A modern 'rediscovery' that maps the 1985 Fast Multipole Method (N-body interaction) to $O(n)$ attention complexity.
- **Bengio et al. (2015)**: Bridge work that treated conditional computation as a policy problem (RL), a path largely abandoned for simpler top-k gating but potentially valuable for 'hard' sparsity.

## Key Findings
- **MoE Dominance**: Mixture-of-Experts is the primary dynamic mechanism in modern SOTA, but it has shifted from discrete EM-based selection to continuous softmax relaxations, leading to 'expert collapse' and balancing issues.
- **Mathematical Convergence**: The most advanced sparse attention patterns (e.g., FMM-based) converge on the same physics-based mathematics used for gravitational and electrostatic simulations in the 80s.
- **Hardware Bottlenecks**: Many 90s techniques prioritized reduction in operations (FLOPs), while modern 'sparsity' often struggles with the memory-bandwidth and regularity requirements of GPUs.

## Proposal Seeds

### Hard-Thresholded Sparse Retrieval Experts (HT-SRE)
- **Core Idea**: Replace learned, continuous gating networks in MoE with deterministic, discrete retrieval mechanisms (Hashing/k-d trees) from 90s IR to solve expert collapse and gating instability.
- **Evidence Basis**: Jordan & Xu (1993) discrete routing; Shazeer (2017) gating limitations.
- **Collision Risk**: High overlap with 'Switch Transformer' and 'Hash Layers,' but specifically targets the shift back to non-learned, signal-processing-style routing.
- **Next Step**: Search for 90s 'neural associative memory routing' to refine the retrieval mechanism.
- **Confidence**: Medium

## Recommended Next Steps
- Investigate **'Tree-Codes' (Barnes-Hut)** from 80s astrophysics as a potentially simpler alternative to the full Fast Multipole Method for Transformer blocks.
- Look for 90s technical reports on **'Branching Neural Networks'** in the context of early real-time embedded systems where computation was extremely scarce.