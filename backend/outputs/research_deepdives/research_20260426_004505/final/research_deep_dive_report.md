# Research Deep Dive: Transformer Architectural Evolution & Optimization

## 1. Executive Summary

This research deep dive investigates the evolutionary trajectory of the Transformer architecture, moving from the foundational $O(n^2)$ self-attention paradigm to the current frontier of efficiency-oriented, structured, and geometrically-aware models. 

The investigation identifies a **tripartite tension** defining the current research frontier:
1.  **Complexity vs. Context:** The struggle to bridge the gap between $O(n)$ complexity (SSMs/Linear Attention) and the "sharpness" (injectivity) and bidirectional context required for high-fidelity language modeling.
2.  **Structure vs. Sparsity:** A shift from *score-based* sparsity (thresholding high-attention weights) toward *structural* sparsity (predicting topology via convolutional masks) and *geometric* stability (addressing "attention sinks" as reference frame needs).
3.  **Adaptive Intelligence vs. Static Efficiency:** Moving from static compression/routing toward "intelligence-aware" mechanisms that use real-time signals (e.g., Shannon entropy) to modulate rank and precision.

The investigation culminates in 8 concrete research spinoff proposals. High-confidence directions include **Entropy-Driven Dynamic Rank and Precision (ED-DRP)**, **Latent Coordinate Anchors (LCA)**, and **Injective-Local Linear Attention (IL-LA)**. These target the most significant unresolved gaps: the unified optimization of rank and precision, the proactive management of geometric sinks, and the mathematical repair of expressiveness lost in linear approximations.

---

## 2. Seed Paper Metadata

