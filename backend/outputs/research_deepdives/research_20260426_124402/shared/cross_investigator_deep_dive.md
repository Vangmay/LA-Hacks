# Cross-Investigator Deep Dive: Sub-Quadratic Architectures and Inductive Bias Restoration

## 1. Synthesis Overview

This deep dive integrates two distinct but converging lines of investigation: **Investigator 01's** focus on the efficiency-accuracy trade-offs (addressability vs. scaling) and **Investigator 02's** focus on mathematical lineage (inductive bias restoration). 

The global synthesis reveals a critical "Addressability-Extrapolation Conflict": 
1. Sub-quadratic models (SSMs/Linear Attention) fail at high-precision retrieval (**Huang 2024**) because they lack the "pointer" capability of the KV-cache.
2. The KV-cache's primary tool for navigation—Positional Encoding (RoPE)—is the primary barrier to context extrapolation (**Zhang 2025/LEDiT**) because explicit coordinates become Out-of-Distribution (OOD) at scale.

**Shared Technical Baseline:**
- **Seed Paper:** Vaswani et al. (2017) discarded recurrence and convolution, creating the gaps that both investigators are now attempting to fill.
- **Collision Risk:** **Schlag (2021)** and **Yeh (2022)** demonstrate that the "novelty" of current efficiency and equivariance efforts often maps back to 1990s Fast Weights (Schmidhuber) and classical Toeplitz/LTI filter theory.

---

## 2. Spinoff Proposal Candidates

### Proposal Candidate: Spectral State-Space Retrieval (S3R)

- **Source proposal seeds:** `Addressable State-Space Retrieval (ASSR)` (Inv 01) + `Spectral Deconfliction of Positional Bias (SD-PB)` (Inv 02).
- **Merged idea:** A hybrid architecture that restores precise "Needle-in-a-Haystack" (NIAH) retrieval to SSMs by combining quantized latent-state checkpointing with a frequency-split positional system.
- **Core novelty claim:** Decouples retrieval addressability from coordinate scaling. It uses "High-Pass RoPE" for local syntax and "Addressable Latent Checkpoints" for global retrieval, preventing state-decay while bypassing the RoPE extrapolation wall.
- **Evidence basis:** 
    - **Huang (2024)**: SSMs fail NIAH due to loss of addressability.
    - **Zhang (2025)**: Explicit PE (RoPE) is the barrier to length scaling.
- **Mechanism:** 
    1. An SSM (Mamba-style) processes the sequence. 
    2. At high-entropy transitions, the latent state is pushed to a k-NN index. 
    3. The query uses **High-Pass RoPE** (zeroing out low frequencies) to identify local context, then uses a **Cross-Attention layer** to retrieve from the latent-state index. Global position is inferred via the causal mask predecessor count rather than RoPE coordinates.
- **Validation:** 128k context NIAH task using Mamba-2.8B as base. Compare against standard Mamba and RoPE-scaled Transformers.
- **Falsification:** If state retrieval fails even with frequency-split coordinates, the bottleneck is "Projection Loss" during the SSM's initial encoding phase, not storage decay.
- **Confidence:** High.
- **Decision:** **Promote**.

---

### Proposal Candidate: Toeplitz-Constrained Graph Attention (TC-GA)

- **Source proposal seeds:** `Differentiable HNSW Attention` (Inv 01) + `Toeplitz-Structured Positional Bias` (Inv 02).
- **Merged idea:** Replaces the $O(N^2)$ attention matrix with a differentiable Hierarchical Navigable Small World (HNSW) graph search where edge formation is strictly governed by a Toeplitz (shift-invariant) kernel.
- **Core novelty claim:** Synergizes $O(N \log N)$ scaling with a hard-baked translation equivariance constraint. This prevents the model from learning position-dependent biases that break during sequence length extension.
- **Evidence basis:** 
    - **Lee (2024/HiP)**: $O(T \log T)$ is possible via locality-biased pruning.
    - **Yeh (2022)**: Equivariance can be discovered through Toeplitz parameter sharing.
