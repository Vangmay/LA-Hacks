# Cross-Investigator Deep Dive: Spinoff Proposals for Sub-Quadratic Inductive Bias Restoration

This synthesis integrates the findings of **Investigator 01 (Scaling & VRAM)** and **Investigator 02 (Inductive Bias & Hybrids)**. It bridges the theoretical "Test-Time Regression" (TTR) framework of 2026 with classical "Robust Control" (H-infinity) to address the performance gap between sub-quadratic models and Transformers.

---

## 1. Global Research Landscape & Contradictions

### Repeated & Foundational Papers
- **Attention is All You Need (2017)**: The $O(n^2)$ baseline cited by all subagents.
- **Mamba / SSM (2023/24)**: The primary sub-quadratic competitor.
- **Transformers are RNNs (2020)**: The linear-attention ancestor.

### Key Evidence Contradictions
1.  **Capability vs. Optimization**: Investigator 01's sources (DeltaNet, 2026) suggest that the performance gap is *architectural* (neglecting curvature), while Investigator 02's sources (Okpekpe, 2025) argue it is largely an *optimization* artifact (fragile learning rates and SNR in selective matrices).
2.  **The "Bandage" Paradox**: Both investigators identify that SOTA hybrids (Griffin, Jamba) use local attention as a "bandage." However, Investigator 01 views this as a fix for **information decay**, while Investigator 02 views it as a fix for **selection/ranking logic**.

### Global Novelty-Risk Patterns
- **Collision Risk**: High overlap exists around Kalman-filter scans (`Luis et al., 2024`). Any proposal focusing on purely Gaussian/L2-optimal recurrence is likely already done. 
- **The "2026 Curve"**: The "Preconditioned DeltaNet" (2026) is the leading edge. Novelty must build *on top* of its curvature-aware TTR framework rather than reinventing standard linear attention.

---

## 2. Spinoff Proposal Candidates

### Proposal Candidate 1: Minimax-Optimal Test-Time Regression (MOTTR)
- **Source proposal seeds**: H-infinity Robust Mamba (Inv 02) + Preconditioned DeltaNet/TTR (Inv 01).
- **Merged idea**: Reframe the "Test-Time Regression" update from a least-squares problem (which assumes L2 Gaussian noise) into a **minimax H-infinity problem** that minimizes worst-case error.
- **Core novelty claim**: First TTR model that provides formal robustness guarantees against "adversarial" or high-entropy context tokens by integrating the H-infinity Riccati update into a hardware-aware associative scan.
- **Evidence basis**: `d3944893...` (DeltaNet 2026) for curvature handling; `3397214...` (Kiriakidis, 2004) for minimax optimality.
- **Mechanism**: The preconditioning matrix $P_t$ in DeltaNet is replaced by an **H-infinity Riccati Gain** $K_t$. The update incorporates a learnable performance bound $\gamma$. When the sequence entropy $H(p_t)$ spikes (indicating "distracting" or noisy tokens), the $\gamma$-bound tightens, making the hidden state $h_t$ "skeptical" of the update.
- **Validation**: Test on LRA and "Needle-in-a-haystack" with injected adversarial tokens (distractors).
- **Falsification**: If the MOTTR Riccati update cannot be simplified into an associative operator (scan-compatible), it will fail to scale $O(n)$ on GPUs.
- **Confidence**: High (Extends established 2026 math with 20th-century robust control).
- **Decision**: **Promote**

---

