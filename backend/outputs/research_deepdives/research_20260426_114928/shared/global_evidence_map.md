# Global Evidence Map: Scaling Beyond Quadratic Complexity & Inductive Bias Restoration

This map synthesizes research findings and novelty spinoff proposals across the full run for the `novelty_ideation` objective. It focuses on bypassing the $O(n^2)$ bottlenecks of the Transformer via State-Space Models (SSMs), Linear Attention, and Control Theory hybrids.

---

## 1. Core Evidence Repository

| Paper ID | Short Title | Year | Search Bucket | Supporting Finding / Evidence Claim | Surfaced By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **204e3073...** | Attention is All You Need | 2017 | Seed Metadata | Established the $O(n^2)$ complexity/VRAM baseline wall. | Inv 01 / Sub 01 |
| **6f68e1bb...** | Transformers are RNNs | 2020 | Foundational | Kernel associativity enables $O(n)$; initial precision failures. | Inv 01 / Sub 01 |
| **a30ac45a...** | How to Train Your HiPPO | 2022 | Foundational | S4 memory derived from Legendre polynomial projections. | Inv 02 / Sub 01 |
| **ea507df0...** | Hydra | 2024 | Recent SOTA | Quasiseparable matrix mixers for bidirectional efficiency. | Inv 01 / Sub 02 |
| **Li et al.** | SCBench | 2024 | Recent SOTA | KV cache (not compute) is the 1M-token VRAM killer. | Inv 01 / Sub 02 |
| **b10e24c7...** | Luis et al. (Kalman Scan) | 2024 | Recent SOTA | Proves Kalman filters are associative scan compatible. | Inv 02 / Sub 01 |
| **d53fe76b...** | Griffin | 2024 | Recent SOTA | Local attention as a "bandage" for linear-recurrence extrapolation. | Inv 02 / Sub 02 |
| **475b1e64...** | SCOUT | 2025 | Frontier | Segment compression mitigates linear state decay. | Inv 01 / Sub 02 |
| **91fd1417...** | Okpekpe & Orvieto | 2025 | Frontier | SSM recall failure is an optimization/LR artifact, not capacity. | Inv 02 / Sub 02 |
| **9df724e6...** | UnHiPPO | 2025 | Frontier | Identifies "noise-free" assumption failure in HiPPO projections. | Inv 02 / Sub 01 |
| **d3944893...** | Preconditioned DeltaNet | 2026 | The Frontier | Linear attention as TTR; first curvature-aware recurrence. | Inv 01 / Sub 01 |
| **45ecf603...** | Tiny Recursive Reasoning | 2026 | The Frontier | Documents "Coverage-vs-Selection" gap in hybrid models. | Inv 02 / Sub 02 |

---

## 2. Research Gaps & Identified Contradictions

| Gap/Contradiction | Evidence Basis | Novelty Risk / Status |
| :--- | :--- | :--- |
| **The "Curvature-Decay" Contradiction** | DeltaNet (2026) vs SCOUT (2025) | DeltaNet fixes local precision via TTR, but doesn't solve long-range hierarchical decay. |
| **The "Bandage" Paradox** | H-infinity Scans vs Griffin (2024) | High: If H-infinity robustness can restore the recurrence, is the "Attention Bandage" still necessary? |
| **Optimization vs Capacity** | Okpekpe (2025) vs Wang & Reid (2026) | Contradiction: Is Associative Recall a structural capacity failure or purely a learning rate problem? |
| **Bidirectional VRAM Scaling for Video** | Hydra (2024) | Underexplored: Quasiseparable mixers for 3D/temporal diffusion volumes vs 2D standard. |

---

## 3. Spinoff Proposal Candidates (`novelty_ideation`)

### Spinoff 1: Hierarchical Preconditioned Recurrence (HPR)
- **Status/Confidence**: Promising / High
- **Seed Mechanism**: Test-Time Regression (TTR) from DeltaNet (2026) + Hierarchical State from SCOUT (2025).
- **Novelty Hypothesis**: A "Delta-Segment-Tree" where parent nodes store compressed second-order summaries of child-state gradients to solve 1M+ context decay.
- **Falsification**: Overhead of summary gradients exceeding the VRAM savings of a hybrid Transformer-KV cache.

### Spinoff 2: HR-Mamba (H-infinity Robust Mamba)
- **Status/Confidence**: Promising / High
- **Seed Mechanism**: Luis et al. (2024) associative Kalman scan.
- **Novelty Hypothesis**: First hardware-aware associative operator for the **H-infinity Riccati update** (Minimax) to handle "distracting" tokens and adversarial distribution shifts.
- **Technical Mechanism**: Data-dependent learnable performance bound $\gamma$ for "skeptical" recurrence.

### Spinoff 3: SelecLR (SNR-Based Selective Learning Rates)
- **Status/Confidence**: Promising / Medium
- **Seed Mechanism**: Okpekpe & Orvieto (2025) optimization friction discovery.
- **Novelty Hypothesis**: Restoring inductive bias through parameter-group schedules that modulate $B$, $C$, and $\Delta$ matrices based on gradient Signal-to-Noise Ratio.
- **Validation Path**: Successful AR training on "shattering" tasks where standard Mamba-2 fails.

### Spinoff 4: BQTL (Bidirectional Quasiseparable Temporal Latents)
- **Status/Confidence**: Speculative / Medium
- **Seed Mechanism**: Hydra (2024) mixers for non-causal tasks.
- **Novelty Hypothesis**: Replacing 3D attention in video diffusion with quasiseparable mixers using a temporal state that "slips" across chunks to maintain global consistency.
- **Validation Path**: FID/FVD scores on 16GB VRAM GPUs vs. Diffusion Transformer (DiT).

---

## 4. Missing Evidence & Future Collision Searches

- **Collision Search (HPR)**: Search for "Recursive Preconditioned Recurrence" or "Hierarchical TTR" in early 2026 preprints.
- **Collision Search (BQTL)**: Verify if "VGamba" (Haruna et al., 2025) or "Diffusion SSMs" (Hong et al., 2025) already solved the temporal "slip-window" consistency.
- **Technical Feasibility (HR-Mamba)**: Mathematical search for the positivity conditions of the H-infinity Riccati operator in a fused Triton kernel.
- **Hardware Audit**: Establish why theoretical $O(N)$ speedups are currently losing to FlashAttention-3 on Blackwell for contexts $<32k$.

---

## 5. Novelty Rubric Summary (Aggregate)

| Metric | Score (1-5) | Reasoning |
| :--- | :--- | :--- |
| **Novelty** | 4.5 | Leverages extreme-recency (2026) foundations (DeltaNet, Tiny Reasoning). |
| **Technical Specificity** | 4.0 | Clear mechanisms named (Riccati scan, SelecLR SNR, Delta-Segment-Tree). |
| **Evidence Support** | 5.0 | Multiple independent subagents confirmed the VRAM/decay/friction gaps. |
| **Research Value** | 4.5 | Directly targets the primary SOTA bottleneck in sequence modeling memory. |

**Final Decision**: Promote HPR and HR-Mamba to full implementation plan; keep SelecLR and BQTL as high-value speculative spinoffs.