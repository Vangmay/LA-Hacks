# Proposal Families: Transformer Architectural Evolution & Optimization

This document synthesizes raw research seeds into concrete, evidence-grounded proposal candidates. The proposals are grouped into three distinct families based on their fundamental research direction: **Adaptive Computational Complexity**, **Structural & Geometric Inductive Biases**, and **Mechanistic Reliability & Expressiveness**.

---

## Family 1: Adaptive Computational Complexity
*Focus: Moving beyond static architectures toward real-time, intelligence-aware modulation of precision, rank, and algorithmic kernels.*

### Proposal Candidate: Entropy-Driven Dynamic Rank and Precision (ED-DRP)
- **Merged Idea**: A unified inference-time control loop that uses the Shannon entropy of attention maps as a real-time signal to simultaneously modulate both low-rank approximations (rank $r$) and quantization bit-width ($b$) for attention components.
- **Core Novelty Claim**: Unlike static joint optimization (MLoRQ) or single-dimension adaptive methods (TALE), ED-DRP implements a dynamic, intelligence-aware compression framework that scales complexity based on the instantaneous informational density of the input.
- **Evidence Basis**: 
    - **Gap**: Lack of a unified mechanism using entropy for *joint* (rank + precision) modulation (Subagent 02).
    - **Support**: Maisonnave (2025) quantifies redundancy via entropy; TALE (2025) validates adaptive rank; MLoRQ (2025) validates joint optimization.
- **Prior-work Collision**: 
    - **MLoRQ (2025)**: Performs joint optimization but is static/pre-planned, lacking a real-time entropy signal.
    - **TALE (2025)**: Adaptive rank but lacks precision/bit-width modulation.
- **Mechanism**: A lightweight entropy estimator (operating on a subset of attention heads) that maps to a discrete lookup table of $(r, b)$ pairs, adjusting $Q, K, V$ projection rank and KV cache precision on-the-fly.
- **Validation**: Implement on Llama-3-8B; compare accuracy/latency/memory against MLoRQ and TALE across varying sequence lengths and informational densities.
- **Falsification**: If entropy does not correlate with the optimal $(r, b)$ pair, or if the entropy estimation latency exceeds the computational savings.
- **Confidence**: **High** (Strong theoretical bridge between information theory and existing adaptive rank/precision work).
- **Decision**: `promote`

### Proposal Candidate: Mixture of Attention Algorithms (MoAA)
- **Merged Idea**: A routing mechanism that selects the specific *computational kernel* (e.g., Full Self-Attention, Windowed/Flash-Attention, or Linear Attention) per block or per layer based on sequence context.
- **Core Novelty Claim**: Shifts the paradigm from selecting *subsets* of attention (heads/tokens) to selecting the *algorithmic implementation* (kernel) to balance precision and latency.
- **Evidence Basis**: 
    - **Gap**: Current MoE/Sparse research focuses on *what* is attended to, not *how* it is computed (Subagent 01).
    - **Support**: ASSENet (2024) demonstrates routing between local/non-local mechanisms in speech.
- **Prior-work Collision**: 
    - **MoA (2022) / MoSA (2025)**: Focus only on head/token selection, not algorithmic complexity.
    - **ASSENet (2024)**: Uses mechanism routing but in a specialized speech context.
- **Mechanism**: A lightweight gating network that predicts the optimal attention kernel (Full vs. Windowed vs. Linear) per layer/block to optimize the FLOPs-to-accuracy tradeoff.
- **Validation**: Benchmark on Long Range Arena (LRA) comparing latency/accuracy against static windowed and full attention.
- **Falsification**: If the overhead of the router and the latency of kernel-switching (launch overhead) exceeds the computational savings of the sparse kernel.
- **Collision Risk**: **High** (Hardware/Triton kernel launch latency).
- **Confidence**: **Medium** (Requires validation of kernel-switching overhead).
- **Decision**: `speculative`

---

## Family 2: Structural & Geometric Inductive Biases
*Focus: Addressing the tension between global modeling and local inductive bias through structural anchoring and frequency-domain gating.*

### Proposal Candidate: Latent Coordinate Anchors (LCA)
- **Merged Idea**: A proactive structural mechanism that introduces a dedicated, learnable coordinate manifold (Anchor Module) to serve as a stable reference frame, replacing the reactive absorption of attention sinks.
- **Core Novelty Claim**: Moves from *reactive* token-based sink absorption (Registers) to *proactive* structural anchoring through a dedicated coordinate manifold.
- **Evidence Basis**: 
    - **Gap**: Tension between sinks as geometric necessity (Ruscio, 2025) vs. computational artifact (Darcet, 2023).
    - **Support**: Failure of unanchored ViTs to maintain clean attention maps.
- **Prior-work Collision**: 
    - **Registers (Darcet, 2023)**: Reactive (extra tokens to absorb energy); LCA is proactive/structural.
    - **VAR (Visual Attention Redistribution)**: Closest semantic match.
