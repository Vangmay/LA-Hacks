# Final Research Deep Dive Report: Sub-Quadratic Architectures and Inductive Bias Restoration

## 1. Executive Summary

This deep dive evaluates the evolution of sequence modeling from the $O(N^2)$ baseline of **Vaswani et al. (2017)** to modern sub-quadratic and retrieval-augmented architectures. The investigation identifies a fundamental "Addressability-Extrapolation Conflict": architectures attempting to solve the quadratic wall (SSMs, Linear Attention) often lose the high-precision retrieval capabilities of the KV-cache, while the primary tool for KV-cache navigation—Positional Encoding (RoPE)—acts as the primary barrier to long-context scaling.

The synthesis draws from 1990s **Fast Weights** and classical **Toeplitz filter theory** to propose eight distinct research spinoffs. These proposals range from high-confidence spectral deconfliction systems to speculative differentiable graph-attention layers. Key findings include the empirical failure of SSMs on precision retrieval (**Huang, 2024**) and the redundancy of explicit positional encodings in the presence of causal masks (**Zhang, 2025**).

---

## 2. Seed Paper Metadata

| Property | Value |
| :--- | :--- |
| **Title** | Attention is All You Need |
| **Paper ID** | `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (ARXIV:1706.03762) |
| **Year** | 2017 |
| **Venue** | NIPS |
| **Authors** | Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin |
| **Core Mechanism** | Multi-Head Self-Attention ($O(N^2)$ dot-product) |
| **Inductive Bias** | Dispensed with recurrence and convolution; used Sinusoidal Absolute PE |
| **Claim** | Attention allows global dependencies without the path-length bottlenecks of recurrence. |

---

## 3. Literature Map by Bucket

| Bucket | Key Papers | Technical Relevance |
| :--- | :--- | :--- |
| **seed_metadata** | Vaswani (2017) | Foundation; the baseline $O(N^2)$ architecture. |
| **foundational_references** | Gehring (2017); Haviv (2022) | Pre-transformer CNNs; Proof of implicit positional signals via causal masks. |
| **closest_prior_work** | Shaw (2018); Katharopoulos (2020) | Relative PE (RPE); Equivalence of Linear Attention and RNNs. |
| **direct_followups** | Schlag (2021); Su (2021) | Link to 1990s Fast Weights; Introduction of RoPE. |
| **recent_followups** | Mamba (2024); LEDiT (2025); HiP (2024) | Selective SSMs; PE-free diffusion; $O(N \log N)$ hierarchical pruning. |
| **critiques_limitations** | Huang (2024); Kazemnejad (2023) | SSM failure on NIAH retrieval; Implicit signal resolution limits. |
| **benchmarks_reproductions** | Long Range Arena (LRA); NIAH | Standardized tests for retrieval precision and long-context scaling. |

---

## 4. Closest Prior Work

*   **Fast Weight Programmers (Schmidhuber, 1992):** **Schlag (2021)** establishes that modern Linear Transformers are mathematically equivalent to these recursive architectures. The "novelty" of current sub-quadratic kernels is often a rediscovery of these additive/error-correcting update rules from the early 90s.
*   **Convolutional Sequence to Sequence (Gehring, 2017):** Utilized $O(N)$ convolutional stacks with decoder attention, providing a baseline for translation-equivariant sequence modeling that Vaswani et al. aimed to simplify into a unified attention mechanism.
*   **Relative Positional Representations (Shaw, 2018):** Re-introduced local shift-invariance (inductive bias) that the original Transformer lacked. This work is the intellectual ancestor of modern relative biases and Rotary Position Encodings (RoPE).

---

## 5. Direct Follow-ups and Recent State of Field

The field has split into two primary camps addressing the quadratic bottleneck:
1.  **Selective State-Space Models (SSMs):** **Mamba (2024)** and **Mamba-2** utilize selective scans for $O(N)$ scaling. However, they suffer from "Addressability Decay," failing to retrieve specific "needles" in long contexts compared to standard Transformers (**Huang 2024**).
2.  **Length Extrapolation Heuristics:** Modern LLMs use **RoPE**, but scaling it to long context requires heuristics like **YaRN** or **NTK-scaling** to avoid distribution shifts. **LEDiT (2025)** argues that any explicit PE is a barrier to extrapolation because it forces the model to handle Out-of-Distribution (OOD) coordinate values.

---

## 6. Critiques, Limitations, Reproductions, and Benchmark Evidence

*   **The Addressability Gap:** Extensive **Needle-in-a-Haystack (NIAH)** testing reveals that while SSMs scale theoretically to infinite lengths, their retrieval precision collapses as state compression saturates. Pure recurrence loses the "pointer" resolution of the KV-cache.
*   **The Locality Trap:** Sub-quadratic pruning ($O(N \log N)$) methods like **HiP (2024)** assume "attention locality." Critiques suggest this locality may be an artifact of RoPE's distance-decay bias (which naturally emphasizes nearby tokens) rather than an inherent property of the data.
*   **Implicit Signal Resolution:** While **Haviv (2022)** proves causal masks provide positional signals, critics note this signal lacks the **high-frequency resolution** (exact token offsets) required for symbolic tasks like code generation or mathematical reasoning.

---

## 7. Novelty Comparison Table

| Mechanism | Vaswani (2017) Seed | Prior Work Predecessor | Modern Sub-Quadratic | Novelty Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Memory** | All-to-all KV Cache | LSTMs (Recurrence) | Selective SSMs | Selective vs. Gated additive updates |
| **Positioning** | Sinusoidal Fixed PE | CNN Local Filters | RoPE / Implicit Mask | Rotary frequency vs. absolute coords |
| **Complexity** | $O(N^2)$ | $O(N)$ Recurrence | $O(N \log N)$ Pruning | Differentiable search vs. static masks |

---

## 8. Research-Gap Candidates

*   **Gap 1: Addressability Decay in Linearized Attention.** Sub-quadratic models lose the discrete "pointer" resolution of the KV-cache.
*   **Gap 2: The Redundancy Conflict in PEs.** Explicit RoPE provides global coordinates that causal masks already encode, leading to OOD crashes.
*   **Gap 3: Differentiability of Graph-Attention.** Hierarchical pruning (HNSW) is efficient for inference but current implementations are difficult to train end-to-end.
*   **Gap 4: Precision Resolution of Implicit Signals.** It is unknown if mask-based signals can resolve exact token offsets at $N > 100k$ context.

---

## 9. Proposal Seed Inventory and Rejected Weak Ideas

### Rejected or Weak Ideas
*   **Context-Adaptive Rotary Base Scaling (CARBS):** Rejected due to high overlap with existing YaRN/NTK-aware scaling heuristics.
*   **PE-Free LLMs for Everything:** Rejected as evidence (Haviv 2022) suggests NoPE models lack the "sharpness" needed for complex symbolic reasoning.
*   **Selective Fragment Retrieval Attention:** Rejected as technically inferior to the more robust "Differentiable HNSW" graph traversal concept.

### Proposal Seed Inventory
1.  **SD-PB:** Spectral Deconfliction of Positional Bias (High-pass RoPE).
2.  **ASSR:** Addressable State-Space Retrieval (Quantized latent snapshots).
3.  **DRT:** Delta-Rule Triton (Fused error-correcting fast weights).
4.  **S3R:** Combined Spectral/SSM Retrieval Hybrid.
5.  **Diff-HNSW Attention:** Fully differentiable graph search layers.
6.  **TC-GA:** Toeplitz-Constrained Graph Attention ($O(N \log N)$ equivariance).
7.  **HNK-TA:** Hyper-Kernel Non-Linear Toeplitz Attention.
8.  **LUGI:** Lazy-Update Graph Indexing for training efficiency.

---

## 10. High-Confidence Spinoff Proposals

## Spinoff Proposal: Spectral Deconfliction of Positional Bias (SD-PB)

### One-sentence idea
Resolves length extrapolation failures by high-pass filtering Rotary Positional Encodings (RoPE) to solve for local syntax while relying on causal-mask implicit signals for global positioning.

### Core novelty claim
Identifies a "redundancy conflict" where explicit PEs provide global coordinates that causal masks already encode, leading to OOD crashes; pruning the global part of the explicit grid restores scaling without losing local precision.

### Seed-paper connection
- Seed mechanism/claim: Used Absolute Positional Encodings (Sinusoids) for all frequencies (Vaswani 2017).
- What the seed paper does: Provides a unified positional grid for both local syntax and global position across all heads.
- What this proposal changes: Replaces the unified signal with a frequency-split hybrid: High-Pass RoPE (relative/local) + Implicit Mask Count (global).

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Implicit global position | Haviv (2022) | Proves explicit global PE is redundant in causal models. |
| RoPE crashes OOD | LEDiT (2025) | Identifies explicit PE as the extrapolation barrier. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| NoPE (No Pos-Encoding) | Kazemnejad (2023) | Removes PE entirely | SD-PB keeps high-freq RoPE for local "sharpness"/syntax. |
| ALiBi | Press (2021) | Static local bias | SD-PB uses dynamic rotary high-frequencies. |

### Future-work/SOTA collision
**LEDiT (2025)** proposes NoPE for Diffusion, but SD-PB targets symbolic reasoning in LLMs where local order is more critical than in pixels.

### Technical mechanism
**Frequency-High-Pass RoPE**: zero out rotary spectrum components with wavelengths longer than the original training sequence length $L_{train}$. The query calculates relative local distance via surviving frequencies, while the "count" of predecessors (implicit in the mask) handles the document-level absolute position.

### Minimum viable validation
- First experiment/proof/implementation: Passkey Retrieval at 32k context on a 1B model trained at 4k.
- Required dataset/tool/formalism: Custom Triton RoPE kernel with frequency masking.
- Success criterion: $>90\%$ retrieval accuracy at 8x training length.

### Falsification criteria
If the implicit signal resolution is too coarse to distinguish token $N$ from $N+1$ at $N=100k$, the model will fail on precise symbolic tasks (e.g. code parsing).

### Research plan
- Week 1: Implement frequency-masking in RoPE kernels (Triton).
- Week 2-3: Pre-train 1B model on sequence length 4k with SD-PB.
- First deliverable: Extrapolation benchmark report (Passkey/NIAH).

### Confidence
- Confidence: High
- What would raise confidence: Confirmation of mask resolution via probing.
- What would lower confidence: Findings that NoPE is sufficient for code-completion.

---

## Spinoff Proposal: Addressable State-Space Retrieval (ASSR)

### One-sentence idea
Restores precise retrieval to sub-quadratic SSMs by externalizing quantized latent state "snapshots" into an addressable vector bank triggered by state-entropy spikes.

### Core novelty claim
Moves from "recurrent state compression" to "addressable state snapshots," decoupling long-term context throughput ($O(N)$) from discrete pointer access (k-NN), specifically targeting the NIAH failure of pure SSMs.

### Seed-paper connection
- Seed mechanism/claim: Discarded recurrence for addressable attention (Vaswani 2017).
- What the seed paper does: Maintains a full KV cache so every historical token is a pointer target.
- What this proposal changes: Reintroduces recurrence (SSM) for throughput but fixes its addressability failure by externalizing snapshots during high-information transitions.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| SSMs fail on NIAH | Huang (2024) | Documents the addressability decay in compressed models. |
| Latent states are addressable | HiP (2024) | Shows tree-search can map hidden activations. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Infini-attention | MvA (2024) | KV cache compression | ASSR stores *SSM hidden states*, not compressed KV-cache pairs. |
| Recurrent Memory Token | RMT (2022) | Recurrent tokens | ASSR uses discrete vector retrieval over latent checkpoints. |

### Future-work/SOTA collision
**Mamba-2 (State Space Duality)** improves the scan efficiency but does not solve the fundamental loss of non-local historical states.

### Technical mechanism
A monitor tracks the entropy of the SSM's selection gate. When entropy spikes (new context topic), the current state vector $h_t$ is quantized and pushed to a FAISS index. Future queries use a small cross-attention layer to "recall" relevant historical states.

### Minimum viable validation
- First experiment/proof/implementation: 128k NIAH task with Mamba-2.8B + ASSR layer.
- Required dataset/tool/formalism: Faiss integration into current SSM scan kernels.
- Success criterion: $100\%$ accuracy on NIAH where base Mamba typically reaches $<10\%$.

### Falsification criteria
If retrieving from historical *states* provides no gain over retrieving *raw token embeddings* (standard RAG), the architecture is redundant.

### Research plan
- Week 1: Develop snapshot quantization and FAISS integration layer.
- Week 2-3: Fine-tune Mamba with ASSR on long-context logic tasks.
- First deliverable: NIAH accuracy vs context length Pareto curve.

### Confidence
- Confidence: High
- What would raise confidence: Proof that state entropy correlates with "needle" positions in NIAH.
- What would lower confidence: Finding that Mamba-2 already resolves addressability via duality.

---

## Spinoff Proposal: Delta-Rule Triton (DRT) Kernels

### One-sentence idea
A hardware-fused error-correcting associative memory kernel that implements the 1990s Delta Rule to increase the information density of Linear Transformers.

### Core novelty claim
Translates theoretical associative memory density improvements (Schmidhuber 1992) into a modern Triton-fused scan, outperforming standard additive updates (RWKV/Mamba) in multi-step logical retrieval.

### Seed-paper connection
- Seed mechanism/claim: All-to-all Self-attention ($O(N^2)$).
- What the seed paper does: Calculates exact pairwise similarity for all possible dependencies.
- What this proposal changes: Replaces global pairwise compute with a fused scan that uses the "Delta Rule" ($W_t = W_{t-1} + e \otimes k$) for $O(N)$ compute with higher capacity than simple additive updates.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Linear Attn $\equiv$ Fast Weights | Schlag (2021) | Proves mathematical lineage to early 90s RNNs. |
| Delta Rule capacity | Schmidhuber (1992) | Shows additive updates (modern standard) saturate early. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Linear Transformers | Katharopoulos (2020) | Uses additive updates | DRT uses error-correcting terms ($v_t - W_{t-1} k_t$). |
| Gated Slotted Attention | Zhang (2023) | Gated updates | DRT specifically targets the Triton-fused error-correction term. |

### Future-work/SOTA collision
**Mamba-2 (2024)** uses hardware-aware scans but its updates are primarily selective additive ones rather than error-correcting associative updates.

### Technical mechanism
Implements the update $W_{t} = W_{t-1} + \eta (v_t - W_{t-1} k_t) \otimes k_t$ as a fused CUDA kernel. This ensures the associative state $W_t$ only updates when the existing memory cannot predict the value $v_t$ for key $k_t$.

### Minimum viable validation
- First experiment/proof/implementation: Perplexity comparison on LongBench vs. RWKV-6.
- Required dataset/tool/formalism: Custom Triton scan kernel implementation.
- Success criterion: Lower perplexity for the same total state size on recall-heavy tasks.

### Falsification criteria
If the sequential nature of the error feedback term cannot be masked by kernel tiling, training throughput will be too low for large models.

### Research plan
- Week 1: Write Triton kernel for sequential Delta Rule scan.
- Week 2-3: Benchmark memory capacity against Pure Additive Linear Attention.
- First deliverable: Capacity-accuracy scaling report.

### Confidence
- Confidence: Medium-High
- What would raise confidence: Triton parallelization of the error-correcting gradient term.
- What would lower confidence: Mamba-2 achieving similar capacity with simpler gating.

---

## Spinoff Proposal: Spectral State-Space Retrieval (S3R)

### One-sentence idea
A hybrid architecture combining the $O(1)$ addressability of snapshots with the $O(N)$ throughput of SSMs by utilizing frequency-split relative positional signals.

### Core novelty claim
Merges the Addressability solution (ASSR) with the Extrapolation solution (SD-PB), creating a state-space model that retrieves from its own history using high-pass relative coordinates.

### Seed-paper connection
- Seed mechanism/claim: Dot-product attention (Vaswani 2017).
- What the seed paper does: Uniform attention over a discrete KV cache with sinusoidal PE.
- What this proposal changes: Replaces global attention with a Selective SSM coupled to a "Spectral Snapshot Bank" indexed by high-frequency RoPE.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| SSM NIAH Failure | Huang (2024) | Proves the base model needs a random-access bank. |
| RoPE Scaling Wall | Zhang (2025) | Proves the bank must avoid explicit global RoPE coordinates. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| RetNet | Sun (2023) | Retentive Recurrence | S3R's memory is addressable via high-pass query, not just recurrent. |
| Jamba | AI21 (2024) | Hybrid SSM/Attn | S3R attends to *latent states*, significantly reducing memory footprint. |

### Future-work/SOTA collision
**Infini-attention** (Google 2024) uses local KV buffers. S3R uses global latent snapshots indexed specifically by local relative RoPE.

### Technical mechanism
1. SSM processes sequence. 2. Latent snapshots stored in FAISS. 3. Query uses **High-Pass RoPE** to find local syntax matches. 4. Query attends to the snapshot bank for non-local global recovery.

### Minimum viable validation
- First experiment/proof/implementation: 1M context retrieval task.
- Required dataset/tool/formalism: Frequency-high-pass RoPE kernel; Mamba-v2 backbone.
- Success criterion: Transformer-level NIAH accuracy at 1M tokens with linear wall-clock scaling.

### Falsification criteria
If the snapshot retrieval latency is dominated by k-NN overhead during training forward-passes.

### Research plan
- Week 1: Integrate high-pass RoPE into SSM attention/gating layers.
- Week 2-3: Evaluation on 1M context longitudinal benchmarks.
- First deliverable: S3R Model Reference Implementation.

### Confidence
- Confidence: Medium-High
- What would raise confidence: Latency parity with vanilla Mamba at 100k+ sequence lengths.
- What would lower confidence: Findings that mask signals fail to resolve snapshot indices at scale.

---

## 11. Speculative or Needs-More-Search Proposals

## Spinoff Proposal: Differentiable HNSW Attention (Diff-HNSW)

### One-sentence idea
Replaces $O(N^2)$ attention with a learned Navigable Small World (HNSW) graph built on activation manifolds that is fully end-to-end differentiable.

### Core novelty claim
Moves from heuristic pruning (HiP, H2O) to an end-to-end differentiable search structure where the graph's navigable edges are optimized via backpropagation.

### Seed-paper connection
- Seed mechanism/claim: Dot-product attention matrix (Vaswani 2017).
- What the seed paper does: Calculates every pairwise score to find the maximum.
- What this proposal changes: Changes the dense score calculation to an $O(N \log N)$ path traversal through an optimized graph.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Tree-search attention | HiP (2024) | Proves k-NN approximations for attention are viable in language. |
| Differentiable k-NN | Yeh (2022) | Shows soft selection can yield gradients. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Reformer | Kitaev (2020) | LSH hashing | Diff-HNSW uses dynamic graph traversal rather than static buckets. |

### Future-work/SOTA collision
**H2O (Heavy Hitter Oracle)** uses static top-k heuristics. Diff-HNSW learns the connectivity to find those heavy hitters.

### Technical mechanism
Uses Gumbel-Softmax on edge selection to build an HNSW index of activations. Gradients flow through the "optimal path" found during graph traversal via Straight-Through Estimators (STE).

### Minimum viable validation
- First experiment/proof/implementation: Throughput vs FlashAttention comparison at 64k.
- Required dataset/tool/formalism: Gumbel-Softmax over adjacency matrices.
- Success criterion: Learned cluster structure in the graph that mirrors semantic logic.

### Falsification criteria
If the construction cost of the graph during training forward-passes exceeds $O(N^2)$ for typical sequence lengths.

### Research plan
- Week 1: Prototype differentiable edge selection module.
- Week 2-3: Baseline vs. Reformer and Longformer LSH.
- First deliverable: Differentiable graph layer code.

### Confidence
- Confidence: Medium
- What would raise confidence: Proof of stable gradients through multi-hop graph hops.
- What would lower confidence: Findings that graph reconstruction freezes training logic.

---

## Spinoff Proposal: Toeplitz-Constrained Graph Attention (TC-GA)

### One-sentence idea
Enforces translation equivariance by constraining graph-attention edge probabilities to satisfy a hard-baked Toeplitz kernel.

### Core novelty claim
Synergizes hierarchical scaling (from Diff-HNSW) with a signal processing hard constraint, preventing the model from learning position-dependent biases.

### Seed-paper connection
- Seed mechanism/claim: Absolute Positional Encoding (Sinusoids) (Vaswani 2017).
- What the seed paper does: Allows the attention map to learn arbitrary non-invariant dependencies.
- What this proposal changes: Restricts the attention search space strictly to relative-distance filters (Toeplitz).

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Equivariance Discovery | Yeh (2022) | Shows shift-invariance can be found via Toeplitz discovery. |
| Graph pruning | HiP (2024) | Shows hierarchical scaling is data-efficient. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| ALiBi | Press (2021) | Static relative bias | TC-GA is a dynamic *graph* constraint based on distance. |

### Future-work/SOTA collision
**Baron (2023)** uses SSMs for vision invariance; TC-GA applies this directly to the attention graph navigation logic.

### Technical mechanism
During HNSW construction, the edge probability $P(i,j)$ is conditioned on a learned Toeplitz bias $B_{i,j} = \mathcal{T}(i-j)$. This ensures the search structure itself adheres to classical linear time-invariant (LTI) properties.

### Minimum viable validation
- First experiment/proof/implementation: Bit-string pattern shift test at arbitrary indices.
- Required dataset/tool/formalism: Toeplitz-gated adjacency matrix.
- Success criterion: 100% accuracy on pattern matching regardless of starting index.

### Falsification criteria
If document reasoning requires "anchors" (like "start of file") which break shift-invariance.

### Research plan
- Week 1: Implement Toeplitz-mask layer for graph construction.
- Week 2-3: Comparative test vs standard Graph Attention (GAT).
- First deliverable: Benchmark results on shift-invariant datasets.

### Confidence
- Confidence: Medium-Low
- What would raise confidence: SOTA results on translation-heavy vision tasks using TC-GA.
- What would lower confidence: Complexity overhead of maintaining the matrix constraint.

---

## Spinoff Proposal: Hyper-Kernel Non-Linear Toeplitz Attention (HNK-TA)

### One-sentence idea
Extends ALiBi's fixed linear bias to a learned non-linear Toeplitz kernel generated by a shared Hypernetwork.

### Core novelty claim
Positional bias should be a learned sequence of non-linear filters constrained to be distance-only, providing more capacity than RoPE without the extrapolation wall.

### Seed-paper connection
- Seed mechanism/claim: Sinusoidal Positional Encoding (Vaswani 2017).
- What the seed paper does: Uses a fixed sinusoidal grid for positional signals.
- What this proposal changes: Uses a Hypernetwork to generate a distance-dependent bias kernel $\phi(|i-j|)$.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| ALiBi Extrapolation | Press (2021) | Proves local Toeplitz-like biases extrapolate well. |
| Hypernetworks | Ha (2016) | Allows efficient generation of large weights from small nets. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| T5 Relative Bias | Raffel (2019) | Learned Relative Bias | HNK-TA uses a *continuous* non-linear kernel net for arbitrary distances. |

### Future-work/SOTA collision
**DeepSeek-V2 (MLA)** uses latent positional signals; HNK-TA focuses on distance-based non-linear filtering.

### Technical mechanism
A small MLP (the Hypernetwork) takes distance $d = |i-j|$ and outputs a scalar bias $B_d$. The attention logit is $QK^T + B_d$. This allows for complex, multi-modal learned attraction/repulsion vs distance while maintaining hard shift-invariance.

### Minimum viable validation
- First experiment/proof/implementation: Training length 2k vs Test length 16k on WikiText.
- Required dataset/tool/formalism: Shared MLP kernel in attention head script.
- Success criterion: Outperforming ALiBi and RoPE on perplexity extrapolation.

### Falsification criteria
If the kernel collapses to a simple linear decay (reducing to ALiBi).

### Research plan
- Week 1: Implement hyper-kernel bias module.
- Week 2-3: Extrapolation benchmarks on 1B parameter models.
- First deliverable: Hyper-kernel vs Fixed-bias comparison report.

### Confidence
- Confidence: Medium
- What would raise confidence: Proof of smoother extrapolation curves than YaRN.
- What would lower confidence: High training variance in the kernel net.

---

## Spinoff Proposal: Lazy-Update Graph Indexing (LUGI)

### One-sentence idea
A training-efficient version of Differentiable HNSW that uses periodically refreshed search indices to mask the construction wall.

### Core novelty claim
Decouples representation learning (gradients) from indexing (structure) to enable sub-quadratic training on standard hardware while maintaining differentiability.

### Seed-paper connection
- Seed mechanism/claim: Multi-head attention (Vaswani 2017).
- What the seed paper does: Recalculates the full attention grid at every optimizer step.
- What this proposal changes: Freezes the attention search structure (graph) for fixed intervals to maximize throughput.

### Evidence basis
| Evidence | Paper/artifact | Why it matters |
|---|---|---|
| Lazy Optimizers | Martens (2015) | Shows periodic updates can converge efficiently. |
| HiP Pruning | HiP (2024) | Shows that local KV cache neighborhoods are relatively stable. |

### Closest prior-work collision
| Collision risk | Paper | Relationship | Why proposal may still survive |
|---|---|---|---|
| Quest | Zhang (2024) | Query-aware cache pruning | LUGI focuses on *indexing latent states* asynchronously during training. |

### Future-work/SOTA collision
**FlashAttention-3** optimizes hardware but doesn't change the $O(N^2)$ algorithm; LUGI targets the algorithmic wall.

### Technical mechanism
The attention graph structure $G$ is held static for $k=100$ steps. Projections $Q, K, V$ are learned continuously. The graph structure is asynchronously rebuilt on a secondary worker/buffer using the latest embeddings.

### Minimum viable validation
- First experiment/proof/implementation: Throughput benchmark vs dense attention.
- Required dataset/tool/formalism: Buffer-swapping logic in the forward pass.
- Success criterion: $>2x$ throughput gain over FlashAttention at 32k context.

### Falsification criteria
If the stale index causes catastrophic loss of context-awareness during training.

### Research plan
- Week 1: Build the buffer-swap attention layer logic.
- Week 2-3: Convergence speed (tokens-per-dollar) analysis.
- First deliverable: Training efficiency report.

### Confidence
- Confidence: Low-Medium
- What would raise confidence: Stable convergence at $k=500$ update intervals.
- What would lower confidence: Findings that embeddings shift too quickly for indexing.

---

## 12. Proposal Triage Matrix

| Proposal | Type | Novelty | Spec. | Evid. | Feas. | Value | Collision | Action |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **SD-PB** | Bias | 5 | 5 | 5 | 5 | 5 | LEDiT/NoPE | **Promote** |
| **ASSR** | State | 5 | 5 | 5 | 4 | 5 | Infini-attn | **Promote** |
| **DRT** | Memory| 4 | 5 | 4 | 4 | 4 | Mamba-2 | **Promote** |
| **S3R** | Hybrid| 5 | 5 | 5 | 3 | 5 | Jamba/JRT | **Promote** |
| **Diff-HNSW**| Graph | 4 | 4 | 3 | 1 | 4 | Reformer | Speculative |
| **TC-GA** | Bias | 3 | 4 | 4 | 4 | 3 | ALiBi/Baron | Speculative |
| **HNK-TA** | Bias | 4 | 4 | 3 | 4 | 4 | T5/ALiBi | Speculative |
| **LUGI** | Opt. | 3 | 4 | 3 | 5 | 3 | LazyGPT/Quest | Speculative |

---

## 13. Evidence Quality and Novelty-Risk Assessment

*   **Evidence Quality:** High. Proposals are grounded in 2024-2025 SOTA critiques (**Huang 2024** for SSMs, **Zhang 2025** for RoPE extrapolation).
*   **Novelty Risk:** High for architectural convergence (**Mamba-2** duality), but the spinoffs mitigate this by explicitly targeting identified retrieval failures (NIAH) rather than theoretical throughput.

---

## 14. Open Questions and Recommended Next Searches

1.  **Bit-resolution of Implicit signals:** Can causal-mask predecessor counts resolve exact token indices at 1 million tokens?
2.  **SSM Write Failure:** Is NIAH failure a loss of addressability (Read) or failure to initially encode the needle into the state (Write)?
3.  **Search 1:** `"Infini-attention" vs "Memory-Augmented State Space" retrieval accuracy`.
4.  **Search 2 (collision):** `"High-pass" rotary embeddings length extrapolation paper`.
5.  **Search 3:** `"Differentiable HNSW" complexity per training step for 1B model`.
6.  **Search 4:** `Is "attention locality" a data property or RoPE artifact?` (Check with APE-trained models).
7.  **Search 5:** `Implicit signal resolution in code-focused LLMs (StarCoder-NoPE)`.
8.  **Search 6:** `Delta-rule scan parallelization on H100 hardware nodes`.
9.  **Search 7:** `Relationship between "Addressability Decay" and the SSM Selection Gate`.
10. **Search 8:** `Selective Scan vs Delta Rule equivalence analysis`.