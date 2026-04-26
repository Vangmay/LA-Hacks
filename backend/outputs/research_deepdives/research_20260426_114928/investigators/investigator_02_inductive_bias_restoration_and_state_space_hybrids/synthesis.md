# Synthesis Report: Inductive Bias Restoration and State-Space Hybrids
**Investigator ID:** `investigator_02_inductive_bias_restoration_and_state_space_hybrids`

## 1. Section Question
How can the foundational inductive biases of classical control theory and signal processing be "restored" to modern State-Space Models (SSMs) to solve identified failures in associative recall, robustness, and reasoning selection, and what are the hardware-aware constraints on these hybrids?

## 2. Subagent Coverage Table

| Subagent | Taste/Archetype | Research Zone | Key Contribution |
| :--- | :--- | :--- | :--- |
| **Subagent 01** | Deep-Time Inductive Cartographer | Prior Art & Mathematical Lineage | Traced S4/Mamba to orthogonal polynomials; identified the "noise-free" gap in HiPPO; proposed H-infinity robust scans. |
| **Subagent 02** | Hybrid Friction Forensic | Recent Critiques & Scaling | Identified optimization friction (LR sensitivity) as the cause of recall failure; mapped "Coverage vs. Selection" gaps in Mamba-2. |

## 3. Literature Buckets

### Foundational References & Closest Prior Work
| Paper ID | Title | Year | Role |
| :--- | :--- | :--- | :--- |
| `a30ac45ac...` | How to Train Your HiPPO | 2022 | Explains S4 memory via Legendre polynomial projections. |
| `3397214bb...` | Kiriakidis & O'Brien (H-infinity) | 2004 | Foundational robust control theory for worst-case perturbations. |
| `204e30738...` | Attention is All You Need | 2017 | Seed baseline for all sequence modeling comparisons. |

### Recent & Future Related Work (2024-2026)
| Paper ID | Title | Year | Relation |
| :--- | :--- | :--- | :--- |
| `9df724e66...` | UnHiPPO | 2025 | Identifies noise-free assumption failure in HiPPO frameworks. |
| `b10e24c77...` | Luis et al. (Kalman Scan) | 2024 | Proves Kalman filters are associative scan compatible (RL context). |
| `91fd14173...` | Okpekpe & Orvieto (AR Failure) | 2025 | Proves Mamba recall failure is an optimization/LR artifact. |
| `d53fe76bd...` | Griffin | 2024 | Establishes local-attention as a necessary "bandage" for extrapolation. |
| `45ecf6033...` | Tiny Recursive Reasoning | 2026 | Documents "Coverage-vs-Selection" gap in Mamba-2 hybrids. |

## 4. Closest Prior/Future-Work Collision Table

| Proposal Concept | Potential Collision | Status | Risk Level |
| :--- | :--- | :--- | :--- |
| Associative Kalman SSM | **Luis et al. (2024)** | High overlap in RL; niche open for LLM/GenAI. | High |
| H-infinity SSM Scans | **Rigatos et al. (2019)** | Theory exists; scan-based GPU implementation missing. | Low |
| Selective LR Schedules | **Layer-wise Adaptive LR** | General methods exist; SSM-parameter SNR focus is new. | Medium |
| Gated Hybrid | **Griffin / Jamba** | Existing hybrids are "static"; dynamic gating is a gap. | Medium |

## 5. Research Gaps with Evidence
- **The Stochastically-Weak Recurrence**: HiPPO assumes noise-free data (`UnHiPPO, 2025`). Modern SSMs lack the online stochastic filtering (Kalman) or robust minimax estimation (H-infinity) that defined 20th-century state-space control.
- **The Optimization-Inductive Bias Paradox**: Associative Recall failures in Mamba are often mistaken for architectural incapacity when they are actually "fragile" optimization issues related to scaling and LR (`Okpekpe & Orvieto, 2025`).
- **The Selection Gap**: Hybrid SSM-Attention models resolve "coverage" (identifying multiple reasoning paths) but remain inferior to pure Transformers in "selection" (picking the best top-1 candidate) (`Wang & Reid, 2026`).

---

## 6. Surviving Proposal Candidates

### Proposal Candidate: HR-Mamba (H-infinity Robust Mamba)
- **Core novelty claim**: First integration of minimax-optimal H-infinity robust estimation into the hardware-aware associative scan framework used by modern SSMs.
- **Source subagents**: Subagent 01
- **Evidence basis**: `Luis et al. (2024)` for Kalman associative scans; `Rigatos et al. (2019)` for H-infinity robustness in non-linear systems.
- **Seed-paper dependency**: Mamba / S4.
- **Difference from seed**: Replaces deterministic or L2-optimal (Kalman) recurrence with a minimax update that minimizes worst-case error, providing formal guarantees against "distracting" tokens.
- **Closest prior-work collision**: Luis et al. (2024) (Kalman focus).
- **Closest future-work/SOTA collision**: Robust Control-based DL in SDE/ODE frameworks.
- **Technical mechanism**: Derive a associative operator for the H-infinity Riccati update. Implement the performance bound $\gamma$ as a data-dependent learnable parameter, allowing the recurrence to become "skeptical" of high-entropy inputs.
- **Minimum viable validation**: Robustness on Long Range Arena (LRA) under adversarial state perturbation/noise injection.
- **Falsification criteria**: If the H-infinity Riccati positivity conditions cannot be maintained during gradient descent, the model will diverge.
- **Confidence**: High