- **Mechanism**: A parallel "Anchor Module" containing learnable parameter vectors that serve as a stable, explicit coordinate manifold, queried via constrained cross-attention or gating to stabilize representational spaces.
- **Validation**: Compare attention map energy distribution and smoothness in LCA vs. Register-ViT; evaluate on dense visual tasks (segmentation/depth).
- **Falsification**: If LCA fails to improve training stability or attention map cleanliness compared to standard Registers.
- **Confidence**: **Medium** (Strong geometric motivation, but architectural complexity risk).
- **Decision**: `promote`

### Proposal Candidate: Gated Local-Global Attention (GLGA)
- **Merged Idea**: A structural, intra-block mechanism that uses a convolutional sparsity mask generator to dynamically gate between local and global attention weights.
- **Core Novelty Claim**: Transitions from *score-based* sparsity (thresholding scores) to *topological* sparsity (predicting a structural mask via convolution).
- **Evidence Basis**: 
    - **Gap**: Distinction between score-based sparsity and structural topology prediction (Subagent 01).
    - **Support**: Hybrid architectures (CNN-Transformer) are common, but use convolution to *augment* rather than *route* attention.
- **Prior-work Collision**: 
    - **Dynamic Sparse Mask (2025)**: Uses percentile/score thresholding (score-based).
    - **GCAT (2025)**: Uses gated conv-attention for feature enhancement, not sparsity routing.
- **Mechanism**: A lightweight convolutional sparsity mask generator that outputs a sparse topology matrix, used to index/route the attention computation.
- **Validation**: Training throughput and perplexity on Long Range Arena (LRA) compared to Sparse Transformers.
- **Falsification**: If the overhead of the convolutional mask generator exceeds the FLOP savings.
- **Collision Risk**: **Medium** (Learning structured sparsity).
- **Confidence**: **Medium** (Requires collision search for 'learned structured sparsity').
- **Decision**: `speculative`

---

## Family 3: Mechanistic Reliability & Expressiveness
*Focus: Repairing mathematical failures of efficient models and using attention dynamics as a diagnostic for reliability.*

### Proposal Candidate: Injective-Local Linear Attention (IL-LA)
- **Merged Idea**: A dual-stream attention mechanism that repairs the mathematical failures of linear attention (lack of injectivity and local modeling) by hybridizing a global injective kernel with a high-precision local stream.
- **Core Novelty Claim**: Specifically targets the *structural repair* of linear approximations by using a local stream to compensate for the global injective kernel's lack of "sharpness."
- **Evidence Basis**: 
    - **Gap**: The mathematical failure of linear attention regarding injectivity and local modeling (Subagent 03).
    - **Support**: Bridging the Divide (2024).
- **Prior-work Collision**: 
    - **LaplacianFormer (2026)**: Addresses injectivity via a Laplacian kernel, but lacks the explicit local-global structural repair.
    - **Hybrid-ViTs**: Use hybrid patterns for standard Softmax, not to fix linear approximations.
- **Mechanism**: Dual-stream: 1) Global stream using a non-monotonic, injective kernel (e.g., Laplacian); 2) Local stream using a sharp, high-precision mechanism (e.g., sliding-window convolution).
- **Validation**: Compare against vanilla Linear Attention and Softmax Attention on tasks requiring both long-range context and high local precision (e.g., high-res segmentation).
- **Falsification**: If the dual-stream approach fails to outperform the complexity-to-accuracy ratio of pure Softmax or pure LaplacianFormer.
- **Confidence**: **Medium** (High novelty, but implementation/complexity risk).
- **Decision**: `promote`

### Proposal Candidate: Attention Stability Diagnostic (ASD)
- **Merged Idea**: A real-time reliability metric that uses the variance/fluctuation of attention weights under domain-specific perturbations (noise) to monitor model trustworthiness in safety-critical environments.
- **Core Novelty Claim**: Moves from using attention for *interpretability* (importance) or *training* (entropy) to using attention *variance* as a *deployment-time diagnostic* for failure detection.
- **Evidence Basis**: 
    - **Gap**: Lack of real-time diagnostic metrics for deployment in noisy, safety-critical environments (Subagent 03).
    - **Support**: Mondal & Jagtap (2026) on structural vulnerabilities.
- **Prior-work Collision**: 
    - **XAI (Agarwal, 2024)**: Focuses on word *importance* (interpretability).
    - **Training Stability (Zhai, 2023)**: Uses entropy to prevent collapse during *training*.
- **Mechanism**: A diagnostic score $\text{ASD} = \text{Var}(\text{AttentionWeights} | \delta)$, where $\delta$ is a controlled domain-specific noise model (e.g., sensor jitter).
- **Validation**: Apply to MultiScaleSleepNet (2025) using Sleep-EDF datasets; correlate ASD decay with task-specific F1 score decay under noise.
- **Falsification**: If performance drops significantly while the ASD remains high (suggesting failure is in FFNs/Embeddings).
- **Confidence**: **Medium** (High novelty/value in safety-critical fields; requires validation of correlation).
- **Decision**: `promote`