- **Title:** Attention is All You Need
- **Authors:** Vaswani et al.
- **Year:** 2017
- **Paper ID:** [ARXIV:1706.03762](https://arxiv.org/abs/1706.03762)
- **Venue:** NeurIPS
- **TLDR:** Introduced the Transformer architecture, replacing recurrence and convolutions with a pure self-attention mechanism.
- **Foundational Bottleneck:** The $O(n^2)$ quadratic scaling of self-attention relative to sequence length.

---

## 3. Literature Map by Bucket

| Bucket | Key Papers / Evidence | Core Contribution |
| :--- | :--- | :--- |
| **Foundational** | Shazeer et al. (2017) [MoE] | Established conditional computation/MoE. |
| **Closest Prior** | MoA (2022); MoSA (2025) | Head-level and token-level routing. |
| **Direct Follow-ups** | DeepSeek-V2 (2024) [MLA] | KV compression via multi-head latent attention. |
| **Recent SOTA** | Mamba/S6 (2023/24); Vision Mamba (2024) | Linear-time $O(n)$ State-Space Models. |
| **Critiques/Gaps** | Bridging the Divide (2024); Ruscio (2025) | Expressiveness/injectivity gaps; Sink geometry. |
| **Efficiency/Sparsity**| TALE (2025); MLoRQ (2025) | Adaptive rank and joint quantization. |
| **Hybrid/Specialized**| MTMixer (2025); ASSENet (2024) | Interleaving SSMs and Transformers. |

---

## 4. Closest Prior Work

| Paper | Year | Relationship to Seed/Proposals | Key Differentiator |
| :--- | :--- | :--- | :--- |
| **MoA (Mixture of Attention)** | 2022 | Direct collision for head-level routing. | Selects *subsets* of heads; does not select *algorithms*. |
| **MoSA (Expert-Choice)** | 2025 | Direct collision for token-level routing. | Selects *tokens*; does not optimize *complexity*. |
| **Registers (Darcet et al.)** | 2023 | Direct collision for attention sink management. | *Reactive* (adds tokens to absorb noise); LCA is *proactive*. |
| **LaplacianFormer** | 2026 | Direct collision for injective linear attention. | Focuses on *global* kernel injectivity; IL-LA adds *local* repair. |

---

## 5. Direct Follow-ups and Recent State of the Field

The field has moved from **Architectural Replacement** (replacing RNNs with Transformers) to **Structural Refinement** (Sparsity/MoE) and is currently entering the era of **Mathematical Repair** (fixing the information-theoretic failures of linear attention). 

The most significant recent shift is the emergence of **State-Space Models (SSMs)** like Mamba, which provide $O(n)$ scaling but introduce a new "expressiveness gap" regarding local modeling and bidirectional context. Simultaneously, the "Attention Sink" phenomenon has transitioned from a perceived training artifact to a recognized geometric necessity for high-dimensional reference frames.

---

## 6. Critiques, Limitations, Reproductions, and Benchmark Evidence

### 6.1 The "Hardware-Complexity Paradox"
A systemic critique across all investigators is the **Observer's Paradox**: mechanisms designed for efficiency (gating, entropy estimation, sparsity prediction) introduce their own $O(n)$ or $O(n \log n)$ overhead. If the controller's complexity is not strictly lower than the bottleneck it solves, the net gain is negative.

### 6.2 The "Sink" Contradiction
There is an unresolved tension in the literature regarding the nature of attention sinks:
- **View A (Geometric):** Sinks are necessary coordinate manifolds (Ruscio, 2025).
- **View B (Semantic/Artifact):** Sinks are "lazy aggregation" shortcuts or training artifacts (Shi, 2026; Darcet, 2023).
*This contradiction dictates whether the solution must be structural (LCA) or reactive (Registers).*

### 6.3 The "Injectivity" Failure
Linear attention approximations (Performer, Linformer) suffer from a lack of **injectivity**, where distinct queries map to identical outputs, causing semantic collapse. This is the primary driver for the "Mathematical Repair" research frontier.

---

## 7. Novelty Comparison Table

| Proposal | Seed Connection | Closest Prior | Novelty Claim | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| **ED-DRP** | Entropy-driven efficiency | MLoRQ / TALE | Real-time joint (Rank + Precision) modulation via entropy. | **High** |
| **LCA** | Sink phenomenon | Registers | Proactive manifold vs. reactive token absorption. | **High** |
| **IL-LA** | Linear attention gap | LaplacianFormer | Dual-stream (Global Injective + Local High-Precision). | **High** |
| **MoAA** | MoE scaling | ASSENet | Routing between *algorithms* (kernels) vs *heads*. | **Medium** |
| **GLGA** | Structural sparsity | Dynamic Sparse Mask | Topological (conv-mask) vs score-based sparsity. | **Medium** |
| **Non-Causal SSM**| SSM lineage | VSSD | Single-pass non-causal mechanism for LLMs. | **Medium** |
| **ASR** | Stability/Variance | Zhai (2023) | Using weight variance as a deployment-time diagnostic. | **Medium** |
| **SFGA** | Frequency-awareness | FANet | Intra-block structural frequency-domain gating. | **Medium** |

---

## 8. Research-Gap Candidates

1.  **Unified Dynamic Complexity Control:** A mechanism that simultaneously optimizes rank and precision using a single information-theoretic signal.
2.  **Non-Causal Single-Pass SSMs:** Efficient bidirectional context for LLM prefix-modeling without the $2\times$ overhead of dual-pass scanning.
3.  **Structural Intra-Block Gating:** Moving from decision-layer gating to mechanism-level routing within a single Transformer block.
4.  **Deployment-Time Reliability Diagnostics:** Using attention weight variance as a real-time sensor for model trustworthiness in noisy environments.

---

## 9. Proposal Seed Inventory and Rejected Weak Ideas

### Rejected or Weak Ideas
- **Automated Circuit Discovery for Transformer Scaling:** Rejected as highly speculative; existing mechanistic interpretability (TransformerLens) lacks the scaling/automation path required.
- **Linear-Complexity Attention Scaling (Generic):** Rejected as too broad; likely to collide with existing efficient attention research.
- **Structurally-Constrained Self-Attention:** Rejected as insufficiently targeted; lacks a clear mathematical objective compared to the IL-LA proposal.

---

## 10. High-Confidence Spinoff Proposals

## Spinoff Proposal: Entropy-Driven Dynamic Rank and Precision (ED-DRP)

### One-sentence idea
A unified inference-time control loop that uses Shannon entropy to simultaneously modulate low-rank approximation (rank $r$) and quantization bit-width ($b$).

### Core novelty claim
Unlike static joint optimization (MLoRQ) or single-dimension adaptive methods (TALE), ED-DRP implements an intelligence-aware compression framework that scales complexity based on the instantaneous informational density of the input.

### Seed-paper connection
- **Seed mechanism/claim:** Transformer overparameterization and information-theoretic efficiency.
- **What the seed paper does:** Established the $O(n^2)$ scaling bottleneck.
- **What this proposal changes:** Uses real-time entropy as the modulator for both rank and precision, rather than static pre-planning.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Entropy as redundancy proxy | Maisonnave (2025) | Provides the theoretical basis for entropy as a signal. |
| Adaptive rank validation | TALE (2025) | Proves rank-adaptivity works for KV cache. |
| Joint optimization feasibility| MLoRQ (2025) | Validates that rank and precision can be optimized together. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Static joint optimization | MLoRQ (2025) | Performs joint optimization. | MLoRQ is static; ED-DRP is dynamic/entropy-driven. |
| Adaptive rank-only | TALE (2025) | Validates adaptive rank. | TALE lacks the precision/bit-width modulation component. |

### Future-work/SOTA collision
Real-time hardware-aware dynamic scaling frameworks.

### Technical mechanism
A lightweight entropy estimator operating on a subset of attention heads that maps to a discrete lookup table of $(r, b)$ pairs, adjusting $Q, K, V$ projection rank and KV cache precision on-the-fly.

### Minimum viable validation
- **First experiment/proof/implementation:** Implement on Llama-3-8B.
- **Required dataset/tool/formalism:** Compare accuracy/latency/memory against MLoRQ and TALE.
- **Success criterion:** Significant reduction in FLOPs/memory with minimal perplexity degradation across varying sequence lengths.

### Falsification criteria
If entropy does not correlate with the optimal $(r, b)$ pair, or if the entropy estimation latency exceeds the computational savings.

### Research plan
- **Week 1:** Implement lightweight entropy estimator on subset of heads.
- **Week 2-3:** Develop lookup table for $(r, b)$ pairs via offline profiling.
- **First deliverable:** Accuracy/Latency/Memory benchmark report on Llama-3.

### Expected contribution type
System/Architecture (Inference Optimization).

### Confidence
- **Confidence:** high
- **What would raise confidence:** Empirical correlation proof between entropy and quantization error.
- **What would lower confidence:** High entropy correlates with rank complexity but not necessarily bit-width requirement.

---

## Spinoff Proposal: Latent Coordinate Anchors (LCA)

### One-sentence idea
A proactive structural mechanism that introduces a dedicated, learnable coordinate manifold to serve as a stable reference frame, replacing reactive attention sinks.

### Core novelty claim
Moves from *reactive* token-based sink absorption (Registers) to *proactive* structural anchoring via a dedicated coordinate manifold.

### Seed-paper connection
- **Seed mechanism/claim:** Attention sink phenomenon and $O(n^2)$ scaling.
- **What the seed paper does:** Established the foundational attention mechanism.
- **What this proposal changes:** Replaces the "absorption" of sink energy with "anchoring" via a parallel manifold.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Sinks as geometric necessity | Ruscio (2025) | Provides the structural motivation for an "anchor." |
| Failure of unanchored ViTs | Darcet (2023) | Shows why current models need "registers." |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Reactive absorption | Darcet (2023) [Registers] | Uses extra tokens for sinks. | LCA is structural/parameter-based, not token-based. |

### Future-work/SOTA collision
Continuous state context in SSMs.

### Technical mechanism
A parallel "Anchor Module" containing learnable parameter vectors that serve as a stable, explicit coordinate manifold, queried via constrained cross-attention or gating to stabilize representational spaces.

### Minimum viable validation
- **First experiment/proof/implementation:** Compare attention map energy distribution and smoothness in LCA vs. Register-ViT.
- **Required dataset/tool/formalism:** Evaluate on dense visual tasks (segmentation/depth).
- **Success criterion:** Improved training stability and smoother attention maps compared to standard Register-ViT.

### Falsification criteria
If LCA fails to improve training stability or attention map cleanliness compared to standard Registers.

### Research plan
- **Week 1:** Design Anchor Module parameterization.
- **Week 2-3:** Integrate into ViT/Transformer and train.
- **First deliverable:** Qualitative/Quantitative comparison of attention smoothness.

### Expected contribution type
Architecture (Structural Inductive Bias).

### Confidence
- **Confidence:** high
- **What would raise confidence:** Demonstrating LCA requires significantly fewer parameters than large Register sets.
- **What would lower confidence:** High architectural complexity leading to instability.

---

## Spinoff Proposal: Injective-Local Linear Attention (IL-LA)

### One-sentence idea
A dual-stream attention mechanism that repairs the mathematical failures of linear attention (injectivity and local modeling) by hybridizing a global injective kernel with a high-precision local stream.

### Core novelty claim
Specifically targets the *structural repair* of linear approximations by using a local stream to compensate for the global injective kernel's lack of "sharpness."

### Seed-paper connection
- **Seed mechanism/claim:** Linear complexity (SSM/Linear Attention).
- **What the seed paper does:** Established the baseline for attention.
- **What this proposal changes:** Adds a dual-stream structure to fix the "injectivity/local modeling" failures of linear models.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Expressiveness gap in linear attention | Bridging the Divide (2024) | Identifies the lack of injectivity/local modeling. |
| Laplacian kernel for injectivity | LaplacianFormer (2026) | Provides a candidate for the global stream. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Global injectivity fix | LaplacianFormer (2026) | Uses a Laplacian kernel. | IL-LA adds the *local* stream for structural repair. |

### Future-work/SOTA collision
Hybrid SSM-Transformer architectures.

### Technical mechanism
Dual-stream: 1) Global stream using a non-monotonic, injective kernel (e.g., Laplacian); 2) Local stream using a sharp, high-precision mechanism (e.g., sliding-window convolution).

