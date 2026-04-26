# Sub-Quadratic Scaling and Linear Recurrence Convergence: Research Handoff

## Overview
This investigation explored the transition from quadratic O(N^2) attention (Vaswani et al., 2017) to sub-quadratic linear recurrences. The research prioritized the 'Proof-Technique Transplanter' taste, specifically looking for control-theory lemmas (Lyapunov stability, Small-Gain Theorem) that can be applied to ensure the convergence of these modern recurrent architectures.

## Top Papers
- **SpectralGuard (Bonetto, 2026)**: Identifies 'Memory Collapse' attacks in SSMs where the spectral radius is driven to zero, destroying reasoning capacity.
- **LrcSSM (Farsang et al., 2025)**: Proposes a diagonal Jacobian constraint to provide formal gradient-stability guarantees that Mamba and Liquid-S4 lack.
- **Formal Synthesis of Lyapunov Neural Networks (Abate et al., 2020)**: Establishes the feasibility of using ML to synthesize Lyapunov functions for formal stability verification.

## Findings & Research Gaps
- **The Stability Gap**: Modern sub-quadratic models (SSMs) trade the inherent stability of the attention matrix for the efficiency of input-dependent recurrences. This creates a vulnerability where long-range dependencies can be 'erased' by unstable state transitions.
- **Input-Driven Instability**: Most existing control-theory proofs for neural networks focus on autonomous (no input) systems. There is a significant gap in formal guarantees for non-autonomous sequence models where inputs vary at every time step.

## Proposal Seeds
1.  **Lyapunov-Stable Linear Recurrence**: A proposal to transplant discrete-time Lyapunov projection into the layer-wise initialization of linear transformers to ensure the recurrence state stays on a bounded manifold as $N \to \infty$.
2.  **SpectralGuard Layer for Adaptive Lyapunov Re-normalization**: A differentiable regularizer that monitors the spectral radius of the transition operator in real-time and applies a projection to prevent 'memory collapse' attacks/failures.

## Recommended Next Steps
- **Adversarial Simulation**: Investigate the 'Memory Collapse' attack mechanism from the 2026 SpectralGuard paper to see if current sub-quadratic models (Mamba, GLA) are actually susceptible in practice.
- **Lemma Extraction**: Search for 'Perron-Frobenius' applications in linear recurrence transformers to see if spectral radius constraints can be simplified for fast GPU implementation.