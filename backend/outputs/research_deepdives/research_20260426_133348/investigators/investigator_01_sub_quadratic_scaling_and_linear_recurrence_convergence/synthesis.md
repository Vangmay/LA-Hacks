# Synthesis Report: Sub-Quadratic Scaling and Linear Recurrence Convergence

**Section Question:** How do modern sub-quadratic architectures (SSMs, Linear Transformers) maintain convergence and representational fidelity compared to the $O(N^2)$ baseline defined in the seed paper?

## 1. Subagent Coverage Table

| Subagent ID | Research Taste | Primary Zone | Key Contribution |
| :--- | :--- | :--- | :--- |
| `subagent_01` | Proof-Technique Transplanter | Control Theory & Stability | Identified legal "Stability Gap" in SSMs; surfaced Lyapunov synthesis and 2026 "Memory Collapse" threats. |

## 2. Literature Buckets

### Seed Metadata
- **204e3073870fae3d05bcbc2f6a8e263d9b72e776**: *Attention is All You Need* (2017). Baseline $O(N^2)$ complexity.

### Foundation & Prior Work (Pre-2023)
- **b25eb299067a5447e3afd550909e6127a07a34f5**: *Formal Synthesis of Lyapunov Neural Networks* (2020). Establishes ML-driven Lyapunov function synthesis for stability.
- **Katharopoulos et al. (2020)**: *Transformers are RNNs*. Foundation for linear attention as recurrence. (Mentioned in evidence strings).

### Recent & Future Follow-ups (2024–2026)
- **22910f92c164971ff6ae886ece9c586c703c7153**: *On Computational Limits of Modern Hopfield Models* (2024). Proves sub-quadratic efficiency depends on pattern-norm thresholds under SETH.
- **33a53331ff99c23997849745cbe4f892316c9e91**: *On the Complexity of the Skolem Problem at Low Orders* (2025). Complexity thresholds for LRS decidability.
- **e1e98a053a81b96d93c30a5c2b0f0f76b06f9571**: *LrcSSM* (2025). Uses diagonal Jacobian constraints for formal gradient-stability in SSMs.
- **02cbf7c87d721ca17b3416d2360350092a21c2c8**: *Mamba-3* (2026). Complex-valued updates and MIMO for state tracking.
- **8fe9ba5ec118c32b3410b0b817b79666ff0951d4**: *SpectralGuard* (2026). Identification of "Memory Collapse" attacks driving spectral radius to zero.

## 3. Prior/Future Collision Table

| Prior Mechanism (Seed/Ancestors) | Future Pressure / Challenge | Collision Point |
| :--- | :--- | :--- |
| **All-to-all Attention** | **Memory Collapse (Bonetto, 2026)** | Attention is stable by design; SSM recurrences are vulnerable to input-driven spectral shrinkage. |
| **Identity Recurrence** | **Diagonal Jacobian (Farsang, 2025)** | Simple linear attention lacks formal guarantees provided by modern constrained SSMs. |
| **Parallel Training** | **Complex-State Tracking (Lahoti, 2026)** | Parallelism in 2017 sacrificed the state-tracking precision now being reclaimed by complex recurrences. |

## 4. Research Gaps with Evidence

- **Gap 1: The Non-Autonomous Stability Gap.**
    - *Evidence:* Abate (2020) vs. Farsang (2025). Most stability proofs focus on autonomous systems; sequence models are non-autonomous (input-driven).
    - *Nature:* Theoretical/Algorithmic. Modern sequence models lack a unified Lyapunov framework that accounts for $x_t$ variation at every step.
- **Gap 2: SETH-Norm Information Collapse.**
    - *Evidence:* Hopfield Limits (2024). Sub-quadratic models may have a "hard ceiling" for information density based on pattern norms. 
    - *Nature:* Complexity-Theoretic. We lack an exact mapping of when a linear recurrence state hits entropic saturation.

