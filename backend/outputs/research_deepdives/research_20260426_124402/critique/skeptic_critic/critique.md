# Critique: Sub-Quadratic Scaling & Positional Encoding Syntheses
- Critic ID: `skeptic_critic`
- Date: 2026-04-26

## 1. Blocking Issues

- **Feasibility Blind-Spot in "Differentiable HNSW":** The proposal for a "Differentiable HNSW Attention Layer" ignores the $O(N \log N)$ or $O(N \text{ poly } \log N)$ construction cost of the HNSW graph *per training step*. While retrieval is efficient, updating a navigable small-world graph differentiably via Gumbel-Softmax requires either maintaining a static graph (failing to learn) or reconstructing it (computationally prohibitive compared to quadratic attention for $N < 100k$). This makes the proposal "not technically meaningful" in its current form.
- **Definitional Overlap in "Toeplitz Attention":** Relative Positional Encoding (RPE) as introduced by Shaw (2018) and used in T5/AliBi *is* a Toeplitz structure because the bias $B_{i,j}$ depends solely on the distance $i-j$. The investigator claims a "hard constraint" is novel, but most RPE implementations already use weight sharing that satisfies the Toeplitz condition. Without a specific mathematical divergence from standard RPE (e.g., a specific spectral regularization or non-linear Toeplitz mapping), this is a "seed restatement."

## 2. Major Issues

- **Collision Omission (ASSR vs. Infini-attention):** The **ASSR** proposal (quantizing SSM snapshots) has a high-risk collision with **Google’s Infini-attention (2024)** and **RetNet (2023)**. These models use compressive memory or "hidden state recycling" that approximates the "snapshot bank" idea. The investigator fails to distinguish how ASSR's retrieval from a *bank* of SSM states differs from the recurrent update of a single compressed state in RetNet or the local/global hybrid in Jamba.
- **Oversimplification of the "Locality Trap":** In the first report, the "Locality Trap" is attributed to pruning heuristics. However, recent work like **Quest (2024)** or **LazyGPT** shows that many "needles" can be found using very high sparsity if the query-dependent importance is tracked. The "Locality Trap" may be an artifact of static pruning, not a fundamental property of sub-quadratic models that a retrieve-over-states (ASSR) model would uniquely solve.
- **Stale Literature in Sub-Quadratic Coverage:** While the investigator acknowledges missing Reformer/Longformer, they also miss the **State Space Duality (SSD)** framework from **Mamba-2 (2024)**. SSD proves that SSMs *are* structured attention. Many of the proposed "hybrid" retrieval mechanisms might be mathematically redundant under the SSD duality, potentially rendering the "Addressability Decay" gap a optimization problem rather than an architectural one.
- **Implicit Signal Scaling Risk (SD-PB):** The **SD-PB** proposal relies on the causal mask's implicit positional signal. While **Haviv (2022)** proves this exists, the investigator provides no evidence that this signal has the *resolution* required for 100k+ contexts. If the implicit signal is coarse (logarithmic or approximate), the "High-Pass RoPE" will leave the model blind to precise ordering at long ranges, causing it to fail on tasks like "Long Document Diffing."

## 3. Minor Issues

- **Terminology Ambiguity:** "Addressability Decay" is used as a formal term but is a descriptive phrase from a single source (`Huang 2024`). It should be reconciled with more standard terms like "State Compression Saturation" or "Memory Volatility."
- **Positional Artifacts Check:** The synthesis correctly identifies RoPE/Locality tension but fails to mention **Shortformer (2020)**, which similarly argued for separating positional signal from content, providing a missed opportunity to ground the "Redundancy Conflict" in older literature.

## 4. Targeted Follow-Up Searches

1.  `"Infini-attention" vs "recurrent snapshot retrieval" for SSMs`
2.  `"Differentiable HNSW" graph construction complexity for Transformers`
3.  `"High-pass" positional encoding for length extrapolation`
4.  `Resolution analysis of implicit positional signals in causal-mask transformers`
5.  `"Quest" vs "HiP Attention" - performance on non-local retrieval tasks`

## 5. Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ASSR (Addressable SSM Retrieval)** | `survives but needs search` | High collision with RetNet/Infini-attention. | *Infini-attention* (Munkhdalai et al. 2024) | Evidence that retrieving *intermediate* states is better than the final compressed state. | Define the "trigger" for snapshot quantization more formally. |
| **Differentiable HNSW Attention** | `not technically meaningful` | Graph construction cost kills the $O(N \log N)$ advantage. | *LSH Reformer* (Kitaev 2020) | Proof of efficient differentiable graph updates. | Switch focus to a *static* HNSW index with learnable projection heads. |
| **SD-PB (Spectral Deconfliction)** | `survives` | Signal resolution of the causal mask for global position. | *NoPE* (Kazemnejad 2023) | Experimental proof that implicit signals scale to 128k+. | Specify the high-pass cutoff frequency $\tau$ relative to $L_{train}$. |
| **Toeplitz Attention Kernels** | `probably already done` | Mathematically equivalent to standard Relative Attention. | *Shaw et al. (2018)*; *AliBi* (Press 2021) | Theoretical distinction from "Relative Bias." | Use a *non-linear* or *learnable kernel* Toeplitz constraint. |
| **Fused Delta-Rule Kernels** | `survives but needs search` | Might be implemented in current Mamba/SSM CUDA kernels already. | *Linear Transformers* (Katharopoulos 2020) | Comparison with current Triton-based Selective Scan kernels. | Identify the specific 90s Delta-rule variant not in current SOTA. |

## 6. Approval Verdict

**APPROVE WITH RESERVATIONS**

The `novelty_ideation` is grounded in high-quality recent evidence (Huang 2024, HiP 2024, LEDiT 2025). The gaps identified are technically sophisticated. However, the **Differentiable HNSW** and **Toeplitz Kernels** proposals suffer from "Theoretic Blindness"—one ignoring implementation cost, the other ignoring existing mathematical equivalencies. 

**Required Actions for Finalizer:**
1.  Downgrade **Differentiable HNSW** to `speculative` unless an $O(N \log N)$ update mechanism is found.
2.  Refine **ASSR** to explicitly contrast with **Infini-attention**.
3.  Promote **SD-PB** as a "High-Confidence" spinoff given the high evidence support in the 2025 LEDiT findings.