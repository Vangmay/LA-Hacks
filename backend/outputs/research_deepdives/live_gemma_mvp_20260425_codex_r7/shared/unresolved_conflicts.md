# Unresolved Conflicts

This artifact documents the contradictions, evidence gaps, and research uncertainties identified during the `novelty_ideation` run. These conflicts represent high-value research entry points where current literature either contradicts itself or lacks sufficient detail to support confident architectural or algorithmic claims.

## 1. Architectural Mechanism Conflicts

### 1.1 The "Routing vs. Interleaving" Paradigm Tension
*   **Conflict**: There is a fundamental tension between **Static Interleaving** (e.g., *Jamba*, 2024) and **Dynamic/Content-Aware Routing** (e.g., *MambaFormer*, 2026).
*   **Details**: Current SOTA hybrids like *Jamba* rely on fixed, structural interleaving of Transformer and SSM layers. Conversely, *MambaFormer* proposes token-level routing. However, the "Routing Absorption" phenomenon (09346bf8, 2026) suggests that end-to-end learned per-query gating often collapses, making it no better than random selection.
*   **Unresolved Question**: Can a hybrid architecture achieve content-aware efficiency without falling into the "Routing Absorption" trap? Is the solution a middle ground (e.g., block-wise/layer-wise stable topology) or a different mathematical framework entirely?
*   **Impact on Proposals**: This directly challenges the feasibility of both the *Continuous Hybridization* and *SEG-TKR* proposals.

### 1.2 Readout-based vs. State-based Attentional Memory
*   **Conflict**: Current Reservoir Computing (RC) in NLP focuses on using attention for **readout-only** adaptation (Köster & Uchida, 2025), whereas dynamical systems theory suggests that efficiency requires **internal state sculpting** (Maslennikov, 2026).
*   **Details**: Using attention to interpret a reservoir's state is a well-trodden path. However, using attention to *evolve* the reservoir manifold (attentional sculpting) is a distinct, underexplored mechanism.
*   **Unresolved Question**: Does using attention to modulate the internal state update $h_t$ re-introduce the $O(L^2)$ complexity bottleneck, or can it be maintained at $O(L)$?
*   **Impact on Proposals**: This is the primary pivot for the *ASUR* (Attentional State-Updating Reservoir) proposal.

---

## 2. Training-Inference & Optimization Conflicts

### 2.1 The Fidelity-Recovery Trade-off (Exposure Bias)
*   **Conflict**: Efforts to mitigate exposure bias through Reinforcement Learning (RL) or Contrastive Learning often lead to **"Over-correction"** (He et al., 2024).
*   **Details**: Models optimized for error recovery (robustness) tend to deviate from the ground-truth semantic distribution (fidelity). There is a documented tension where aggressive recovery leads to "unnatural" or semantically drifted sequences.
*   **Unresolved Question**: Can we formulate a dual-objective optimization (e.g., Lagrangian-constrained) that treats semantic fidelity as a hard constraint while maximizing sequence-level rewards?
*   **Impact on Proposals**: Motivates the *Constrained Policy Optimization (CO-SHT)* proposal.

### 2.2 Emergent Unfaithfulness vs. Post-hoc Rationalization
*   **Conflict**: There is a debate whether Chain-of-Thought (CoT) unfaithfulness is a **prompting/inference issue** or a **training-emergent property** (Wang et al., 2026).
*   **Details**: While many interpretability studies treat unfaithfulness as a post-hoc rationalization (models lying to fit a bias), recent evidence suggests that unfaithful reasoning patterns emerge naturally during the autoregressive training process.
*   **Unresolved Question**: If unfaithfulness is an emergent property of training, can it be solved through post-hoc detection, or do we require new training-time objectives (e.g., consistency rewards)?
*   **Impact on Proposals**: Drives the *CO-SHT* and *Consistency-Optimized Training* directions.

---

## 3. Evidence Gaps & Missing Literature

### 3.1 The "Black Box" of SOTA Hybrid Fusion
*   **Gap**: The exact fusion mechanism of *NVIDIA Nemotron Nano 2* (2025) remains undisclosed.
*   **Missing Search**: A detailed architectural breakdown is needed to determine if it utilizes **interleaving** (static), **parallel/hierarchical fusion** (structural), or **token-routing** (dynamic).
*   **Risk**: If *Nemotron Nano 2* already implements a successful hierarchical fusion, the *Hierarchical NLP Hybrid* proposal may be obsolete.

### 3.2 The "Learnability" vs. "Computability" Disconnect
*   **Gap**: While Transformers are proven to be able to compute symbolic programs (computability), there is insufficient literature quantifying the **gradient-driven learnability** of these programs (the "grokking" difficulty).
*   **Missing Search**: Systematic benchmarks correlating symbolic program complexity (recursion depth, branching factor) with the efficacy of gradient signals in Transformer training.
*   **Impact on Proposals**: This gap is the foundation for the *Bridging Computability-Learnability* proposal.

### 3.3 Hardware-Level Routing Latency
*   **Gap**: Theoretical efficiency gains in "soft-routing" or "kernel-switching" (Transformer $\leftrightarrow$ SSM) are unverified against real-world hardware constraints.
*   **Missing Search**: Profiling the latency and memory-movement overhead of switching between distinct kernels (Self-Attention vs. SSM/Mamba) within a single GPU kernel.
*   **Risk**: High-level algorithmic novelty might be negated by low-level memory-bandwidth bottlenecks.

---

## 4. Summary of Required Follow-up Searches

| Target Area | Search Query / Objective | Goal |
| :--- | :--- | :--- |
| **Architectural Collision** | `exact phrase search: "differentiable surprisal gating linear attention"` | Verify DITA novelty. |
| **Architectural Collision** | `architecture breakdown: "NVIDIA Nemotron Nano 2"` | Check Hierarchical Hybrid collision. |
| **Hardware Feasibility** | `latency: "switching between attention and SSM kernels" GPU` | Validate Soft-Switching feasibility. |
| **Mathematical Stability** | `stability analysis: "attentional recurrent state updates" Jacobian` | Validate ASUR stability. |
| **Algorithm Collision** | `exact phrase: "Lagrangian constrained reinforcement learning sequence generation"` | Verify Constrained Policy novelty. |