### Minimum viable validation
- **First experiment/proof/implementation:** Compare against vanilla Linear Attention and Softmax Attention.
- **Required dataset/tool/formalism:** Tasks requiring both long-range context and high local precision (e.g., high-res segmentation).
- **Success criterion:** Superior complexity-to-accuracy ratio compared to pure Softmax or pure LaplacianFormer.

### Falsification criteria
If the dual-stream approach fails to outperform the complexity-to-accuracy ratio of pure Softmax or pure LaplacianFormer.

### Research plan
- **Week 1:** Formulate injective kernel selection.
- **Week 2-3:** Design the local stream integration/gating.
- **First deliverable:** Implementation of the dual-stream kernel.

### Expected contribution type
Mathematical/Algorithm (Approximation Repair).

### Confidence
- **Confidence:** high
- **What would raise confidence:** Mathematical proof of injectivity restoration.
- **What would lower confidence:** High implementation/complexity overhead.

---

## 11. Speculative or Needs-More-Search Proposals

## Spinoff Proposal: Mixture of Attention Algorithms (MoAA)

### One-sentence idea
A routing mechanism that selects the specific computational kernel (e.g., Full Self-Attention, Windowed/Flash-Attention, or Linear Attention) per block or per layer based on sequence context.

### Core novelty claim
Shifts the paradigm from selecting *subsets* of attention (heads/tokens) to selecting the *algorithmic implementation* (kernel) to balance precision and latency.