- **Mechanism:** During graph construction (KV-cache indexing), the edge probability $P(i,j)$ is conditioned on a learned Toeplitz bias $B_{i,j} = \mathcal{T}(i-j)$. Gradients flow through the Gumbel-Softmax selected edges of the HNSW graph. This ensures the search structure itself adheres to classical signal processing LTI (Linear Time-Invariant) properties.
- **Validation:** Parity test with CNNs on "bit-string pattern shifts" and performance on Long Range Arena (LRA).
- **Falsification:** If the computational overhead of maintaining a differentiable graph exceeds $O(N^2)$ for $N < 32k$, the implementation is non-viable.
- **Confidence:** Medium (High implementation risk).
- **Decision:** **Speculative**.

---

### Proposal Candidate: Delta-Rule Triton (DRT) Kernels

- **Source proposal seeds:** `Hardware-Aware Kernel Refactor of 1990s Fast Weights` (Inv 01).
- **Merged idea:** Resurrecting the 1992 "Delta Rule" for associative memory as a fused Triton scan, specifically designed to address the memory-capacity wall in Linear Transformers.
- **Core novelty claim:** Translates theoretical associative memory density gains (from the 90s) into modern hardware-aware performance, outperforming "Selective Scan" (Mamba) on tasks requiring multi-step retrieval.
- **Evidence basis:** 
    - **Schlag (2021)**: Linear Transformers are mathematically equivalent to Fast Weight Programmers.
    - **Schmidhuber (1992)**: Identified the "Delta Rule" as superior to additive updates for memory capacity.
- **Mechanism:** Implements the $W_{t} = W_{t-1} + \eta (v_t - W_{t-1} k_t) \otimes k_t$ update as a fused CUDA kernel. This "error-correcting" update allows for higher density of information storage in the linear state compared to standard Linear Attention.
- **Validation:** Compare perplexity/retrieval accuracy against RWKV-6 and Mamba-2 on LongBench.
- **Falsification:** If the sequential nature of the Delta Rule update (which is harder to parallelize than additive scans) cannot be masked by Triton tiling, it will be too slow for training.
- **Confidence:** Medium-High.
- **Decision:** **Promote**.

---

## 3. Global Novelty-Risk Matrix

| Proposal | Primary Seed | Theoretical Risk | Collision Risk (Pre-2017) | SOTA Collision (Post-2022) |
| :--- | :--- | :--- | :--- | :--- |
| **S3R** | Vaswani 2017 | State-Entropy stability | RNN Hidden States | Mamba-2 / Jamba |
| **TC-GA** | Lee 2024 / Yeh 2022 | Graph gradient variance | HNSW / Locality Sensitive Hashing | H2O (Heuristic Pruning) |
| **DRT Kernels** | Schlag 2021 | Sequential scan latency | Fast Weight Programmers (1992) | RWKV / Mamba-2 |

## 4. Contradictions & Missing Evidence

1.  **The "Locality" Paradox:** Investigator 01's Finding (HiP 2024) assumes attention is naturally local. Investigator 02's Finding (LEDiT 2025) suggests RoPE *forces* this locality and causes failure at scale. If we remove RoPE, does the "Locality Trap" in sub-quadratic models disappear, or does the model lose the ability to resolve local syntax entirely?
2.  **Implicit Signal Resolution:** Both investigators mention "Implicit Position" from the causal mask (Haviv 2022, LEDiT 2025). However, there is no evidence that this signal has the **high-frequency resolution** required for tasks like code-compilation or chemical structure parsing.
3.  **Missing Evaluation:** Neither investigator found comprehensive benchmarks comparing **"PE-free SSMs"** vs. **"RoPE-augmented SSMs"** on logic-heavy tasks.

## 5. Recommended Adversarial Search

- **Query:** "Can causal mask implicit positional signals resolve high-frequency syntax (parsing/code)?"
- **Query:** "Hardware-fused Delta Rule scan vs Selective Scan performance."
- **Focus:** Identify if the "Spectral Deconfliction" idea (High-Pass RoPE) has already been attempted in the "Linear RoPE" or "YaRN" literature under a different name (e.g., "band-pass filtering attention").

---

## 6. Novelty Score Rubric (Top Candidate: S3R)

- **Novelty:** 5/5 (Unique intersection of state-space storage and spectral PE pruning).
- **Technical specificity:** 4/5 (Specific mechanism for frequency-split gating and k-NN state-checkpointing).
- **Evidence support:** 5/5 (Grounded in documented failures of SSMs [Huang 2024] and RoPE [Zhang 2025]).
- **Feasibility:** 3/5 (Requires complex Triton development for state-retrieval latency).
- **Research value:** 5/5 (Solves the primary "scaling vs. precision" trade-off in modern architectures).