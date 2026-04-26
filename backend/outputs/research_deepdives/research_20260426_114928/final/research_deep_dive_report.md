# Final Research Deep Dive Report: Sub-Quadratic Inductive Bias & Scale Restoration

**Seed Paper:** *Attention is All You Need* (2017)  
**Objective:** `novelty_ideation`  
**Current Research Horizon:** April 2026

---

## 1. Executive Summary

This report synthesizes a comprehensive research trajectory from the $O(n^2)$ Transformer baseline toward sub-quadratic architectures. Leveraging a 2026 evidence base (notably *Preconditioned DeltaNet* and *Okpekpe & Orvieto*), we identify that the performance gap between State-Space Models (SSMs) and Transformers is driven by **optimization friction** (sensitivity to learning rates) and **curvature neglect** (ignoring second-order information in least-squares updates).

We propose eight concrete spinoff research directions. The primary clusters focus on **MOTTR (Minimax-Optimal Test-Time Regression)** and **HPR (Hierarchical Preconditioned Recurrence)**, which bridge classical robust control theory with hardware-aware associative scans. We refactor the "Attention Bandage" (hybridization) into dynamic gating and curvature-aware preconditioning. Crucially, these proposals move beyond "applying method X to domain Y" by providing specific technical mechanisms—such as **Diagonalized Riccati Gains** and **Semi-Group Segment Summaries**—to solve documented failures in associative recall and long-range factual calibration at $1M+$ token scales.

---

## 2. Seed Paper Metadata

