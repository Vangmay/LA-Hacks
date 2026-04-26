# Unresolved Conflicts: Scaling, Inductive Bias, and Robustness and State-Space Models

This document outlines the critical contradictions, empirical gaps, and missing literature buckets identified across the scaling and hybrid-modeling investigations. These conflicts must be resolved through targeted follow-up searches and experiments before the spinoff proposals can be finalized with high confidence.

## 1. Primary Technical Contradictions

### A. The "Bandage" Paradox: Optimization vs. Architecture
There is a fundamental disagreement in the 2025-2026 literature regarding why sub-quadratic models (SSMs) fail at complex reasoning tasks:
*   **The Optimization Argument:** Okpekpe & Orvieto (2025) provide evidence that Associative Recall (AR) failures are not structural but are "fragile optimization artifacts" caused by learning rate (LR) and scaling sensitivity.
*   **The Structural Argument:** Wang & Reid (2026) and the creators of Griffin (2024) argue that there is a structural "Selection Gap." They claim SSMs are adept at "coverage" (identifying candidates) but inherently inferior at "selection" (ranking the top-1 candidate), necessitating the "attention bandage."
*   **Unresolved:** If the issue is purely optimization, hybrid models (Jamba, Griffin) are computationally inefficient compared to a properly tuned pure SSM. If the issue is structural, pure SSMs (Mamba-2, DeltaNet) will hit a reasoning ceiling regardless of scale or LR tuning.

### B. Theoretical Complexity vs. Hardware Reality
*   **The Conflict:** DeltaNet (2026) and Hydra (2024) demonstrate theoretical $O(n)$ scaling. However, on modern Blackwell/H100 hardware, FlashAttention-3 (quadratic $O(n^2)$) often maintains a higher throughput for sequences under 32k tokens due to the high constant factor of recurrent scans and the complexity of second-order preconditioning.
*   **Unresolved:** The exact "crossover point" where preconditioned recurrences become practically superior in a VRAM-constrained environment remains a moving target, complicated by the lack of fused Triton/CUDA kernels for these 2026-era models.

### C. State Compression vs. Factual Calibration
*   **The Conflict:** Research into segment compression (SCOUT, 2025) shows significant VRAM savings, but medical and legal benchmarking studies report a documented trade-off where "compressed" recurrent states lead to significantly lower factual calibration (hallucinations) compared to full KV caches.
*   **Unresolved:** It is unclear if second-order preconditioning (DeltaNet) can recover this factual precision without increasing the recurrent state to the point of negating VRAM benefits.

---

## 2. Weak Evidence and Speculative Claims

### A. H-infinity Feasibility at Scale
The proposal for `HR-Mamba` relies on H-infinity robust control theory. While the mathematical lineage is solid (Luis et al., 2024; Rigatos et al., 2019), there is **zero evidence** that the performance bound parameter $\gamma$ can be effectively tuned during backpropagation at LLM scales (1B+ parameters). There is a high risk that the Riccati positivity conditions will lead to gradient divergence.

### B. Bidirectional Video VRAM Footprint
`Hydra (2024)` claims superior performance for bidirectional tasks, but its application to 3D video volumes (as proposed in `BQTL`) is speculative. Evidence for the VRAM footprint of quasiseparable mixers at 1M+ token video scales (temporal + spatial) compared to 2D image scales is missing.

### C. The Mamba-2 "Selection Gap" at Scale
The "coverage-vs-selection" disconnect (Wang & Reid, 2026) was documented on **"tiny" 7M parameter models**. There is currently no evidence confirming whether this gap persists at 1B+ scales or if the "Selection Gap" is simply an emergent property that disappears with standard scaling laws.

---

## 3. Missing Literature Buckets & Failed Searches

*   **Associative Scan Compatibility for Riccati Updates:** We have confirmed the Kalman Filter (L2) can be formulated as an associative scan (Luis et al., 2024), but we lack a definitive search confirming if the H-infinity Minimax Riccati update satisfies the same properties of an associative operator.
*   **VGamba (2025) Collision Search:** A search for "VGamba" is needed to ensure the bidirectional temporal persistence proposed in `BQTL` was not already solved by Haruna et al. (2025).
*   **Fused Kernel Performance:** Failed to find empirical benchmarks for "Preconditioned DeltaNet" implementation vs. "FlashAttention-3" on Blackwell architectures.
*   **Selective Ranking Inductive Bias:** There is a missing link between the "Selection Gap" literature and parallel research into "Mixture of Depths" or "Selective Ranking" layers.

---

## 4. Required Follow-up Searches

To move the proposal candidates from `Speculative` to `Promising/Promote`, the following exact searches are required:

1.  **Search Query:** `"VGamba" Haruna (2025) bidirectional video diffusion`
    *   *Purpose:* Kill or refine `BQTL` and `RQB` proposals.
2.  **Search Query:** `associative scan implementation of H-infinity Riccati equation`
    *   *Purpose:* Determine the implementation feasibility of `HR-Mamba`.
3.  **Search Query:** `SNR (Signal-to-Noise Ratio) of Mamba selectivity gradients training-time`
    *   *Purpose:* Validate the mechanism of the `SelecLR` proposal.
4.  **Search Query:** `"quasiseparable matrix" Triton kernel implementation VRAM`
    *   *Purpose:* Verify if the VRAM savings claimed for Hydra/BQTL are achievable on current hardware.
5.  **Search Query:** `"Selection Gap" Transformer vs SSM at 1B+ scale`
    *   *Purpose:* Check if the findings from `Tiny Recursive Reasoning` (2026) have been replicated in larger models.