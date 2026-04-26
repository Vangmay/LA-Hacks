# Proposal Families: Transformer Evolution & Optimization

This document synthesizes the raw research seeds from across the `novelty_ideation` run into concrete, evidence-grounded proposal families. These families group spinoff ideas by their underlying research tensions: **Architectural Efficiency**, **Structural Inductive Bias**, and **Reasoning Faithfulness**.

---

## Family 1: Hybrid Dynamics & Adaptive Scaling
*Focus: Resolving the $O(L^2)$ complexity vs. high-precision reasoning tension by moving from static/interleaved architectures to dynamic, content-aware hybridization.*

### Proposal 1.1: Continuous/Soft Hybridization of Transformers and SSMs
- **Core Novelty Claim**: Replaces discrete "expert routing" (MambaFormer) or static interleaving (Jamba) with a differentiable, token-wise weighted combination of attention and state-space modules.
- **Evidence Basis**: Zero results found for "soft routing" or "continuous blending" in recent Transformer-Mamba literature; current SOTA (MambaFormer) is limited to hard, discrete token-level switching.
- **Mechanism**: A sigmoid-gated residual connection where a lightweight gating head $\sigma(g(x_t))$ computes continuous weights for a weighted sum: $y_t = \alpha_t \cdot \text{Attn}(x_t) + (1-\alpha_t) \cdot \text{SSM}(x_t, h_{t-1})$.
- **Prior-Work Collision**: *MambaFormer* (uses hard, discrete routing); *Jamba* (uses static, interleaved blocks).
- **Validation Path**: Compare against Jamba and MambaFormer on **LongBench**; measure the efficiency-accuracy Pareto frontier (FLOPs vs. Perplexity).
- **Falsification**: The gating mechanism adds $O(n)$ overhead that negates SSM efficiency, or "soft" mixtures cause unstable training gradients.
- **Confidence**: High (Gap confirmed by zero-result search).

### Proposal 1.2: Attentional State-Updating Reservoir (ASUR)
- **Core Novelty Claim**: Uses attentional mechanisms to actively "sculpt" the internal manifold of a reservoir, rather than just interpreting it at the readout.
- **Evidence Basis**: Current RC-NLP (Köster & Uchida, 2025) only applies attention to *readouts*. Maslennikov (2026) proves sculpted dynamics are essential for RNN efficiency.
- **Mechanism**: A gated recurrent update: $h_t = \text{tanh}(W_{res}h_{t-1} + \text{Attention}(x_t, h_{t-1}))$, where Attention operates on a fixed-size latent representation to maintain $O(L)$ complexity.
- **Prior-Work Collision**: *Echo State Networks* (passive dynamics); *Köster & Uchida* (readout-only).
- **Validation Path**: Perplexity vs. Latency benchmark on **WikiText-103** against standard ESNs and Transformers.
- **Falsification**: The attentional gate increases complexity back toward $O(n^2)$ or causes vanishing gradients in the reservoir manifold.
- **Confidence**: Medium (Requires distinguishing from emerging Structured SSMs).

### Proposal 1.3: Dynamic Attention-SSM Hybridization via Information Density Gating
- **Core Novelty Claim**: Uses information density (entropy) to route tokens between Attention (high-entropy/salient) and SSM (low-entropy/context) kernels.
- **Evidence Basis**: The tension between $O(N^2)$ retrieval (Transformers) and $O(N)$ compression (SSMs) is established (VL-Mamba, 2024), but content-dependent kernel switching is underexplored.
- **Mechanism**: A lightweight entropy estimator $E(x_t)$ acts as a router: if $E(x_t) > \tau$, use Attention; else, use SSM.
- **Prior-Work Collision**: *Jamba* (static); *Mixture-of-Experts* (routes to experts, not fundamental computational kernels).
- **Validation Path**: **Needle-in-a-Haystack** and **LRA** benchmarks to prove retention of "perfect memory" with near-SSM scaling.
- **Falsification**: Gating overhead exceeds SSM efficiency gains, or the gate fails to differentiate "key" vs "context" tokens.
- **Confidence**: High.

---

## Family 2: Structural Inductive Bias & Stable Sparsity
*Focus: Moving from "topology-blind" self-attention to learned, stable structural constraints to improve efficiency without falling into the "routing absorption" trap.*