### Seed-paper connection
- **Seed mechanism/claim:** MoE/Conditional computation.
- **What the seed paper does:** Established parameter-based routing.
- **What this proposal changes:** Routes *algorithms* (kernels) instead of *experts* (weights).

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Mechanism routing in speech | ASSENet (2024) | Demonstrates viability of mechanism selection. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Token/Head selection | MoA/MoSA | Focus only on subsets. | MoAA selects the mathematical implementation. |

### Future-work/SOTA collision
Hardware-aware dynamic kernels.

### Technical mechanism
A lightweight gating network that predicts the optimal attention kernel (Full vs. Windowed vs. Linear) per layer/block. To minimize dispatch latency, the router operates at the block-level using Triton kernels for efficient switching.

### Minimum viable validation
- **First experiment/proof/implementation:** Benchmark on Long Range Arena (LRA).
- **Required dataset/tool/formalism:** Compare latency/accuracy against static windowed and full attention.
- **Success criterion:** Measurable latency reduction without loss in LRA scores.

### Falsification criteria
If the overhead of the router and the latency of kernel-switching (launch overhead) exceeds the computational savings of the sparse kernel.

### Research plan
- **Week 1:** Define the kernel-selection gating architecture.
- **Week 2-3:** Develop Triton kernels for efficient switching.
- **First deliverable:** Latency/Accuracy benchmark report.

### Expected contribution type
System/Architecture (Dynamic Routing).

### Confidence
- **Confidence:** medium
- **What would raise confidence:** Profiling data showing low Triton dispatch overhead.
- **What would lower confidence:** High kernel-launch latency on standard GPUs.

---

## Spinoff Proposal: Gated Local-Global Attention (GLGA)