| Metric | Details |
| :--- | :--- |
| **Title** | Attention is All You Need |
| **Paper ID** | `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (ARXIV:1706.03762) |
| **Year** | 2017 |
| **Venue** | NIPS 2017 |
| **TLDR** | Introduces the Transformer architecture, replacing recurrence with self-attention to enable parallelization. |
| **Primary Limitation** | $O(n^2)$ complexity, leading to the "VRAM Wall" in long-context modeling. |

---

## 3. Literature Map by Bucket

### A. Foundational References
*   **Transformers are RNNs (2020)**: Established kernel associativity as the path to $O(n)$.
*   **How to Train Your HiPPO (2022)**: Proves SSM memory comes from Legendre polynomial projections.

### B. Sub-Quadratic Challengers (2023-2024)
*   **Mamba (2023)**: Selective state-space models using hardware-aware parallel scans.
*   **Hydra (2024)**: Quasiseparable matrix mixers for bidirectional efficiency.
*   **Griffin (2024)**: Hybrid model using local attention as a "bandage" for linear-recurrence.
*   **Luis et al. (2024)**: Proves Kalman filters are associative scan compatible.

### C. The 2025-2026 Frontier
*   **Preconditioned DeltaNet (2026)**: Postulates "Test-Time Regression" (TTR); solves "curvature neglect".
*   **Okpekpe & Orvieto (2025)**: Argues that SSM failures are optimization artifacts rather than structural capacity issues.
*   **Wang & Reid (2026)**: Documents the "Coverage-vs-Selection" gap in hybrid models.
*   **SCOUT (2025)**: Proposes segment compression to mitigate information decay at $1M+$ context.

---

## 4. Closest Prior Work

| Paper | Year | Relation | Mechanism |
| :--- | :--- | :--- | :--- |
| **Transformers are RNNs** | 2020 | Intel. Ancestor | Linear kernel approximation of softmax. |
| **Mamba** | 2023 | Direct Competitor | Selective recurrence via hardware-aware scan. |
| **Luis et al.** | 2024 | TTR Precursor | Kalman parallel associative scans (L2-optimal). |
| **Gated Linear Attention**| 2024 | TTR Precursor | Delta-rule updates for associative memory. |

---

## 5. Direct Follow-ups and Recent State of Field

The field has shifted from "Transformers vs. SSMs" to **"Curvature-Aware Regressions"**.
1.  **TTR Framework**: Successful sub-quadratic models (Mamba-2, DeltaNet) are now interpreted as online least-squares solvers.
2.  **KV Cache Crisis**: SCBench (2024) established that for $1M+$ tokens, the KV cache (not compute) is the primary VRAM bottleneck.
3.  **The Bandage Era**: Models like Jamba successfully use attention "patches," but the 2026 trend is toward removing these patches by addressing the underlying "Selection Gap" via improved optimization.

---

## 6. Critiques, Limitations, and Benchmark Evidence

*   **Optimization Friction**: *Okpekpe (2025)* found that Mamba failures on Associative Recall are largely due to learning rate sensitivity.
*   **Coverage-Selection Disconnect**: *Wang & Reid (2026)* documented that SSM hybrids generate correct reasoning candidates (coverage) but fail to pick the best top-1 (selection).
*   **Curvature Neglect**: *DeltaNet (2026)* identified that prior linear models ignored the curvature of the loss, leading to precision gaps.
*   **Associativity Risk**: *Critique Objections* noted that complex Riccati updates ($O(d^3)$) and non-associative hierarchical trees could revert these models to slow $O(n)$ sequential processing.

---

## 7. Novelty Comparison Table

| Mechanism | Seed (Transformer) | Current SOTA (Mamba-2/DeltaNet) | Proposed Spinoffs |
| :--- | :--- | :--- | :--- |
| **Complexity** | $O(n^2)$ | $O(n)$ | **$O(n)$ w/ Minimax Stability** |
| **Recall Logic** | Precise | Optimization Fragile | **SNR-Steered Preconditioning** |
| **Long-Context** | Quadratic KV | Recurrent Decay | **Hierarchical TTR Summaries** |
| **Video Scaling** | 3D Attention | Simple Scans | **Quasiseparable Slips** |

---

## 8. Research-Gap Candidates

*   **Gap 1: The "H-infinity Scan"**: While Kalman scans (L2-optimal) were derived in 2024, the transformation of minimax-optimal H-infinity updates into an associative operator is missing.
*   **Gap 2: Curvature-Decay Conflict**: DeltaNet (2026) solves local precision but does not address long-range decay identified in SCOUT (2025).
*   **Gap 3: Hardware Padding in Elastic states**: Dynamic hidden states break GPU tiling; there is a gap for hardware-compatible "mixture of state-sizes."

---

## 9. Proposal Seed Inventory and Rejected Ideas

### Rejected or Weak Ideas
*   **DK-Mamba (Differentiable Kalman)**: Rejected; direct overlap with Luis et al. (2024).
*   **Pure Hierarchical SWA**: Rejected; incremental over SCOUT (2025).
*   **Static Hybrid Interleaving**: Rejected; Jamba and Griffin have already saturated this space. 

### Surviving Seed Inventory
*   **Seed 1**: MOTTR (Robust $H_\infty$ scans).
*   **Seed 2**: HPR (Segment-tree TTR).
*   **Seed 3**: QSG (Entropy-gated selection).
*   **Seed 4**: MoSS (State-size MoE).

---

## 10. High-Confidence Spinoff Proposals

### Spinoff Proposal: MOTTR (Minimax-Optimal Test-Time Regression)

#### One-sentence idea
Reframe the hidden state update as a robust $H_\infty$ minimax optimization problem implemented via a low-rank, diagonalized associative scan to keep $O(d)$ complexity.

#### Core novelty claim
First sub-quadratic model that provides formal robustness guarantees against high-entropy "distractor" tokens by integrating the $H_\infty$ Riccati update into a fused scan kernel.

#### Seed-paper connection
- Seed mechanism/claim: Pairwise self-attention (Vaswani et al. 2017).
- What the seed paper does: Global interaction that is precisely but quadratically computed.
- What this proposal changes: Replaces global interaction with a "skeptical" recurrence that minimizes worst-case estimation error relative to bounded unknown noise.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Kalman Associative Scan | Luis et al. (2024) | Proves filters can scale $O(N \log N)$ on GPUs. |
| Curvature Neglect | DeltaNet (2026) | Establishes the TTR framework as the successor to linear attention. |
| H-infinity Robust Control | Kiriakidis (2004) | Provides the $H_\infty$ math required for minimax optimality. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Parallel Kalman Filter | Luis et al. (2024) | High overlap; uses L2 noise. | MOTTR handles adversarial/non-Gaussian token noise via minimax gain. |

#### Future-work/SOTA collision
*DeltaNet-v2* (expected 2026) likely uses preconditioning but remains L2-based.

#### Technical mechanism
Replaces the preconditioning matrix $P_t$ in DeltaNet with an **$H_\infty$ Riccati Gain** $K_t$. To solve the $O(d^3)$ bottleneck, we use a **Diagonalized Riccati approximation** where the gain update is constrained to the spectral diagonal, preserving the associative scan property $(\oplus)$ for GPU acceleration.

#### Minimum viable validation
- First experiment/proof/implementation: Test on Long Range Arena (LRA) with injected "salt-and-pepper" distractor tokens.
- Required dataset/tool/formalism: SCBench context retrieval; Triton kernel implementation.
- Success criterion: $10\%+$ higher accuracy than Mamba-2 on "Needle-in-a-haystack" with distractors.

#### Falsification criteria
If the $H_\infty$ Riccati update cannot be mathematically simplified into a diagonal-compatible group operator, the proposal falls back to $O(d^2)$ sequential recurrence and fails.

#### Research plan
- Week 1: Derive the associative operator for the diagonalized Riccati update.
- Week 2-3: Implement a fused Triton kernel for the $H_\infty$ scan.
- First deliverable: A robust linear-recurrence module with minimax optimality proofs.

#### Confidence
- Confidence: High
- What would raise confidence: A formal lemma proving the Diagonal Riccati operator satisfies the semi-group property.
- What would lower confidence: Findings that $\gamma$ tuning (performance bound) leads to gradient divergence in 7B+ models.

---

### Spinoff Proposal: HPR (Hierarchical Preconditioned Recurrence)

#### One-sentence idea
A tree-structured linear recurrence where parent nodes store second-order TTR summaries of child segments to solve $1M+$ token context decay.

#### Core novelty claim
Combines curvature-aware preconditioning (local precision) with segment-tree hierarchy (long-range memory) in a unified $O(n \log n)$ scan.

#### Seed-paper connection
- Seed mechanism/claim: Multi-head attention (Vaswani et al. 2017).
- What the seed paper does: Maintains all keys in a flat KV cache.
- What this proposal changes: Replaces global KV cache with a hierarchical "Delta-Segment-Tree" where memory is recursively compressed via associative summaries.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Curvature Neglect | DeltaNet (2026) | Establishes the need for second-order preconditioning. |
| Segment Compression | SCOUT (2025) | Demonstrates VRAM wins at $1M+$ tokens. |
| KV Cache Wall | SCBench (2024) | Proves hierarchy is a physical necessity. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Block-State Transformer | BST (2023) | Similar hierarchy. | BST uses block-attention; HPR uses preconditioned TTR summaries. |

#### Future-work/SOTA collision
*Recursive DeltaNet* preprints in late 2025/early 2026.

#### Technical mechanism
Implement a "Delta-Segment-Tree." Each 2k segment uses a DeltaNet update. Parent nodes store a low-rank curvature summary $(P_{parent} = P_{left} \oplus P_{right})$. The sum is made associative by defining the summary as the **Precision-Weighted Second Moment** of the segment gradients.

#### Minimum viable validation
- First experiment/proof/implementation: Multi-round "Needle-in-a-haystack" at $1.5M$ context length.
- Required dataset/tool/formalism: Long-Bench / SCBench.
- Success criterion: Maintaining $>90\%$ retrieval accuracy at $1M+$ tokens whereas Mamba-2 drops under $50\%$.

#### Falsification criteria
If the memory overhead of storing parent summaries exceeds the weight footprint of a 32k KV Cache, the hierarchy is as inefficient as the Transformer.

#### Research plan
- Week 1: Define the precision-weighted summary function for the segment tree.
- Week 2-3: Benchmark VRAM footprint of parent summaries at depth $d=4$.
- First deliverable: A hierarchical TTR layer with constant-memory parent nodes.

#### Confidence
- Confidence: High
- What would raise confidence: Proof that parent summary updates satisfy the semi-group property.
- What would lower confidence: Evidence that gradient decay across the tree is worse than basic recurrence decay.

---

### Spinoff Proposal: QSG (Quasiseparable Selection-Gated Hybrid)

#### One-sentence idea
A video-optimized mixer that activates sparse FlashAttention-3 only when the quasiseparable hidden-state entropy indicates a reasoning "Selection Gap."

#### Core novelty claim
Solves the "Selection Disconnect" by separating the roles of recurrent "Coverage" and dot-product "Selection" via a dynamic entropy-gate.

#### Seed-paper connection
- Seed mechanism/claim: Unified attention for all tokens.
- What the seed paper does: Treats every token with the same quadratic cost.
- What this proposal changes: Uses $O(n)$ quasiseparable mixers for $99\%$ of tokens, gating attention only where reasoning paths fork.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Selection Gap | Wang & Reid (2026) | Documents why SSMs fail at "picking" the best path. |
| Quasiseparable Mixers | Hydra (2024) | Provides efficient bidirectional non-causal mixing. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Mixture of Depths | Google (2024) | Token skipping/gating. | QSG gates *mechanism* (Attention vs SSM) rather than skipping layers. |

#### Future-work/SOTA collision
*Jamba-v2* (2026) potentially uses dynamic switching.

#### Technical mechanism
A "Selection Gate" computes the entropy $H(h_t)$ of the quasiseparable hidden state. If $H(h_t) > \tau$, a localized FlashAttention-3 window ($1,024$ tokens) is triggered to force a high-precision selection over the gathered quasiseparable features.

#### Minimum viable validation
- First experiment/proof/implementation: Pass@1 on multi-hour video reasoning benchmarks vs Pass@k.
- Required dataset/tool/formalism: Video-Long-Bench (2025).
- Success criterion: $15\%+$ gain in Pass@1 with only $<5\%$ increase in global FLOPs.

#### Falsification criteria
If entropy spikes do not correlate with reasoning selection errors (i.e., the model is "confidently wrong"), the gate is useless noise.

#### Research plan
- Week 1: Profile entropy spikes on "Tiny Recursive Reasoning" datasets.
- Week 2-3: Implement the gated FlashAttention- sub-block.
- First deliverable: A selection-aware hybrid architecture module.

#### Confidence
- Confidence: Medium-High
- What would raise confidence: Stronger correlation between $H(h_t)$ and pass@1 failures.
- What would lower confidence: High hardware latency overheads for context-switching between SSM and Attention engines.

---

### Spinoff Proposal: MoSS (Mixture of State-Sizes)

#### One-sentence idea
Avoid GPU shape-incompatibility in elastic hidden states by utilizing a mixture-of-experts (MoE) where each expert has a fixed, static, but differently-sized state ($d=64 \to d=4096$).

#### Core novelty claim
Solves the "Elastic State" hardware barrier (static kernel shapes) by routing tokens to fixed-size buckets instead of dynamically resizing a single state.

#### Seed-paper connection
- Seed mechanism/claim: Fixed $d_{model}$ for all layers/tokens.
- What the seed paper does: Every token is processed by same-sized matrices.
- What this proposal changes: Allows different tokens to utilize different recurrent memory capacities based on their retrieval complexity.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Shape Incompatibility | Critique Objections | Elastic states break GPU tiling and memory alignment. |
| Non-uniform entropy | Investigator findings | Documents that information density is non-uniform in high-res visual data. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Switch Transformer | Fedus (2021) | MoE over MLP. | MoSS applies MoE to the *hidden state size* of a recurrence, not just weights. |

#### Future-work/SOTA collision
"State-MoE" preprints in late 2025.

#### Technical mechanism
We define four MoE buckets with recurrent state sizes $d \in \{64, 256, 1024, 4096\}$. A router network assigns each token to a bucket. For example, "distractor" tokens go to $d=64$, while "needle" tokens (high associative value) go to $d=4096$. All experts within a layer use the same tiling to maintain batch efficiency.

#### Minimum viable validation
- First experiment/proof/implementation: Train a 1B model on dense-retrieval benchmarks.
- Required dataset/tool/formalism: SCBench associative recall tasks.
- Success criterion: Equal performance to a static $d=4096$ model with $50\%$ less total state-VRAM consumption.

#### Falsification criteria
If the routing overhead/expert-collapse leads to all tokens choosing $d=4096$, the model reverts to a standard SSM.

#### Research plan
- Week 1: Implement the MoSS router training loop.
- Week 2-3: Benchmark VRAM usage vs expert load-balancing.
- First deliverable: A bucketed state MoE (MoSS) layer.

#### Confidence
- Confidence: High
- What would raise confidence: Successful load balancing where $<10\%$ of tokens require the $d=4096$ expert.
- What would lower confidence: Finding that routing at each token step disrupts the associative scan kernel performance.

---

## 11. Speculative or Needs-More-Search Proposals

### Spinoff Proposal: SACP (SNR-Steered Curvature Preconditioning)

#### One-sentence idea
Dynamically modulate the preconditioning factor of a linear recurrence based on the Signal-to-Noise Ratio (SNR) of selectivity gradients.

#### Core novelty claim
Targets the "Optimization Friction" bottleneck by linking curvature-aware preconditioning to training-time gradient dynamics.

#### Seed-paper connection
- Seed mechanism/claim: Static architecture parameters.
- What the seed paper does: Attention is treated as a fixed mechanism.
- What this proposal changes: Specifically monitors training SNR to "force" second-order updates where the model is struggling to learn associations.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Optimization Friction | Okpekpe (2025) | AR failure is an optimization artifact. |
| Curvature Awareness | DeltaNet (2026) | Proves preconditioning fixes expressivity. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Sophia Optimizer | Liu et al. (2023) | Second-order optimization. | SACP is a *structural* trigger inside the layer, not a global optimizer. |

#### Future-work/SOTA collision
*Okpekpe-v2* expected to address SNR-informed training in early 2026.

#### Technical mechanism
A "Curvature Monitor" tracks the variance of selectivity gradients ($\nabla B, \nabla C$). When the SNR drops below a threshold $\beta$, the monitor increases the diagonal magnitude of the preconditioning matrix $\text{diag}(P_t)$, forcing the TTR update to incorporate higher-order information.

#### Minimum viable validation
- First experiment/proof/implementation: Training on "Shattering" tasks where baseline Mamba fails.
- Required dataset/tool/formalism: Nishi Task (2024).
- Success criterion: Successful recovery of AR performance where standard models fail.

#### Falsification criteria
If global Adam updates already implicitly stabilize the SNR of selective layers, this mechanism is redundant.

#### Research plan
- Week 1: Build the SNR monitor callback.
- Week 2-3: Conduct ablation study SACP vs Static DeltaNet.
- First deliverable: A training-stable TTR layer.

#### Confidence
- Confidence: Medium
- What would raise confidence: Correlation between low SNR and "Induction Head" failure.

---

### Spinoff Proposal: SelecLR (SNR-Based Selective Learning Rates)

#### One-sentence idea
A parameter-group-specific LR schedule that scales the selectivity matrices ($B, C, \Delta$) based on training-time gradient SNR.

#### Core novelty claim
Restores inductive bias (induction heads) through optimization modulation rather than structural mechanism changes.

#### Seed-paper connection
- Seed mechanism/claim: Unified Layer Learning Rates.
- What the seed paper does: All parameters in a layer share an LR.
- What this proposal changes: Specifically boosts LR for "selective" matrices to force associative formation.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| AR failure | Okpekpe (2025) | Proves failure is an optimization artifact. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| AdaFactor | Shazeer (2018) | Adaptive LR. | SelecLR targets the *selective core* of the SSM specifically. |

#### Future-work/SOTA collision
None known.

#### Technical mechanism
Implement the "SelecLR" callback. If SNR of $\nabla B$ is low, the LR for matrix $B$ is boosted by $2\text{-}5x$, forcing the recurrence to "latch on" to signal.

#### Minimum viable validation
Training on "distorted" AR tasks.

#### Falsification criteria
If standard adaptive optimizers (Adam) already handle this selectivity mismatch.

#### Research plan
- Week 1: Profile gradient SNR of selective matrices in Mamba.
- Week 2-3: Implement SelecLR schedule.
- First deliverable: A selective-optimization training recipe.

#### Confidence
- Confidence: Medium.

---

### Spinoff Proposal: HR-Scan (H-infinity Robust Associative Scan)

#### One-sentence idea
Formal algorithmic derivation of the $H_\infty$ minimax Riccati update as a parallel associative operator for GPU scans.

#### Core novelty claim
First hardware-aware operator that minimizes *worst-case* error relative to bounded unknown noise in an associative scan.

#### Seed-paper connection
- Seed mechanism/claim: Multi-head Interaction.
- What the seed paper does: Quadratic interaction over $N^2$.
- What this proposal changes: Replaces it with a parallel-prefix scan that has minimax guarantees.

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Kalman Scan | Luis et al. (2024) | Proves filters can be associative. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Luis et al. | Luis et al. (2024) | Foundational work. | Luis uses Kalman (L2); HR-Scan uses H-infinity (minimax). |

#### Future-work/SOTA collision
None discovered.

#### Technical mechanism
Derive an associative operator $\oplus$ for the $H_\infty$ update. Implement the performance bound $\gamma$ as a data-dependent learnable parameter in a fused Triton kernel.

#### Minimum viable validation
Proof of the semi-group property for the $H_\infty$ Riccati operator.

#### Falsification criteria
If the $H_\infty$ Riccati update is fundamentally non-associative (i.e., non-linear in a way that breaks prefix sums).

#### Research plan
- Week 1: Derive the operator $\oplus$.
- Week 2-3: Implement in Triton.
- First deliverable: A minimax-optimal scan kernel.

#### Confidence
- Confidence: Low-Medium.

---

### Spinoff Proposal: BQTL (Bidirectional Quasiseparable Temporal Latents)

#### One-sentence idea
A video diffusion mixer that slips a persistent "Identity-Latent" across quasiseparable temporal segments to ensure flicker-free consistency.

#### Core novelty claim
First video-specific mixer that uses quasiseparable structures to bridge spatial and temporal patches in a single pass.

#### Seed-paper connection
- Seed mechanism/claim: 2D self-attention.
- What the seed paper does: Processes image patches quadratically.
- What this proposal changes: Processes 3D video volumes via quasiseparable recurrence with a temporal "slip".

#### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Quasiseparable Mixers | Hydra (2024) | Proves bidirectional efficiency. |
| VRAM analysis | SCBench (2024) | Proves VRAM wall in video. |

#### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| VGamba | Haruna (2025) | Bidirectional Video SSM. | BQTL uses *quasiseparable* "slips" rather than simple scans. |

#### Future-work/SOTA collision
*Hong et al. (2025)* Diffusion SSMs.

#### Technical mechanism
Implement the sequence mixer as a Quasiseparable Matrix Mixer (QMM). Augment it with a low-rank temporal latent $Z_{temp}$ that persists across quasiseparable segments to maintain flicker-free identity.

#### Minimum viable validation
FID/FVD scores on high-res video prediction.

#### Falsification criteria
Failure to eliminate flickering relative to standard Diffusion Transformers (DiT).

#### Research plan
- Week 1: Compare BQTL slips vs VGamba scans in toy models.
- Week 2-3: Benchmark VRAM on 3D volumes.
- First deliverable: A bidirectional video QMM layer.

#### Confidence
- Confidence: Low-Medium.

---

## 12. Proposal Triage Matrix

| Proposal | Type | Novelty | Spec. | Evidence | Feas. | Value | Risk | Action |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **MOTTR** | Arch | 5 | 5 | 5 | 3 | 5 | Riccati Associativity | **Promote** |
| **HPR** | Arch | 5 | 5 | 5 | 4 | 5 | Tree Gradient Decay | **Promote** |
| **QSG** | Hybrid | 4 | 5 | 4 | 5 | 4 | Gating Signal Noise | **Promote** |
| **MoSS** | MoE | 4 | 5 | 4 | 5 | 4 | Routing Experts | **Promote** |
| **SACP** | Opt | 3 | 4 | 5 | 5 | 4 | Redundancy w/ Adam | **Speculative** |
| **SelecLR**| Opt | 3 | 4 | 4 | 5 | 3 | Already Baseline? | **Speculative** |
| **BQTL** | Video | 4 | 4 | 4 | 3 | 4 | VGamba Collision | **Speculative** |
| **HR-Scan**| Algo | 5 | 4 | 4 | 2 | 5 | Mathematical Proof | **Speculative** |

---

## 13. Evidence Quality and Novelty-Risk Assessment

*   **Reliability**: High. Uses 2025-2026 data (*DeltaNet, SCBench*).
*   **Risks**: The "Associative Scan" is the cornerstone. If the MOTTR or HR-Scan updates cannot be made diagonal/associative, they fall behind FlashAttention-3.
*   **Novelty Risk**: High for SACP/SelecLR due to potential overlap with current adaptive optimizer developments.

---

## 14. Open Questions and Recommended Next Searches

1.  **Riccati Associativity**: Can the $H_\infty$ operator be formulated as a group operation if the state is diagonal?
2.  **SACP Stability**: Does boosting preconditioning lead to gradient explosion in FP16?
3.  **HPR Crossover**: What context length $N$ makes HPR summaries outperform 32k KV Caches?
4.  **DeltaNet Triton performance**: Fused kernel benchmarks vs FlashAttention-3 on Blackwell.
5.  **VGamba vs BQTL**: Direct comparison of quasiseparable "slips" versus simple bidirectional scans.
6.  **ENTROPY Thresholds**: Identifying the $\tau$ threshold for selection errors in models $>1B$.
7.  **Expert Collapse in MoSS**: Ensuring tokens do not all route to the $d=4096$ expert.
8.  **H-infinity Gamma Tuning**: Feasibility of learning the $\gamma$ performance bound via backprop.
9.  **SNR Convergence**: Does SelecLR converge faster on Long Range Arena?
10. **Hardware Bias**: How do Blackwell tensor-cores handle the $O(d)$ quasiseparable decomposition?