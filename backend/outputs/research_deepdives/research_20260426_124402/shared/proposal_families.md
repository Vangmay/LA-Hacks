# Proposal Families

## Family: Addressable Sub-Quadratic Retrieval
**Focus:** Restoring the "pointer" capability and retrieval precision of quadratic attention to $O(N)$ or $O(N \log N)$ architectures without reintroducing $O(N^2)$ KV-caches.

### 1. Proposal Candidate: Addressable State-Space Retrieval (ASSR)
- **Source proposal seeds:** `Addressable State-Space Retrieval (ASSR)` (investigator_01).
- **Merged idea:** Re-introduces discrete addressability to State Space Models (SSMs) by externalizing latent state snapshots into an indexed bank, allowing for random-access "recall" when the sequential state decays.
- **Core novelty claim:** Unlike hybrid models (e.g., Jamba) that alternate SSM and Attention layers, ASSR performs retrieval over *compressed latent states* rather than raw token embeddings, specifically triggered by state-entropy spikes.
- **Evidence basis:** `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (Huang 2024) identifies that SSMs (Mamba) fail at "Needle-in-a-Haystack" (NIAH) tasks despite theoretical infinite context due to "addressability decay."
- **Prior-work collision:** Fast Weight Programmers (90s) used additive updates (associative memory); ASSR adds discrete indexing.
- **Future-work collision:** Mamba-2 (State Space Duality) simplifies the scan but does not address the storage/retrieval of historical states for non-local tasks.
- **Mechanism:** A quantization-trigger mechanism monitors state entropy. When a token represents a significant context shift, the SSM's hidden state is pushed to a k-NN index. Future queries perform a lightweight cross-attention over these "state checkpoints."
- **Validation:** Test on NIAH with 128k context using a Mamba-2.8B base model enhanced with an ASSR retrieval layer.
- **Falsification:** If performance gains are identical to retrieving raw token embeddings (RAG), then the latent state storage provides no architectural advantage.
- **Confidence:** High (Grounding in clear empirical SOTA failure).
- **Decision:** promote

### 2. Proposal Candidate: Differentiable HNSW Attention Layer
- **Source proposal seeds:** `Differentiable HNSW Layer for Dynamic Sub-Quadratic Attention` (investigator_01).
- **Merged idea:** Replaces the dense dot-product attention matrix with a navigable small-world graph structure built on activations that is fully end-to-end differentiable.
- **Core novelty claim:** Moves from "heuristic pruning" (e.g., H2O, HiP) to "learned indexing" where the search graph's edges are optimized via backpropagation to support $O(N \log N)$ training and inference.
- **Evidence basis:** `428c6bd657229d4f3360b5f5920ad3609739ecdc` (HiP 2024) shows that tree-search can approximate attention, but remains non-differentiable / training-free.
- **Prior-work collision:** Reformer (LSH-based routing), Reformer (2020); HNSW (Malkov 2018) is non-differentiable.
- **Future-work collision:** Sparse Attention (BigBird) uses static/random masks; this is dynamic and content-indexed.
- **Mechanism:** Uses Gumbel-Softmax or Straight-Through Estimators on graph edge selection to build a Navigable Small World (HNSW) index of KV pairs. Gradients flow through the "optimal path" found during graph traversal.
- **Validation:** Train a 1B parameter model from scratch on the Pile and compare perplexity/throughput parity with FlashAttention-2.
- **Falsification:** If the computational cost of maintaining the graph (insertions/updates) exceeds the quadratic cost for $N < 64k$.
- **Confidence:** Medium-High.
- **Decision:** promote

---

## Family: Inductive Bias Restoration & Spectral Scaling
**Focus:** Resolving the "Extrapolation Wall" by formally separating local syntactic biases from global positional signals.

### 1. Proposal Candidate: Spectral Deconfliction of Positional Bias (SD-PB)
- **Source proposal seeds:** `Spectral Deconfliction of Positional Bias (SD-PB)` (investigator_02), `Implicit-Explicit Hybrid Resonance (IE-HR)` (investigator_02).
- **Merged idea:** Resolves the length-extrapolation failure by high-pass filtering explicit positional encodings (RoPE) to provide local precision while relying on causal-mask implicit signals for global positioning.
- **Core novelty claim:** Identifies a "redundancy conflict" where explicit PEs (RoPE) provide global coordinate values that causal masks already implicitly encode, leading to OOD crashes when those explicit coordinates hit unseen values.
- **Evidence basis:** `Zhang et al. (2025)` (LEDiT) claims explicit PE is the primary barrier to OOD scaling; `Haviv et al. (2022)` proves causal masks provide implicit global position.
- **Prior-work collision:** NoPE (removes PE entirely), ALiBi (linear local bias).
- **Future-work collision:** Recent "interpolation" methods (YaRN, LongRoRA) try to stretch the grid; SD-PB prunes the grid to prevent OOD failure.
- **Mechanism:** **Frequency-High-Pass RoPE**. Modify the rotary frequency spectrum to zero out components below a threshold $\tau$. RoPE maintains relative ordering for syntax, while the "count" of preceding tokens (implicit in the causal mask) handles global document structure.
- **Validation:** "Passkey Retrieval" and NIAH at 8x training length (e.g., train at 4k, test at 32k) compared against standard RoPE and YaRN.
- **Falsification:** If the model fails on tasks requiring exact absolute indexing (e.g., "What is the 542nd word?"), the implicit signal is too coarse.
- **Confidence:** High.
- **Decision:** promote

### 2. Proposal Candidate: Hard-Constrained Toeplitz Attention Kernels
- **Source proposal seeds:** `Translation-Invariant Attention via Toeplitz-Structured Positional Bias` (investigator_02).
- **Merged idea:** Enforces true translation equivariance by constraining the positional bias in attention to be a formal Toeplitz operator, preventing the model from learning position-dependent artifacts.
- **Core novelty claim:** Moves from "soft" learned relative biases (T5, Shaw 2018) to a "hard" structural constraint that ensures the attention mechanism behaves as a sequence of dynamic shift-invariant filters (discrete convolution).
- **Evidence basis:** `Yeh et al. (2022)` (Equivariance discovery) shows shift-invariance can be "discovered" as Toeplitz matrices; `Baron et al. (2023)` shows SSMs restore this bias in ViTs.
- **Prior-work collision:** Shaw et al. (2018) - Relative bias; Yeh et al. (2022) - Parameter sharing.
- **Future-work collision:** ALiBi uses a fixed Toeplitz-like slope; this proposal makes the *entire* bias kernel dynamic but constrained.
- **Mechanism:** Impose the structural constraint $A = QK^T + \mathcal{T}(\phi)$ where $\mathcal{T}$ represents a Toeplitz matrix generated by a learned continuous kernel $\phi(i-j)$. This prevents the model from ever breaking shift-invariance in the attention logit.
- **Validation:** Parity test with CNNs on synthetic bit-string pattern matching tasks where patterns occur at arbitrary indices.
- **Falsification:** If the model requires breaking shift-invariance (local/global absolute anchors) to achieve competitive NLP performance, the constraint will be a bottleneck.
- **Confidence:** Medium.
- **Decision:** speculative

---

## Rejected or Weak Ideas

- **Context-Adaptive Rotary Base Scaling (CARBS):** Rejected. Heuristic scaling (YaRN) and NTK-aware scaling are already highly optimized; a learned MLP adds performance overhead for likely marginal gain.
- **Formal Equivalence Analysis (Linear/Gated RNN):** Rejected. Primarily an analytical/survey contribution; does not propose a novel architectural artifact.
- **Selective Fragment Retrieval Attention:** Rejected. Too similar to existing sliding-window + global token patterns (BigBird/Longformer). Replaced by the more technically specific "Differentiable HNSW" proposal.
- **PE-Free LLMs for Everything:** Rejected. Research shows PE-free models lack high-frequency "sharpness" needed for code/reasoning; replaced by the "Spectral Deconfliction" hybrid proposal.

## Novelty Score Rubric

| Proposal | Novelty | Technical Spec. | Evidence | Feasibility | Value |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **ASSR** | 5 | 4 | 5 | 4 | 5 |
| **Diff. HNSW** | 4 | 5 | 3 | 3 | 4 |
| **SD-PB** | 5 | 4 | 5 | 5 | 5 |
| **Toeplitz Kernels**| 3 | 4 | 4 | 4 | 3 |