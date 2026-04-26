# Cross-Investigator Deep Dive: Sub-Quadratic Transitions & Structural Integrity

## 1. Cross-Investigator Comparative Analysis

The three investigators converge on a central crisis: the departure from the Transformer's $O(N^2)$ global attention (Vaswani, 2017) introduces vulnerabilities that were inherently protected by the quadratic baseline.

### 1.1 Repeated Evidence & Global Anchors
*   **Seed Foundation:** All investigators utilize **Vaswani et al. (2017)** as the complexity and structural baseline.
*   **The 2024 Reasoning Trap:** Both `investigator_03` (Dynamic/Sparse) and `investigator_01` (Recurrence) rely on **Yang et al. (2024)** ("Do Efficient Transformers Really Save Computation?") to argue that sub-quadratic scaling often necessitates an "efficiency tax" in reasoning depth.
*   **Redundancy Benchmark:** `investigator_02` and `investigator_03` both reference **Michel et al. (2019)** to justify architectural pruning, though they derive different Spinoffs (one focuses on rank-adaptive projections, the other on semantic hubs).

### 1.2 Contradictions & Conflict Zones
*   **Stability vs. Pruning:** `investigator_01` identifies a "Stability Gap" where input-driven recurrences are fragile. Conversely, `investigator_02` identifies "Intra-Module Slack" and advocates for rank reduction. **The Contradiction:** Reducing rank/complexity (per `investigator_02`) may exacerbate the spectral instabilities and "Memory Collapse" identified by `investigator_01` (Bonetto, 2026).
*   **Mechanism Execution:** `investigator_02` proposes learned locality masks (Saliency Gates). However, `investigator_03` highlights via **SADIMM (2025)** that such semantic/token-based pruning disrupts GPU load balancing. A "novel" structural gate from `investigator_02` might be hardware-obsolete upon arrival if it ignores the dimension-parallel dataflow requirements of `investigator_03`.

### 1.3 Synthesized Research Gaps
1.  **The Non-Autonomous Stability-Reasoning Nexus:** We lack a framework proving that Lyapunov-stable recurrences (`inv_01`) provide the necessary tree-path connectivity for multi-hop logic (`inv_03`).
2.  **Geometric Rank-Awareness:** While spectral attention handles SO(3) symmetry (`inv_02`), it does not dynamically adjust its projection rank based on the manifold curvature, leading to wasted compute in "flat" regions of the data manifold.

---

## 2. Spinoff Proposal Candidates

### Proposal Candidate 1: Lyapunov-Stabilized Semantic Hubs (LSSH)
*   **Source Proposal Seeds:** `subagent_01` (Lyapunov-Stable Recurrence), `subagent_02` (SOHRA).
*   **Merged Idea:** A linear-complexity attention mechanism where tokens are clustered into latent "hubs" whose temporal evolution is constrained by a differentiable Lyapunov barrier function to prevent reasoning collapse.
*   **Core Novelty Claim:** First architecture to solve the hardware load-imbalance of dynamic hubs while simultaneously providing formal stability guarantees for non-autonomous sequence tracking.
*   **Evidence Basis:** *SADIMM* (2025) hardware constraints + *LrcSSM* (2025) Jacobian stability + *ReHub* (2024) clustering.
*   **Mechanism:**
    1.  **Dimension-Parallel Hashing:** Discrete semantic hub assignment following the SADIMM dataflow to ensure GPU SM occupancy.
    2.  **Lyapunov Projection:** The transition matrix $A$ between temporal hub states is projected onto a contraction mapping manifold using the Small-Gain Theorem.
*   **Validation:** Benchmark on 'Chain-of-Thought as DP' (Yang 2024) vs. Mamba-3 and FlashAttention.
*   **Falsification:** If hub-stabilization prevents the learning of "unstable" high-order logic (e.g., chaotic state transitions required for specific algorithmic tasks).
*   **Confidence:** High.
*   **Decision:** **Promote** (Strongest synthesis of theory and hardware).

