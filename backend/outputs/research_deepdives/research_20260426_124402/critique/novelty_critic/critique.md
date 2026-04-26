# Critique: Sub-Quadratic Scaling & Positional Encoding Novelty

- **Critic ID:** `novelty_critic`
- **Date:** 2026-04-26
- **Workspace:** `...\critique\novelty_critic`
- **Research Objective:** `novelty_ideation`

---

## Blocking Issues

1.  **Scope Mismatch in Report 1:** The Report title is "Sub-Quadratic Scaling and **Retrieval-Augmented Attention**," yet the synthesis focuses almost exclusively on SSM/State-Space models and pruning. It misses the intersection of *external* retrieval (RAG) and *architectural* sub-quadratic mechanisms. Without evidence from papers like **RETRO** (Borgeaud et al. 2022) or **Unlimiformer** (Bertsch et al. 2023), the synthesis fails to address how these sub-quadratic architectures merge with explicit retrieval systems.
2.  **Missing "ALiBi" Collision in Report 2:** Proposal "Hard-Constrained Toeplitz Attention Kernels" ignores **ALiBi** (Press et al. 2021). ALiBi is a hard-coded relative positional bias that is essentially a non-learned Toeplitz constraint. Claiming a "Toeplitz Kernel" as a spinoff without distinguishing it from ALiBi makes the proposal potentially obsolete upon arrival.

## Major Issues

1.  **Failure to Account for RMT (Recurrent Memory Transformer):** In the "ASSR" proposal (Report 1), the synthesis cites Huang 2024 as the gap. However, it ignores **RMT (Bulatov et al. 2022/2023)** which already effectively "checkpoints" segments into long-term recurrent memory. The "novelty" of retrieving state-snapshots needs to be specifically contrasted against RMT’s recurrent segment tokens.
2.  **Positional Encoding "Implicit Signal" Resolution:** Report 2 relies on the claim that causal masks provide "implicit global position" (Haviv 2022). However, recent investigations into "NoPE" (No Positional Encoding) architectures suggest that this signal is logarithmic or non-existent in deeper layers. The synthesis needs a targeted check on the *resolution* of this signal to see if it can actually replace explicit PE for global context.
3.  **HNSW Efficiency Paradox:** Proposal "Differentiable HNSW" (Report 1) ignores the construction cost. HNSW is $O(N \log N)$ for *search*, but the *graph construction* during training (where every update changes embeddings and thus the graph neighbors) is likely $O(N^2)$ or higher. The synthesis fails to address the feasibility of re-building or updating the graph-index every SGD step.
4.  **Implicit Bias vs. Explicit Constraint:** Report 2 mentions Yeh (2022) for "equivariance discovery" but fails to check if **Vision Transformers (ViT)** with "Convolutions-as-Attention" (e.g., CvT, Wu et al. 2021) already solve the translation invariance problem. If the goal is "Inductive Bias Restoration," why is this approach better than existing hybrid CNN-Transformers?

## Minor Issues

1.  **Terminology Overlap:** The term "Locality Trap" is used without checking if it's a standard term or a subagent-coined term. If it's a new term, it needs a formal definition relative to "Local Attention" or "Sliding Windows."
2.  **Hardware-Awareness Gap:** The "Fused Delta-Rule Kernels" seed is rejected/ignored, but modern SOTA (Mamba) succeeded specifically because of hardware-aware kernels (Scan). Rejecting modernizing 90s theory might be short-sighted if the reason for previous failure was purely memory-wall constraints.

---

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ASSR (Report 1)** | `survives but needs more search` | Overlap with Recurrent Memory Transformer (RMT). | *Recurrent Memory Transformer* (Bulatov 2022) | Distinction between "Snapshot Retrieval" and "Recurrent Token" memory. | Compare memory overhead of SSM-state storage vs. RAG KV-cache storage. |
| **Diff. HNSW (Report 1)** | `speculative` | Construction cost during training. | *Reformer* (LSH-based search). | Proof that graph updates can be $O(N \log N)$ per step. | Focus on "Lazy Graph Updates" where the index is only refreshed every $K$ steps. |
| **SD-PB (Report 2)** | `survives` | Signal resolution of causal masks. | *LEDiT* (2025) / *NoPE* (2023). | Empirical limit of "Causal Mask Indexing" resolution. | Define a specific "High-Pass" cutoff frequency based on training length $L$. |
| **Toeplitz Kernels (Report 2)** | `probably already done` | Soft vs. Hard constraint distinction. | *ALiBi* (2021) / *T5* (2019). | Evidence that learned Toeplitz functions outperform ALiBi's fixed slope. | Reformulate as a "Non-Linear Toeplitz Function" using Hypernetworks. |

---

## Targeted Follow-Up Searches

1.  **Search Query:** `"Recurrent Memory Transformer" vs "State Space Model" NIAH task performance`
    *   *Reason:* To see if ASSR is already solved by RMT.
2.  **Search Query:** `"Differentiable HNSW" implementation or "learnable graph index" for transformer attention`
    *   *Reason:* To check if the $O(N^2)$ graph construction wall is a solved problem.
3.  **Search Query:** `"Implicit Positional Encoding" resolution limit in NoPE transformers`
    *   *Reason:* To see if the causal mask actually provides granular indices (1, 2, 3...) or just coarse buckets (Early, Middle, Late).
4.  **Search Query:** `"Toeplitz attention" equivariance Yeh 2022 vs ALiBi relative position bias`
    *   *Reason:* To verify the delta between learned parameter-sharing and fixed-bias schemes.

---

## Approval Verdict

**Approve with Reservations.**

The synthesis reports high-quality, modern evidence (2024-2025 papers like LEDiT and HiP), which is excellent. However, the proposals are at high risk of "reinventing the wheel" (ALiBi, RMT) or "theoretical impossibility" (Differentiable Graph Construction during training). The investigator must execute the targeted searches for **RMT** and **ALiBi** to ensure the core novelty claims of ASSR and Toeplitz Attention are not already satisfied by these existing works. Additionally, the "Retrieval-Augmented" portion of Report 1 needs literal "Retrieval" papers to ground the "Augmentation" claim.