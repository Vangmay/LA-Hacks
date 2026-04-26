# Proposal Families: Sub-Quadratic Inductive Bias & Scale Restoration

This document synthesizes findings from Investigator 01 (Scaling & VRAM) and Investigator 02 (Inductive Bias & Hybrids) into concrete research spinoffs. The focus is on bridging the gap between the efficiency of 2023–2025 State-Space Models (SSMs) and the expressive precision of Transformers, utilizing the 2026 "Test-Time Regression" (TTR) and "Curvature-Aware" frameworks.

---

## Family 1: Control-Theoretic Robustness & Optimization
**Core Theme:** Restoring classical stochastic optimality and robust control (Minimax/H-infinity) to modern hardware-aware associative scans to solve optimization friction and outlier sensitivity.

### Proposal Candidate: HR-Scan (H-infinity Robust Associative Scan)
- **Source proposal seeds:** HR-Mamba (Inv-02), Preconditioned DeltaNet (Inv-01).
- **Merged idea:** Formulating the H-infinity minimax Riccati update as a parallel associative operator for LLM recurrences.
- **Core novelty claim:** First implementation of minimax-optimal estimation in a sub-quadratic $O(N \log N)$ scan. Unlike the Kalman Scan (Luis et al., 2024) which minimizes expected error, HR-Scan minimizes the *worst-case* error relative to bounded unknown noise (distractor tokens).
- **Evidence basis:** 
    - `Luis et al. (2024)`: Proven parallel associative scan for Kalman Filters.
    - `Preconditioned DeltaNet (2026)`: Establishes TTR framework; identifies curvature neglect as the primary expressivity gap.
- **Prior-work collision:** Luis et al. (2024) only addresses $L^2$-optimal (Gaussian) noise. Rigatos et al. (2019) has the theory but lacks the DL associative scan formulation.
- **Mechanism:** Derive an associative operator $\oplus$ for the H-infinity update where the performance bound $\gamma$ is a data-dependent learnable parameter. The state $h_t$ update uses a modified gain that becomes "skeptical" of inputs when the Riccati positivity condition is near-violation, effectively filtering "adversarial" or "hallucinatory" context tokens.
- **Validation:** Needle-in-a-haystack under distribution shift; Long Range Arena (LRA) with salt-and-pepper token noise injection.
- **Falsification:** If $\gamma$ optimization consistently leads to Riccati instability (divergence) during gradient descent, the minimax framework is incompatible with non-convex DL optimization.
- **Confidence:** High (Theoretical foundation is firm).
- **Decision:** Promote.

### Proposal Candidate: SelecLR (SNR-Based Selective Learning Rates)
- **Source proposal seeds:** SelecLR (Inv-02).
- **Core novelty claim:** An optimization hybrid that "restores" inductive bias (induction heads) by modulating learning rates based on the Signal-to-Noise Ratio (SNR) of selectivity matrices ($B, C, \Delta$).
- **Evidence basis:** `Okpekpe & Orvieto (2025)`: Proven that AR failure in Mamba is an optimization artifact of LR sensitivity, not capacity.
- **Mechanism:** A "SelecLR" optimizer wrapper. During the first 10% of training, it monitors the $\text{Var}(\nabla)/(E[\nabla]^2)$ of the selectivity matrices. If the SNR is below a threshold (indicating the model is not "hooking" onto associative patterns), it boosts the LR for the $\Delta$ and $C$ matrices relative to the layer norm and mixer weights.
- **Validation:** Successful training on "Shattering" tasks or high-complexity AR where vanilla Mamba-2 fails at standard global LRs.
- **Falsification:** If AR performance remains flat despite high selectivity SNR, the bottleneck is structural state-size capacity, not optimization.
- **Confidence:** Medium.
- **Decision:** Promote.

---

## Family 2: Mechanism-Dynamic Hybrids for the "Selection Gap"
**Core Theme:** Moving from static "architectural sandwiches" (Jamba/Griffin) to dynamic, error-driven hybrids that allocate expensive quadratic attention only where the model detects "Selection" or "Precision" bottlenecks.

### Proposal Candidate: DySelection (Dynamic Surprise-Gated Hybrid)
- **Source proposal seeds:** DyG-Hybrid (Inv-02), ESEK (Inv-01).
- **Merged idea:** A hybrid model that triggers local attention based on the SSM recurrent state’s own uncertainty or "prediction surprise."
- **Core novelty claim:** Solves the "Selection Gap" (Wang & Reid, 2026) where SSMs identify reasoning paths (coverage) but cannot pick the best one (selection). Unlike Griffin (2024), the attention is not static but "sparse-on-detect."
- **Evidence basis:** 
    - `Wang & Reid (2026)`: Documents the Coverage-vs-Selection gap in Mamba-2 hybrids.
    - `Griffin (2024)`: Confirms local attention is an empirical "bandage" for linear models.
