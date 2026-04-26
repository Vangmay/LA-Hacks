# Unresolved Conflicts

This document outlines the extant contradictions, evidentiary gaps, and missing literature partitions identified across the sub-quadratic scaling and positional encoding investigations. These conflicts must be addressed through targeted adversarial searches and empirical validation before promoting speculative seeds to high-confidence research proposals.

## 1. Core Architectural Contradictions

### 1.1 The Extrapolation Redundancy Paradox
*   **The Conflict:** **LEDiT (2025)** argues that explicit Positional Encodings (PE) like RoPE are the *primary obstacle* to length extrapolation because they introduce Out-of-Distribution (OOD) coordinate values. Conversely, **standard LLM SOTA** (Llama-3, Mistral) relies heavily on RoPE for performance. **Haviv (2022)** suggests causal masks provide implicit global signals, making explicit PE redundant for global ordering but potentially necessary for local "sharpness."
*   **Unresolved Question:** Is explicit PE a "crutch" that provides high-frequency local syntax at the cost of a global extrapolation "wall," or is the implicit signal from causal masking too coarse for non-linear reasoning (e.g., code, logic)?
*   **Required Follow-up Search:** `spectral analysis of hidden states in NoPE (No Positional Encoding) vs RoPE transformers on code-completion tasks`.

### 1.2 Equivariance vs. Capacity Trade-off
*   **The Conflict:** **Vaswani (2017)** intentionally broke translation equivariance (shift-invariance) to allow the model to learn context-specific positional meanings. Modern "restoration" efforts (**Yeh 2022**, **Baron 2023**) treat this removal as a flaw and propose re-introducing hard Toeplitz constraints.
*   **Unresolved Question:** Does a hard translation-equivariance constraint (Toeplitz) act as a regularizer that improves generalization, or a bottleneck that prevents the model from identifying document-specific "anchors" (like the start/end of a sequence)?
*   **Required Follow-up Search:** `performance degradation of shift-invariant kernels in document-level vs sentence-level NLP tasks`.

### 1.3 The "Locality Trap" Artifact
*   **The Conflict:** Sub-quadratic models like **HiP (2024)** achieve $O(T \log T)$ by assuming "attention locality" (nearby tokens are most important). However, it is unclear if this locality is a fundamental property of language data or an artifact induced by **RoPE/Relative bias**, which decays with distance.
*   **Unresolved Question:** If trained with Absolute Positional Encodings (APE) or NoPE, would the attention maps still exhibit the locality that sub-quadratic pruning heuristics rely on?
*   **Required Follow-up Search:** `attention head entropy comparison: RoPE vs APE in long-context (128k+) sequences`.

---

## 2. Weak Evidence & Speculative Claims

### 2.1 The SSM "Projection Loss" Hypothesis
*   **Weakness:** The failure of SSMs (Mamba) on Needle-in-a-Haystack (NIAH) tasks is well-documented (**Huang 2024**). However, the proposal for **Addressable State-Space Retrieval (ASSR)** assumes the failure is due to *state decay* (storage). Recent critiques suggest it may instead be *projection loss* (the model fails to encode the needle into the state initially).
*   **Missing Evidence:** Comparative analysis showing whether an SSM *can* recall a needle if the state is perfectly preserved vs. if the bottleneck is the initial write-to-state.
*   **Required Follow-up Search:** `Mamba selective scan information bottleneck analysis: write vs read failure`.

### 2.2 Implicit Position Granularity
*   **Weakness:** While **Haviv (2022)** proves LLMs learn implicit position, the evidence for the *resolution* of this signal is thin. It is unclear if the implicit signal can distinguish token $N$ from $N+1$ at scale (e.g., at position 32,768).
*   **Required Follow-up Search:** `probing for absolute token index resolution in PE-free causal transformers at 32k context`.

---

## 3. Missing Literature Buckets & Failed Searches

### 3.1 The 2019-2020 "Efficiency Survey" Gap
*   **Missing Bucket:** The investigation lacks explicit coverage of the "first wave" of efficient transformers, specifically **Reformer (LSH)** and **Longformer (Sliding Window)**. This creates a risk of re-proposing mechanisms (like Fragment Retrieval) that were matured in 2020.
*   **Failed Search:** Querying for `internal KV-cache retrieval` yielded zero results, highlighting a lexical mismatch between "Database Retrieval" and "Efficient Attention Mechanisms."

### 3.2 Lexical Failure in Limitation Mining
*   **Failed Search:** `limitations of RoPE "Rotary Positional Embedding" long context` yielded zero high-citation results. Critique of RoPE is likely "hidden" within the methodology sections of papers proposing new scaling heuristics (YaRN, NTK-aware), rather than standalone critiques.
*   **Required Search Strategy:** Switch from "limitation" keywords to "OOD length failure" and "frequency interpolation error" in 2024/2025 papers.

---

## 4. Exact Follow-up Searches Needed

To resolve the conflicts above, the next run must execute the following precise queries:

1.  **Search 1 (Toeplitz Collision):** `"Discrete Toeplitz Constraint" AND "Self-Attention" AND "backpropagation"` — Determine if hard-constrained shift-invariant attention has been implemented and dismissed for capacity reasons.
2.  **Search 2 (Implicit Signal Decay):** `"Causal mask" position sensing resolution "linear attention"` — Analyze if the implicit positional signal survives the transition from Softmax-Attention to Sub-quadratic/Linear Attention (SSMs).
3.  **Search 3 (Spectral PE Pruning):** `"High-pass filter" positional encoding OR "band-limited" RoPE` — Directly test the collision risk for the `SD-PB` (Spectral Deconfliction) proposal.
4.  **Search 4 (State vs. Embedding):** `internal retrieval of "SSM states" vs "raw embeddings"` — Check if existing hybrid models (Jamba, etc.) have already attempted to retrieve previous latent snapshots rather than text.