### One-sentence idea
A structural, intra-block mechanism that uses a convolutional sparsity mask generator to dynamically gate between local and global attention weights.

### Core novelty claim
Transitions from *score-based* sparsity (thresholding scores) to *topological* sparsity (predicting a structural mask via convolution).

### Seed-paper connection
- **Seed mechanism/claim:** Structural sparsity / Parallelization via CNNs.
- **What the seed paper does:** Introduced the foundational $O(n^2)$ bottleneck.
- **What this proposal changes:** Uses a convolutional layer to control the attention topology rather than just augmenting features.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Distinction between score/structural | Subagent 01 | Identifies the gap in current sparsity research. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Dynamic Sparse Mask | 2025 | Uses percentile/score thresholding. | GLGA uses topological mask prediction. |

### Future-work/SOTA collision
Learned structured sparsity.

### Technical mechanism
A lightweight convolutional sparsity mask generator that outputs a sparse topology matrix $M$, used to index/route the attention computation: $\text{Attn}(Q, K, V) = \text{Softmax}(Q(K \odot M)^T)V$.

### Minimum viable validation
- **First experiment/proof/implementation:** Training throughput and perplexity on Long Range Arena (LRA) compared to Sparse Transformers.
- **Required dataset/tool/formalism:** LRA benchmark.
- **Success criterion:** Training throughput and perplexity improvement over score-based sparse transformers.

### Falsification criteria
If the overhead of the convolutional mask generator exceeds the FLOP savings from the sparse attention mechanism.

### Research plan
- **Week 1:** Design convolutional mask generator.
- **Week 2-3:** Implement sparse indexing in Triton.
- **First deliverable:** Throughput/Accuracy benchmark.

### Expected contribution type
Architecture (Structural Sparsity).

### Confidence
- **Confidence:** medium
- **What would raise confidence:** Proven lower overhead compared to thresholding.
- **What would lower confidence:** High mask-generation latency.

---

## Spinoff Proposal: Single-Pass Non-Causal SSM for Prefix-LM

### One-sentence idea
Achieving bidirectional/non-causal context in a single scan, optimized for the specific prefix-dependency patterns of LLMs.

### Core novelty claim
Moving from multi-scan/dual-pass bidirectional SSMs (which double overhead) to a single-pass non-causal SSM mechanism specifically designed for the prefix-dependency patterns of LLM pre-training.

### Seed-paper connection
- **Seed mechanism/claim:** SSM/Mamba lineage.
- **What the seed paper does:** Established causal SSMs.
- **What this proposal changes:** Moves from dual-pass (bidirectional) to single-pass non-causal kernel.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Prefix-LM effectiveness | RedLLM (2025) | Validates the non-causal paradigm for LLMs. |
| Non-causal SSM in vision | VSSD (2024) | Proves non-causality is possible via SSD modification. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Vision-centric non-causality | VSSD (2024) | Non-causal SSM for vision. | Novelty is in the 1D language/prefix mechanism. |

### Future-work/SOTA collision
General-purpose non-causal SSM architectures for NLP.

### Technical mechanism
A modified State-Space Duality (SSD) kernel that incorporates a non-causal mechanism (e.g., asymmetric state update) within a single-pass scan: $\mathbf{h}_t = \mathbf{A}(\tau) \mathbf{h}_{t-1} + \mathbf{B}(\tau) \mathbf{x}_t$, where $\mathbf{A}(\tau)$ is a function of a look-ahead window $\tau$.

### Minimum viable validation
- **First experiment/proof/implementation:** Perplexity, throughput, and memory efficiency on prefix-completion tasks.
- **Required dataset/tool/formalism:** Prefix-LM tasks.
- **Success criterion:** Competitive perplexity with significantly higher throughput/lower memory than dual-pass Mamba.

### Falsification criteria
If the single-pass mechanism fails to capture context as effectively as dual-pass SSMs or standard attention-based prefix-LMs.

### Research plan
- **Week 1:** Mathematical formulation of the asymmetric state update.
- **Week 2-3:** Implementation of the single-scan kernel.
- **First deliverable:** Perplexity/Throughput benchmark.

### Expected contribution type
Algorithm/Mathematical (Non-Causal Kernel).

### Confidence
- **Confidence:** medium
- **What would raise confidence:** Proof of single-scan bidirectional capacity.
- **What would lower confidence:** Mathematical impossibility of achieving non-causality in one pass without $O(n^2)$.