## 5. Proposal Candidate Inventory

### Proposal Candidate 1: Adaptive Lyapunov Re-normalization Layer (ALR-Layer)
- **Core novelty claim:** First differentiable control-theory regularizer that prevents "Memory Collapse" in SSMs by enforcing a contraction mapping in real-time.
- **Source subagents:** `subagent_01`
- **Evidence basis:** *SpectralGuard* (2026) and *LrcSSM* (2025).
- **Seed-paper dependency:** Builds on the linear recurrence successors of Vaswani (2017).
- **Difference from seed:** Replaces the $O(1)$ path-length stability of attention with a $O(N)$ stability constraint for recurrences.
- **Closest prior-work collision:** *LrcSSM* (2025) uses restrictive diagonal Jacobians.
- **Closest future-work/SOTA collision:** *SpectralGuard* (2026) only detects collapse; ALR-Layer remediates it during training.
- **Technical mechanism:** Uses the Small-Gain Theorem to apply a projection to the discretization step of an SSM, ensuring the transition operator $A$ maintains a spectral radius $\rho(A) < 1$ relative to a state-dependent Lyapunov function $V(x)$.
- **Minimum viable validation:** Robustness against "Spectral Poisoning" attacks on Long Range Arena (LRA).
- **Falsification criteria:** If the ALR-Layer introduces more FLOP overhead than a quadratic Transformer, or if it inhibits "fast-dynamics" learning in language.
- **Confidence:** Medium-High.
- **Required next searches:** "Differentiable spectral radius approximation"; "Projected gradient descent on Lyapunov manifolds".

### Proposal Candidate 2: Spectral-Gated Complex Recurrence (SGCR)
- **Core novelty claim:** Minimizing the memory overhead of *Mamba-3* by only activating complex-valued kernels when local spectral convergence slows.
- **Source subagents:** `subagent_01`
- **Evidence basis:** *Mamba-3* (2026) and *mmMamba* (2025).
- **Seed-paper dependency:** Re-introduces complex recurrence into the parallelizable Transformer framework.
- **Difference from seed:** Direct contrast to 2017's "No Recurrence" mantra to solve state-tracking issues.
- **Closest prior-work collision:** Gated Linear Attention; Mamba-2.
- **Closest future-work/SOTA collision:** *Mamba-3* (full complex state).
- **Technical mechanism:** $O(1)$ eigenvalue estimation of the state-transition matrix; a gating mechanism switches from real to complex updates only when the moving average of state-norm changes indicates a low-convergence regime.
- **Minimum viable validation:** Associative Recall task benchmarks comparing SGCR vs. Full Complex Mamba-3.
- **Falsification criteria:** If a purely real-valued gated model with a higher hidden dimension outperforms a hybrid complex-gated model at the same parameter count.
- **Confidence:** Medium.
- **Required next searches:** "Eigenvalue-based gating performance in SSMs".

## 6. Rejected or Weak Ideas

- **Recurrence-Augmented Attention Sharpening:** Rejected as *speculative/weak*. Simple weight-averaging or soft-masking in the attention matrix likely achieves similar sparsification without the overhead of a recurrence kernel.
- **Identifying Discrete Recurrence Limits (Capacity Gaps):** Marked as *speculative*. High falsification risk; precision increases (FP32/FP64) may arbitrarily delay state collapse, making "hard" thresholds difficult to prove without strict hardware assumptions.

## 7. Recommended Next Searches

1.  **"Perron-Frobenius applications in linear transformers"**: To find if spectral radius can be constrained via simpler positive-matrix properties rather than full Lyapunov synthesis.
2.  **"Ablation of complex-valued states in Mamba-3"**: To verify if the MIMO improvements are truly decoupled from the complex-valued discretization.
3.  **"Evasion Existence Theorem in sequence models"**: To deep-dive into the 2026 *SpectralGuard* attack mechanism for adversarial robustness proposals.