### Proposal Candidate 2: Curvature-Adaptive Rank Projections (CARP)
*   **Source Proposal Seeds:** `investigator_02` (RAAP), `investigator_02` (ISA-RM).
*   **Merged Idea:** An attention mechanism that adjusts the rank of $W_q, W_k, W_v$ projections based on the intrinsic Laplace-Beltrami curvature of the input manifold.
*   **Core Novelty Claim:** Moves beyond fixed-rank pruning to "Geometric Rank Discovery," where the architecture allocates more expressive power (rank) to regions of high high-frequency spectral components (curvature).
*   **Evidence Basis:** *TransAct* (2024) intra-module redundancy + *An et al.* (2025) spectral attention.
*   **Mechanism:** Compute the Laplace-Beltrami eigenfunctions of the input mesh/sequence. Use a "Curvature Gate" (SVD-based) to increase the rank of the projection matrices when the local spectral entropy exceeds a threshold.
*   **Validation:** 3D Shape Matching (FAUST) and Facial Expression Recognition (FER) where local "Action Units" represent high-curvature features.
*   **Falsification:** If a fixed low-rank model with higher hidden dimension outperforms CARP at the same parameter count, proving rank-adaptation is sub-optimal compared to width.
*   **Confidence:** Medium-High.
*   **Decision:** **Promote**.

### Proposal Candidate 3: Spectral-Gated Reasoning Testbed (RDST-v2)
*   **Source Proposal Seeds:** `investigator_03` (RDST), `investigator_01` (SpectralGuard).
*   **Merged Idea:** A diagnostic suite that correlates the "logical failure point" of a model with its spectral radius shrinkage during long-context traversal.
*   **Core Novelty Claim:** The first benchmark to treat "model reasoning" as a dynamical system stability problem rather than just a token-matching problem.
*   **Evidence Basis:** *Bonetto (2026)* spectral poisoning + *Yang (2024)* reasoning logic failures.
*   **Mechanism:** Synthetically generate multi-hop logic tasks (e.g., Longest Common Subsequence). Instrument the model to output its internal transition operator eigenvalues at each reasoning node.
*   **Validation:** Profile 10+ models (Mamba, GLA, BigBird); show that $N_{fail}$ (reasoning breakdown) is predicted by the spectral radius $\rho$ hitting a critical threshold.
*   **Falsification:** If reasoning fails while the spectral radius remains stable (indicating failures in weight semantics rather than dynamical stability).
*   **Confidence:** High.
*   **Decision:** **Promote**.

---

## 3. Rejected or Weak Ideas

*   **Recurrence-Augmented Attention Sharpening (RAAS):** Rejected as **weak/speculative**. Overlaps heavily with existing "Gated Linear Attention" (GLA) without providing a unique technical differentiator. Falsification risk is too high (simple masking is easier).
*   **Identifying Discrete Recurrence Limits (Capacity Gaps):** Rejected as **speculative**. While theoretically interesting, the "hard" thresholds are likely invisible in practical FP16/BF16 training, making the "Sentinel" limit difficult to validate empirically.
*   **Dynamic Relative-Distance Biases:** Rejected as **done**. Mechanisms like ALiBi and RoPE already saturate this space; the proposal lacked a specific "Structural Audit" mechanism to differentiate it from basic gated biases.

---

## 4. Novelty Risk & Global Score Rubric

| Proposal | Novelty (1-5) | Technical Spec. (1-5) | Evidence Support (1-5) | Feasibility (1-5) | Research Value (1-5) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LSSH** | 5 | 4 | 5 | 3 | 5 |
| **CARP** | 4 | 4 | 4 | 3 | 4 |
| **RDST-v2**| 3 | 5 | 5 | 5 | 4 |

**Global Novelty Risk:** The primary risk is the **"Linearity Lie"** (identified by investigator_03). Mathematically $O(N)$ mechanisms often have constant factors or memory-bandwidth bottlenecks that make them slower than $O(N^2)$ FlashAttention in reality. Any proposal (especially LSSH) must survive a CUDA-level kernel benchmark against FlashAttention-v3.

---

## 5. Missing Evidence & Recommended Adversarial Searches

*   **Adversarial Search 1:** "Dimension-parallel SVD-gating in Triton/CUDA" (To check if Proposal 1 or 2 hit a hardware dead-end in current kernel libraries).
*   **Adversarial Search 2:** "Laplace-Beltrami eigenfunctions for sequence modeling" (To verify if Proposal 2's spectral mechanism has been applied to NLP or if it is restricted to 3D geometry).
*   **Adversarial Search 3:** "Stability-constrained MoEExpert routing" (Check for 2025/2026 pre-prints on Lyapunov functions in MoE).