### Proposal 2.1: Stable Entropy-Gated Topology-Kernel Routing (SEG-TKR)
- **Core Novelty Claim**: Combines stable, layer-wise topology discovery with dynamic, entropy-based kernel switching to avoid "Routing Absorption."
- **Evidence Basis**: Failure of per-query gating due to co-adaptation (09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a) and the success of hierarchical/coarse-to-fine scaling.
- **Mechanism**: 1. **Coarse Topology Stage**: Predicts a stable, block-wise adjacency matrix. 2. **Entropy Gate**: Estimates information density per block. 3. **Kernel Dispatch**: Selects kernel (SSM vs Attn) based on density within the stable topology.
- **Prior-Work Collision**: *Jamba* (static); *Sparsifiner* (per-query instability).
- **Validation Path**: Compare against Jamba on **LongBench** and **LRA**, measuring FLOPs vs. Retrieval Accuracy.
- **Falsification**: The entropy gate's overhead exceeds $O(N)$ savings, or the "stable" topology still collapses to a sliding window.
- **Confidence**: Medium-High.

### Proposal 2.2: Decoupled Topology Learning for Transformers
- **Core Novelty Claim**: Learns a stable, layer-wise/block-wise structural mask (topology) that is decoupled from fine-grained Q/K/V projections to prevent routing absorption.
- **Evidence Basis**: "Routing Absorption" proves end-to-end per-query gating is ineffective; hierarchical/coarse-to-fine methods (VSA, RocketKV) provide a path to stability.
- **Mechanism**: A two-stage module: (1) A "Coarse Topology Predictor" (operating on pooled features) outputs a sparse adjacency matrix. (2) "Fine-Grained Attention" uses this stable mask as a structural constraint.
- **Prior-Work Collision**: *Graphormer* (fixed graphs); *Sparsifiner* (per-query gating); *SVOO* (training-free profiling).
- **Validation Path**: Comparative study on **dependency parsing** or **hierarchical classification**; measure convergence rate vs. vanilla Transformers.
- **Falsification**: The topology becomes too coarse for dependencies, or the Predictor becomes a bottleneck.
- **Confidence**: Medium.

---

## Family 3: Reasoning Faithfulness & Alignment
*Focus: Resolving the "over-correction" in error recovery and the "post-hoc rationalization" in CoT by introducing training-time consistency constraints.*

### Proposal 3.1: Constrained Policy Optimization for Balanced Error Recovery
- **Core Novelty Claim**: Resolves the exposure bias "over-correction" problem by using a Lagrangian-constrained framework that treats semantic fidelity as a hard constraint.
- **Evidence Basis**: The documented tension where error-recovery objectives cause semantic drift (He et al., 2024).
- **Mechanism**: $\max \text{Reward}$ subject to $\text{KL}(\text{Model} || \text{GroundTruth}) < \epsilon$, using a Lagrangian-constrained policy gradient.
- **Prior-Work Collision**: *DPO/CPL* (implicit preference modeling rather than explicit constraints).
- **Validation Path**: Compare vanilla RL-tuned vs. Constrained RL on **NMT**; measure Reward (ROUGE) vs. Fidelity (BERTScore).
- **Falsification**: The constraint $\epsilon$ is too restrictive to allow error recovery, or the Lagrangian is too unstable for LLMs.
- **Confidence**: Medium.

### Proposal 3.2: Consistency-Optimized Structural-Hybrid Training (CO-SHT)
- **Core Novelty Claim**: Uses multi-stage, process-based consistency rewards during RL to ensure hybrid architectural choices (Attn vs. SSM) align with the logical reasoning trace.
- **Evidence Basis**: Emergence of unfaithfulness during training (60bf56ed72d032600f01161fd40769273bef84a8) and the utility of multi-dimensional rewards (VERITAS).
- **Mechanism**: $R = R_{outcome} + \lambda R_{structural\_consistency}$, where $R_{structural\_consistency}$ measures the causal impact of a selected kernel/topology on the reasoning step's validity.
- **Prior-Work Collision**: *VERITAS/ReFIne* (RAG-specific or general trustworthiness, not structural alignment).
- **Validation Path**: Train on **modular arithmetic**; measure reduction in the "transient unfaithfulness phase" compared to standard SFT/RLHF.
- **Falsification**: The consistency reward is too sparse for convergence or too expensive for scaling.
- **Confidence**: Medium.