# Critique: Sub-Quadratic Scaling and Inductive Bias Synthesis

- **Critic ID:** `coverage_critic`
- **Critique Lens:** `coverage and search recall`
- **Workspace:** `C:\Users\ishur\OneDrive\Desktop\VS_Code_Projects\LA-Hacks\backend\outputs\research_deepdives\research_20260426_124402\critique\coverage_critic`
- **Research Objective:** `novelty_ideation`

---

## Blocking Issues

1.  **Missing "Infini-attention" / Segmented Retrieval Baselines:**
    In the `Sub-Quadratic Scaling` report, the **ASSR** proposal (Addressable State-Space Retrieval) fails to account for **Infini-attention (MvA et al., April 2024)** or **Recurrent Memory Transformer (RMT)**. Infini-attention specifically addresses the retrieval of compressed local states (KV-states) using a compressive memory retrieved via attention. The synthesis does not explain why retrieving *SSM states* is fundamentally different from retrieving *compressed KV states* from a fixed-size memory buffer. This lacks the "novelty pressure" required to distinguish it from current Google SOTA.
    *   **Repair Action:** Perform a direct comparison search between "Infini-attention" and "SSM state snapshot retrieval."

2.  **Absence of Efficient Transformer (2020) Surveys:**
    The report acknowledges missing the `surveys` bucket (e.g., Tay et al., 2020). This is a blocking issue because the **Differentiable HNSW** proposal is highly likely to collide with **Reformer (LSH Attention)** or **Routing Transformer**. Without documenting why graph-based navigation is superior to LSH-based bucketing (which already achieves $O(N \log N)$), the proposal is technically unanchored.
    *   **Repair Action:** Search for "Graph-based vs LSH-based sparse attention" to establish a technical baseline.

## Major Issues

3.  **ALiBi (2021) Collision in Toeplitz Proposal:**
    The `Inductive Bias` report proposes **Hard-Constrained Toeplitz Attention** but fails to reference **ALiBi (Attention with Linear Biases, 2021)** as a "closest prior work." ALiBi essentially imposes a static Toeplitz-like penalty on the attention matrix. The synthesis needs to prove why a *learned* or *hard-constrained* Toeplitz kernel is different from the high-performing fixed Toeplitz bias in ALiBi.
    *   **Repair Action:** Adversarial search: "Is learned Toeplitz bias more effective than ALiBi for length extrapolation?"

4.  **Implicit Mask Frequency Resolution:**
    The **SD-PB (Spectral Deconfliction)** proposal assumes the causal mask provides a "globally low frequency" signal. However, there is no evidence cited regarding the *resolution* of this signal. If the implicit signal is only "approximate" (e.g., distinguishing only context blocks rather than exact indices), the proposal for a high-pass RoPE would destroy the model's ability to count or reason about long-distance exact pointers.
    *   **Repair Action:** Targeted search for "resolution of implicit positional encoding in causal transformers."

## Minor Issues

5.  **GQA/MLA Impact on Addressability:**
    The `Sub-Quadratic` report discusses "addressability decay" but ignores the industry merge toward **Grouped Query Attention (GQA)** and **Multi-head Latent Attention (MLA)**. These methods already "compress" the state. The ASSR proposal needs to specify if it is retrieving from these compressed latent heads or the raw SSM weights.
    *   **Repair Action:** Clarify the mechanism of ASSR in the context of DeepSeek-V2 style latent attention.

6.  **Locality Trap vs. Longformer:**
    The "Locality Trap" gap (Gap 2 in Synthesis 1) mentions HiP (2024) but fails to mention that this was the core motivation for **Longformer (2020)** and **BigBird**. The proposal `Selective Fragment Retrieval Attention` was rejected, which is correct, but the survivor `Differentiable HNSW` must explicitly address the "scattered relevant tokens" problem better than the "Global Tokens" used in Longformer.

---

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ASSR (Addressable State-Space)** | `probably already done` | It is functionally identical to Infini-attention but with an SSM backbone. | Infini-attention (MvA 2024); RMT (Burtsev) | Evidence that SSM states are "more addressable" than KV-states. | Search: "Retrieval over latent SSM snapshots vs Compressive KV." |
| **Differentiable HNSW Attention** | `survives but needs more search` | Training a graph-build step is $O(N^2)$ without a clever heuristic, defeating the sub-quadratic goal. | Reformer (LSH); Routing Transformer | Proof of differentiability through HNSW entry points. | Search: "Differentiable Graph Construction in Attention." |
| **SD-PB (Spectral Deconfliction)** | `survives` | **High potential.** Specifically targets the redundancy between RoPE and Implicit Bias. | NoPE (2023); LEDiT (2025) | Empirical evidence that implicit signals are low-frequency. | Search: "FFT of attention weights in PE-free models." |
| **Hard Toeplitz Attention** | `not actually novel` | Soft Toeplitz biases (Shaw, T5, AliBi) are well-explored. Hard constraints usually hurt performance. | ALiBi (2021); Yeh et al. (2022) | Evidence that hard constraints outperform soft biases. | Rename to "Dynamically Filtered Toeplitz" and focus on LTI filters. |
| **Fused Delta-Rule Kernels** | `survives but needs more search` | Might have been solved by NVIDIA/Tri Dao (Mamba-2/SSD). | Mamba-2 (State Space Duality, 2024) | Verification of delta-rule equivalence in SSD. | Search: "Delta rule implementation in Mamba-2 Triton kernels." |

---

## Targeted Follow-Up Searches

1.  `"Infini-attention" vs "Memory-Augmented SSM" retrieval performance`
2.  `"resolution of implicit positional signal in causal mask" + "needle in a haystack"`
3.  `"Differentiable Navigable Small World" neural network layers`
4.  `"Spectral analysis" + "RoPE" + "high-pass filter" for length extrapolation`
5.  `"Linear Time-Invariant" constraints for Self-Attention logit matrices`

---

## Approval Verdict

**Approve with Reservations.**

The `novelt_ideation` is grounded in high-quality modern citations (LEDiT 2025, Huang 2024), but the proposals are currently "collision-heavy." **ASSR** and **Toeplitz Attention** risk being restatements of Infini-attention and ALiBi, respectively. **SD-PB** is the most promising survivor but requires a feasibility check on the "resolution" of mask signals. The sub-quadratic synthesis must explicitly address the 2020-2021 "Efficient Transformer" era to ensure it isn't reinventing LSH/Sparse-Attention under a new "Graph" label.