---

## Spinoff Proposal: Attention Stability Regularization (ASR)

### One-sentence idea
A training-time regularization term that penalizes excessive variance in attention weights under controlled environmental perturbations to ensure deployment reliability.

### Core novelty claim
Moves from using attention for *interpretability* (importance) or *training* (entropy) to using attention *variance* as a *deployment-time diagnostic and regularization tool*.

### Seed-paper connection
- **Seed mechanism/claim:** Transformer structural vulnerabilities in safety-critical domains.
- **What the seed paper does:** Identifies reliability/trustworthiness gaps in medical/robotic applications.
- **What this proposal changes:** Transforms a diagnostic "observation" into a training-time "regularization objective."

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Structural vulnerabilities | Mondal & Jagtap (2026) | Provides the high-level motivation for reliability. |
| Entropy for stability | Zhai et al. (2023) | Baseline for entropy-based stability. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| XAI/Importance | Agarwal (2024) | Focuses on word importance. | ASR focuses on weight *variance* and stability. |

### Future-work/SOTA collision
Safe-by-design architectures.

### Technical mechanism
A training-time regularization term $\mathcal{L}_{stab} = \text{Var}(\text{Softmax}(QK^T/\sqrt{d}) | \delta)$ that penalizes excessive variance in attention weights when subjected to domain-specific noise $\delta$ (e.g., sensor jitter).

### Minimum viable validation
- **First experiment/proof/implementation:** Apply to MultiScaleSleepNet (2025) using Sleep-EDF datasets.
- **Required dataset/tool/formalism:** EEG datasets + noise injection.
- **Success criterion:** Correlate ASR score decay with task-specific F1 score decay under noise.

### Falsification criteria
If performance drops significantly while the ASR remains high (suggesting failure is in FFNs/Embeddings).

### Research plan
- **Week 1:** Define domain-specific noise models $\delta$.
- **Week 2-3:** Implement ASR loss and train on EEG tasks.
- **First deliverable:** Correlation analysis of ASR vs. F1.

### Expected contribution type
Algorithm/Training (Reliability/Robustness).

### Confidence
- **Confidence:** medium
- **What would raise confidence:** Empirical correlation proof between stability and error.
- **What would lower confidence:** High entropy correlates with rank complexity but not necessarily bit-width requirement.

---

## Spinoff Proposal: Structural Frequency-Gated Attention (SFGA)

### One-sentence idea
A structural, intra-block mechanism that uses a lightweight spectral-complexity probe to dynamically gate between local and global attention weights.

### Core novelty claim
Transitions from *score-based* sparsity (thresholding scores) to *topological* sparsity (predicting a structural mask via convolution).

### Seed-paper connection
- **Seed mechanism/claim:** Local-global scale-specific features.
- **What the seed paper does:** Identified the need for local-global bridging.
- **What this proposal changes:** Implements this bridging as a single-stream gated mechanism rather than parallel branches.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Local-global gap | Swin (2025) | Identifies limitations in scale-specific modeling. |
| Frequency-aware modules | FANet (2025) | Shows frequency-awareness is a viable augmentation. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Decision-layer gating | PlgFormer (2025) | Uses gating for feature fusion. | SFGA operates intra-block for attention weights. |

### Future-work/SOTA collision
Unified scale-aware models.

### Technical mechanism
A gating mask $G$ derived from a local DCT-based spectral probe that modulates the attention matrix: $A_{final} = (1 - G) \odot A_{local} + G \odot A_{global}$.

### Minimum viable validation
- **First experiment/proof/implementation:** Benchmark on NYU Depth V2 or KITTI depth completion.
- **Required dataset/tool/formalism:** Dense prediction datasets.
- **Success criterion:** Improved spatial precision over standard Swin/ViT.

### Falsification criteria
If the spectral probe/gating mechanism increases latency significantly without improving spatial precision over standard Swin/ViT.

### Research plan
- **Week 1:** Design lightweight DCT-based probe.
- **Week 2-3:** Integrate into Transformer block.
- **First deliverable:** Spatial precision/latency benchmark.

### Expected contribution type
Architecture (Structural Inductive Bias).

### Confidence
- **Confidence:** medium
- **What would raise confidence:** Low DCT overhead in hardware.
- **What would lower confidence:** High latency of intra-block spectral probing.