### Proposal Candidate 2: SNR-Steered Curvature Preconditioning (SACP)
- **Source proposal seeds**: Selective LR Schedules (Inv 02) + Adaptive Curvature Preconditioning (Inv 01).
- **Merged idea**: Dynamically scales the preconditioning factors of a TTR recurrence based on the **Signal-to-Noise Ratio (SNR)** of the selectivity gradients during training.
- **Core novelty claim**: Solves the "Optimization Friction" bottleneck by linking second-order curvature awareness (Inv 01) to training-time gradient dynamics (Inv 02). 
- **Evidence basis**: `91fd1417...` (Okpekpe, 2025) on LR sensitivity; `d3944893...` (DeltaNet 2026) on curvature neglect.
- **Mechanism**: A "Curvature Monitor" tracks the variance of the gradients for the $B$ (Key) and $C$ (Value) projection matrices. If the gradient SNR drops below a threshold (signaling a failure to learn associative recall), the SACP controller boosts the magnitude of the preconditioning matrix diagonal $\text{diag}(P_t)$, effectively "forcing" the model to prioritize second-order information in those heads.
- **Validation**: Success on "Shattering" tasks (Nishi et al.) where standard Mamba and DeltaNet fail to recover after context shifts.
- **Falsification**: If global Adam/AdaFactor updates already implicitly solve this via their own second-moment tracking, the specific SACP mechanism will be redundant.
- **Confidence**: Medium
- **Decision**: **Speculative** (Needs collision search for "Gradient SNRs in Preconditioned Recurrence").

---

### Proposal Candidate 3: Quasiseparable Selection-Gated Hybrid (QSG)
- **Source proposal seeds**: BQTL/RQB (Inv 01) + Selection vs. Coverage Gap (Inv 02).
- **Merged idea**: A video-optimized architecture using a bidirectional quasiseparable mixer for "Coverage" (gathering features across frames) and a sparse, gated attention block for "Selection" (picking the top-1 event).
- **Core novelty claim**: Specifically addresses the pass@k vs pass@1 disconnect documented in 2026 reasoning studies by separating the roles of recurrent mixing and dot-product selection.
- **Evidence basis**: `45ecf603...` (Wang & Reid, 2026) for Selection gap; `ea507df0...` (Hydra, 2024) for quasiseparable mixers.
- **Mechanism**: A "Selection Gate" derived from the quasiseparable mixer's hidden state entropy $H(h_t)$. If the mixer identifies multiple competing high-probability temporal transitions (low selection confidence), it triggers a **FlashAttention-3** sub-block over a 1k-token window to "force" a point-selection.
- **Validation**: Pass@1 accuracy on multi-hour video reasoning benchmarks vs. Pass@k.
- **Falsification**: If the gate triggers attention too frequently, the VRAM footprint will revert to $O(n^2)$, negating the quasiseparable scaling benefits.
- **Confidence**: Medium-High
- **Decision**: **Promote**

---

## 3. Rejected or Weak Ideas

| Idea | Reason for Rejection | Source collision |
| :--- | :--- | :--- |
| **DK-Mamba** | Overlap with existing 2024 work. | `Luis et al. (2024)` |
| **Pure Hierarchical SWA** | Incremental. SCOUT (2025) already explores segment compression. | `SCOUT (2025)` |
| **Mamba for Diffusion** | Too generic; "Gamba" and "Hydra" versions already exist in 2024/25. | `Hong et al. (2025)` |

---

## 4. Final Novelty Score Rubric

| Proposal | Novelty (1-5) | Technical Spec. (1-5) | Evidence (1-5) | Feasibility (1-5) | Research Value (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MOTTR** | 5 | 4 | 5 | 3 | 5 |
| **SACP** | 3 | 3 | 4 | 5 | 4 |
| **QSG** | 4 | 4 | 4 | 4 | 4 |

---

## 5. Summary of Missing Evidence & High-Priority Searches

1.  **Search Collision**: `"H-infinity" Riccati equation "associative scan"` - This is the last check for MOTTR. If a scan-based Riccati derivation exists for minimax control in DL, the novelty drops to 2.
2.  **Benchmark Availability**: Search for the **"Tiny Recursive Reasoning" (2026)** dataset or methodology to replicate the Coverage-vs-Selection gap findings.
3.  **Hardware Profiling**: Triton/CUDA kernels for **Quasiseparable Mixers** vs **FlashAttention-3** are needed to verify if Proposal 3 (QSG) actually saves VRAM in 16GB-32GB environments.