- **Mechanism:** The SSM hidden state $h_t$ is used to compute a "Surprise Meter" $\sigma_t = \text{Entropy}(P(x_{t+1} | h_t))$. If $\sigma_t > \tau$, a gated key-value attention head activates for the local window. This allows the model to "focus" only at reasoning forks or high-entropy retrieval points.
- **Validation:** Measure FLOPs vs. Accuracy on reasoning-selection benchmarks (e.g., GSM8K with distractors); should outperform static hybrids by $20\%+$ efficiency.
- **Falsification:** If entropy spikes do not correlate with reasoning selection errors (i.e., the model is "confidently wrong"), the gating mechanism fails.
- **Confidence:** Medium.
- **Decision:** Promote.

---

## Family 3: Hierarchical & Bidirectional Structural Scaling
**Core Theme:** Managing long-range dependency and spatial/temporal consistency in visual and ultra-long text domains using structured state management.

### Proposal Candidate: Delta-Segment-Tree (Hierarchical TTR)
- **Source proposal seeds:** Hierarchical Preconditioned Recurrence (Inv-01), SCOUT (Inv-01).
- **Merged idea:** A tree-structured linear recurrence where parent nodes store preconditioned second-order summaries of child segments.
- **Core novelty claim:** Combines second-order TTR (solving local curvature) with segment compression (solving long-range decay).
- **Evidence basis:** 
    - `Preconditioned DeltaNet (2026)`: Theoretical need for second-order preconditioning.
    - `SCOUT (2025)`: Proven performance of segment compression.
- **Mechanism:** Each sequence segment (e.g., 2k tokens) is processed via a Curie-aware DeltaNet update. The segment’s final state and its curvature preconditioner are "collapsed" into a parent node using a quasiseparable matrix structure. This allows $O(N)$ recurrence while maintaining a "lossless" multi-scale view of the past.
- **Validation:** Needle-in-a-haystack at 1M context vs. Mamba-2 and standard DeltaNet.
- **Falsification:** The method fails if the memory overhead for storing summaries exceeds the VRAM footprint of a 32k-context Hybrid-Transformer.
- **Confidence:** High.
- **Decision:** Promote.

### Proposal Candidate: BQTL (Bidirectional Quasiseparable Temporal Latents)
- **Source proposal seeds:** BQTL (Inv-01), RQB (Inv-01).
- **Merged idea:** Bidirectional non-causal quasiseparable mixers for video diffusion that prevent "ghosting" by slipping a low-rank temporal latent across segments.
- **Core novelty claim:** First video-specific diffusion mixer that uses quasiseparable structures to bridge spatial and temporal patches in a single pass, bypassing the KV cache growth of 3D attention.
- **Evidence basis:** `Hydra (2024)` and `SCBench (2024)` VRAM analysis.
- **Collision Risk:** `VGamba (2025)` or `Hong et al. (2025)` might have implemented bidirectional SSMs, but the "Quasiseparable Slip" across temporal segments is underexplored.
- **Mechanism:** Replaces 3D attention with a Quasiseparable Matrix Mixer (QMM). Includes a persistent "Identity-Latent" $Z_{temp}$ that is updated via quasiseparable mixing but persists across sliding-window boundaries to ensure flicker-free temporal consistency.
- **Validation:** FID/FVD scores on high-res 1-minute video prediction vs. Diffusion Transformers (DiT) within a 16GB VRAM constraint.
- **Falsification:** Failure to eliminate flickering (temporal discontinuity) relative to DiT.
- **Confidence:** Medium (Speculative).
- **Decision:** Promote (as a specialized spinoff).

---

## Rejected or Weak Ideas
- **"Mamba for Everything"**: Rejected as a research premise. Evidence (SCOUT, Wang & Reid) shows pure SSMs have documented precision and selection failures.
- **"Differentiable Kalman-Mamba"**: Rejected due to 1:1 collision with `Luis et al. (2024)`. Promoted only as the "HR-Scan" variant (H-infinity).
- **"Static SSM-Attention Hierarchies"**: Rejected. Superseded by the `DySelection` and `Delta-Segment-Tree` proposals which provide dynamic or theoretical improvements over existing 2024 "sandwich" models.