---

## 12. Proposal Triage Matrix

| Proposal | Type | Novelty score | Specificity score | Evidence score | Feasibility score | Research-value score | Biggest collision risk | Recommended action |
|---|---|---:|---:|---:|---:|---:|---|---|
| **ED-DRP** | Adaptive | 5 | 5 | 5 | 5 | 5 | MLoRQ (Static vs Dynamic) | **Promote** |
| **LCA** | Structural | 4 | 4 | 4 | 4 | 5 | Registers (Reactive vs Proactive) | **Promote** |
| **IL-LA** | Mathematical | 4 | 5 | 4 | 3 | 5 | LaplacianFormer (Kernel vs Hybrid) | **Promote** |
| **MoAA** | Adaptive | 3 | 4 | 3 | 2 | 4 | Kernel Launch Overhead | **Speculative** |
| **GLGA** | Structural | 3 | 4 | 3 | 3 | 3 | Learned Structured Sparsity | **Speculative** |
| **Non-Causal SSM**| Mathematical | 5 | 2 | 3 | 2 | 5 | VSSD (Vision focus) | **Speculative** |
| **ASR** | Training | 3 | 2 | 3 | 4 | 3 | Attribution Error (is it FFN?) | **Speculative** |
| **SFGA** | Structural | 3 | 4 | 3 | 3 | 3 | DCT Overhead | **Speculative** |

---

## 13. Evidence Quality and Novelty-Risk Assessment

### 13.1 Evidence Quality
- **High Quality:** The evidence for the "Expressiveness Gap" in linear attention and the "Sink Phenomenon" is highly robust, supported by both mathematical theory (Laplacian, statistical mechanics) and empirical observations (Registers, ViT failures).
- **Medium Quality:** The link between Shannon entropy and the optimal $(rank, precision)$ pair is theoretically sound but requires targeted empirical validation to ensure entropy maps to both parameters effectively.

### 13.2 Novelty-Risk Assessment
- **Primary Risk: The Efficiency Paradox.** Every proposed mechanism (gating, entropy estimation, sparsity prediction) introduces a "control tax." If the controller's $O(f(n))$ complexity is not strictly lower than the savings of the sparse/low-rank kernel, the net gain is negative.
- **Secondary Risk: Hardware Alignment.** Modern performance is driven by optimized, static kernels (FlashAttention). Breaking these static execution paths for dynamic/custom kernels (MoAA, GLGA) risks significant "dispatch latency" penalties.

---

## 14. Open Questions and Recommended Next Searches

### 14.1 Open Questions
1.  **Complexity Budget:** What is the formal complexity bound for a "lightweight" entropy estimator or gating network that ensures a net FLOP reduction?
2.  **Kernel Dispatch Latency:** How much latency is introduced when switching between Triton-optimized kernels (e.g., FlashAttention $\to$ Linear) on modern GPUs?
3.  **Attribution:** Can we rigorously decouple the contribution of the attention mechanism to model robustness from the contributions of the LayerNorm/Residual stream?
4.  **Entropy-Precision Link:** Does high attention entropy specifically necessitate higher bit-width (precision), or does it merely imply higher rank complexity?
5.  **Mathematical Feasibility:** Can a single-pass non-causal kernel be implemented without re-introducing quadratic-like dependencies?
6.  **Complexity of DCT:** How does the computational cost of intra-block DCT-based probing compare to the benefits of frequency-domain gating?
7.  **Sink/Semantic Conflict:** How does the choice of a structural (LCA) vs semantic (SFGA) solution resolve the "Sink Contradiction"?
8.  **Injectivity vs Locality:** Does the dual-stream approach of IL-LA actually solve the local-modeling gap, or is it just an additional parameter overhead?
9.  **Router Complexity:** Can a router for MoAA be made $O(1)$ relative to sequence length through block-level grouping?
10. **Reliability Correlation:** To what extent does attention weight variance correlate with end-to-end loss in safety-critical domains?

### 14.2 Recommended Next Searches
- **System-Level:** `"Triton kernel launch overhead" AND "dynamic sparsity"`
- **Information Theory:** `"correlation between attention entropy and quantization error in Transformers"`
- **Mathematical:** `"single-pass bidirectional state space model kernel" AND "non-causal"`
- **Structural:** `"learned structured sparsity transformer" AND "convolutional topology prediction"`