### Proposal Candidate: SelecLR (SNR-Based Selective Learning Rates)
- **Core novelty claim**: Restoring SSM inductive bias through parameter-group-specific LR schedules based on the Signal-to-Noise Ratio (SNR) of selectivity gradients.
- **Source subagents**: Subagent 02
- **Evidence basis**: `Okpekpe & Orvieto (2025)` (Optimization friction as the root of AR failure).
- **Seed-paper dependency**: Mamba-2.
- **Difference from seed**: Baseline Mamba uses global LR; SelecLR modulates only the $B$, $C$, and $\Delta$ matrices (the "selective" core) to force the formation of induction-head-like behaviors.
- **Closest prior-work collision**: AdaFactor/Adam (general adaptive LR).
- **Closest future-work/SOTA collision**: Work on "Mamba gradient dynamics" (likely in review for ICLR 2025/2026).
- **Technical mechanism**: Monitor gradient variance during the first 1k steps. If SNR in selectivity matrices is below a threshold, boost the LR for these specific parameters while keeping the mixer LR stable.
- **Minimum viable validation**: Successful training on "Shattering" tasks or high-complexity Associative Recall where vanilla Mamba fails.
- **Falsification criteria**: If AR failure persists despite high SNR in selectivity matrices, the bottleneck is architectural capacity (state size), not optimization.
- **Confidence**: Medium

### Proposal Candidate: DyG-Hybrid (Dynamic Gradient-Gated Hybrid)
- **Core novelty claim**: A "Soft-Hybrid" that gates local attention based on SSM prediction confidence/entropy, moving beyond "static" architecture sandwiches like Griffin or Jamba.
- **Source subagents**: Subagent 02
- **Evidence basis**: `De et al. (2024) (Griffin)` and `Wang & Reid (2026)` (Selection gap).
- **Seed-paper dependency**: Griffin / Hawk.
- **Difference from seed**: Griffin uses a fixed interleaved ratio of attention/SSM. DyG uses a "Surprise Meter" to trigger attention only at tokens where the recurrence bottleneck is mathematically present.
- **Closest prior-work collision**: Static Hybrids (Jamba/Griffin).
- **Closest future-work/SOTA collision**: "Dynamic Depth" or "Mixture of Depths" models.
- **Technical mechanism**: Entropy-based gating. If $H(p_t) > \text{threshold}$, the attention block activates. The gating signal is derived from the SSM's own hidden state uncertainty.
- **Minimum viable validation**: Measure FLOPs vs. Accuracy tradeoff on "Reasoning Selection" tasks; should outperform static hybrids by allocating compute only to "selection" bottlenecks.
- **Falsification criteria**: If entropy spikes do not correlate with reasoning selection errors, the gating mechanism will be noisy.
- **Confidence**: Medium

---

## 7. Rejected or Weak Ideas
- **Differentiable Kalman-Mamba (DK-Mamba)**: Rejected due to direct collision with `Luis et al. (2024)` which already derived the associative scan Kalman filter. Novelty was too thin without shifting to minimax/robustness.
- **State-Expansion Scaling**: Rejected as "generic". Simply increasing state size (Mamba-2) is already identified as insufficient for solving "Selection" errors in 2026 literature.

## 8. Novelty-Risk Matrix
| Proposal | Theoretical Novelty | Implementation Risk | Collision Risk |
| :--- | :--- | :--- | :--- |
| **HR-Mamba** | High | Extreme (Riccati Stability) | Low |
| **SelecLR** | Medium | Low | Medium |
| **DyG-Hybrid** | Medium | Medium (Training Stability) | High |

## 9. Contradictions & Weak Spots
- **The "Bandage" Paradox**: There is a contradiction in findings. Subagent 01 argues we can "restore" the recurrence to be robust (H-infinity), implying we don't need attention. Subagent 02's evidence suggests attention is a "mandatory bandage" for selection.
- **Optimization vs. Capacity**: `Okpekpe` claims it's just LR; `Wang & Reid` claim it's a structural selection gap. This remains the core tension for the next research phase.

## 10. Recommended Next Search
- **Search Query**: `"H-infinity" Riccati equation "associative scan" implementation`
- **Search Query**: `"selection inductive bias" vs "coverage inductive bias" transformer ssm`
- **Missing Bucket**: **Benchmark/Reproduction Stress Tests** for H-infinity bounds in neural networks—very little evidence exists on whether $\gamma$ tuning is feasible in LLM scales.