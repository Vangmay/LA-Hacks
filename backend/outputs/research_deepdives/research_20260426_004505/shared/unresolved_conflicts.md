# Unresolved Conflicts

This document outlines the technical contradictions, evidentiary weaknesses, and literature gaps identified during the synthesis of Transformer scaling, sparsity, and structural mechanics. These conflicts must be resolved before any proposal can be promoted from `speculative` to `high-confidence`.

## 1. Technical Contradictions

### 1.1. Efficiency vs. Control Overhead (The "Tax" Problem)
Across all proposed mechanisms (MoAA, ED-DRP, GLGA, SFGA), there is a recurring tension between the computational savings of the mechanism and the FLOPs/latency required to implement the controller.
- **The Conflict**: A gating network for kernel selection (MoAA) or an entropy estimator for rank/precision (ED-DRP) adds overhead. If the router/estimator's complexity is $O(n)$ or $O(n \log n)$, it may negate the savings of the $O(n)$ or $O(\sqrt{n})$ sparse/low-rank kernel it selects.
- **Missing Evidence**: Exact characterization of the "break-even point" where the overhead of dynamic routing (especially in Triton/CUDA kernel-switching) exceeds the savings of a sparse kernel.

### 1.2. Sink Interpretations: Geometric Necessity vs. Computational Artifact
There is a fundamental disagreement in the literature regarding the nature of "Attention Sinks."
- **The Conflict**: 
    - **View A (Geometric/Structural)**: Sinks are a fundamental requirement for establishing stable coordinate manifolds/reference frames in high-dimensional space (Ruscio et al., 2025). *Implication: We need proactive structural anchors (LCA).*
    - **View B (Artifact/Heuristic)**: Sinks are byproduct artifacts of training dynamics or "lazy aggregation" of background noise (Shi et al., 2026). *Implication: We need reactive absorption (Registers).*
- **Impact on Novelty**: If the sink is a semantic shortcut, architectural "anchors" (LCA) may fail to generalize. If the sink is geometric, "registers" are merely a suboptimal patch.

### 1.3. SSM Bidirectionality: Multi-Scan vs. Single-Pass
The path to non-causal SSMs for LLMs is bifurcated by a trade-off in complexity.
- **The Conflict**: Existing bidirectional SSMs (Vision Mamba, Dual-path Mamba) primarily use multi-scan/dual-pass strategies, which effectively doubles the constant factor of the $O(n)$ complexity. A single-pass mechanism (Proposed) is theoretically superior but mathematically difficult to implement without re-introducing quadratic-like dependencies.
- **Unresolved Question**: Can a single-pass kernel (like VSSD) capture the semantic precision required for 1D language sequences, or is the "second pass" necessary for the complex long-range dependencies found in text?

## 2. Evidentiary Weaknesses

### 2.1. Entropy Correlation Gap
The viability of the **ED-DRP** proposal rests on the assumption that Shannon entropy of the attention map is a high-fidelity proxy for the optimal $(rank, precision)$ pair.
- **The Gap**: While entropy correlates with redundancy (Maisonnave, 2025), it is unproven whether high entropy in an attention map specifically necessitates high-rank *and* high-precision. High entropy might simply indicate high complexity (rank) without requiring higher bit-width (precision).
- **Required Search**: "Correlation between attention map entropy and quantization error in Transformers."

### 2.2. Domain Transferability of Robustness
Much of the evidence for "intrinsic denoising" or "stability" comes from specialized, high-SNR or highly structured domains (EEG, medical signals, vision).
- **The Gap**: It is unclear if the "denoising paths" identified in statistical mechanics (Tiberi, 2024) manifest in the same way in the discrete, symbolic, and highly structured semantic space of Natural Language Processing (NLP).
- **Risk**: A diagnostic metric (ASD) optimized for physiological noise may be entirely irrelevant for the linguistic perturbations (typos, syntactic shifts) encountered in LLMs.

## 3. Missing Literature Buckets & Failed Searches

### 3.1. Hardware-Aware Kernel Switching
- **Status**: **Critical Gap**.
- **Problem**: Most novelty in sparsity/routing assumes infinite-speed kernel switching.
- **Missing Search**: "GPU kernel launch latency for non-standard attention kernels (Triton/CUDA)" and "hardware-aware dynamic sparsity in Transformers."

### 3.2. Learned Structural Sparsity
- **Status**: **High Collision Risk**.
- **Problem**: The distinction between "score-based sparsity" (thresholding) and "topological sparsity" (predicting structure) is thin.
- **Missing Search**: "learned structured sparsity transformer" and "convolutional attention topology prediction."

## 4. Exact Follow-up Search Protocol

To resolve these conflicts, the following searches are mandated before promoting candidates:

| Target Conflict | Search Query | Goal |
| :--- | :--- | :--- |
| **Overhead Tax** | `"Triton kernel launch overhead" AND "dynamic sparsity"` | Quantify the latency cost of switching kernels. |
| **Entropy/Precision** | `"attention entropy" AND "quantization error" AND "rank-precision"` | Validate the entropy-driven control signal. |
| **SSM Non-Causality** | `"single-pass bidirectional state space model" AND "language"` | Confirm if a language-specific non-causal kernel exists. |
| **Structural Sparsity**| `"learned structural sparsity" AND "transformer topology"` | Perform an adversarial collision check for GLGA. |
| **Reliability Proxy**| `"attention weight variance" AND "model uncertainty" AND "robustness"` | Test if ASD is a valid reliability metric. |