# critique.md

## Blocking Issues
*None. The syntheses are high-quality, well-structured, and maintain high technical density.*

## Major Issues

1.  **Metric vs. Mechanism (Synthesis 1 - Faithfulness Score):**
    *   **Affected Artifact:** Proposal Candidate: "Quantifying Attention Faithfulness via Causal Intervention".
    *   **Failure Mode:** The proposal is a **diagnostic metric**, not a **research direction/spinoff mechanism**. A research proposal in this context should aim to *solve* unfaithfulness, not just measure it. As written, it is a benchmarking paper, which is a lower tier of novelty than the other technical architecture/optimization proposals.
    *   **Evidence Weakness:** It lacks a "technical mechanism" that uses the score to improve the model (e.g., using the score as a loss term or a pruning signal).
    *   **Concrete Repair:** Reframe the proposal to: *"Causal-Intervention-Guided Attention Regularization"*. Use the faithfulness score as a penalty term in the loss function to force attention weights to align with causal importance during training.

2.  **Architectural Redundancy (Synthesis 2 vs. Synthesis 3):**
    *   **Affected Artifact:** The entire research deep dive structure.
    *   **Failure Mode:** Synthesis 2 (Scaling & Hybridization) and Synthesis 3 (Related Work & Novelty) overlap significantly. Both cover the Transformer-SSM hybridization space. This creates a "split brain" effect where different subagents are essentially proposing variations of the same idea (Soft routing vs. Entropy-gated routing) without a unified taxonomy.
    *   **Evidence Weakness:** The "Research Gaps" in Synthesis 3 partially repeat the "Research Gaps" in Synthesis 2.
    *   **Concrete Repair:** Merge the hybridization discussions. Synthesis 2 should focus on the *mechanics of hybridization* (SSM vs. RC), and Synthesis 3 should focus on the *structural/topological limits* (Routing Absorption, Topology-blindness).

3.  **Implementation Blindness (Synthesis 2 - Continuous Hybridization):**
    *   **Affected Artifact:** Proposal Candidate: "Continuous/Soft Hybridization of Transformers and SSMs".
    *   **Failure Mode:** The proposal ignores the **"Kernel Switching Penalty"**. In modern LLM acceleration, the bottleneck is often not FLOPs but memory movement/IO between specialized kernels (e.g., switching from a highly optimized FlashAttention kernel to a specialized SSM/Mamba kernel). A "soft" mixture requires computing both paths or executing complex branching, which may destroy the very efficiency the hybrid aims to achieve.
    *   **Evidence Weakness:** No mention of hardware-aware constraints or unified kernel feasibility.
    *   **Concrete Repair:** Add a specific requirement to the "Technical Mechanism": The gating must be implemented via a **unified CUDA kernel** that computes both contributions in a single pass to minimize memory IO overhead.

## Minor Issues

1.  **Incomplete Metadata (Synthesis 2):**
    *   **Affected Artifact:** Subagent 03 coverage in the "Research Gaps" section.
    *   **Failure Mode:** The investigator notes an "Error on specific paper ID" (9e06fa...). This is a violation of the "durable knowledge" rule. 
    *   **Concrete Repair:** The investigator must perform a `get_paper_metadata` call to resolve that ID before finalizing the synthesis.

2.  **Vague "Fidelity" Definition (Synthesis 1 - Constrained Policy):**
    *   **Affected Artifact:** Proposal Candidate: "Constrained Policy Optimization".
    *   **Failure Mode:** "Semantic fidelity" is not a formal technical term. 
    *   **Concrete Repair:** Specify the fidelity metric (e.g., "KL-divergence from the teacher model's distribution" or "BERTScore similarity to the ground-truth sequence").

## Targeted Follow-Up Searches

1.  **Hardware-Efficiency Search:** `query: "unified kernel attention and SSM" OR "fused attention-SSM kernel implementation"` to validate the feasibility of "Continuous Hybridization" and "SEG-TKR".
2.  **Routing Absorption Verification:** `query: "routing absorption in mixture of experts" AND "transformer gating stability"` to ensure "SEG-TKR" is actually addressing a distinct problem from standard MoE absorption.
3.  **Causal Reward Complexity:** `query: "cost of causal intervention in reinforcement learning" OR "differentiable causal mediation loss"` to assess the feasibility of "CO-SHT".

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
|---|---|---|---|---|---|
| **DITA** | survives but needs more search | Surprisal noise as gradient signal | KV Admission | Correlation between surprisal and semantic retention | Test if surprisal is a stable gradient in autoregressive settings. |
| **Faithfulness Score** | too vague | It is a metric, not a method | N/A | A mechanism to *act* on the score | Reframe as "Causal-guided weight regularization". |
| **Constrained Policy** | speculative | Standard Lagrangian optimization | DPO / CPL | Unique "fidelity" signal vs. standard KL | Define the exact divergence term that distinguishes it from DPO. |
| **Continuous Hybrid** | survives | Kernel switching/IO overhead | MambaFormer | Hardware latency of non-discrete routing | Add a requirement for a unified, fused kernel. |
| **ASUR** | survives | Manifold instability | Echo State Transformer | Stability of $O(L)$ updates with attention | Include a "manifold stability" proof sketch in the proposal. |
| **Hierarchical NLP** | probably already done | Parallel local-global is common | Jamba / Local-window attention | Distinction from standard multi-scale architectures | Specify how the "fusion" layer differs from standard cross-attention. |
| **SEG-TKR** | survives | Implementation complexity | Sparsifiner | Stability of block-wise topology learning | Specify a "coarse-to-fine" training schedule to stabilize topology. |
| **CO-SHT** | speculative | Reward sparsity/complexity | VERITAS | Computational cost of causal rewards | Propose a way to approximate the causal reward without full intervention. |

## Approval Verdict
**approve-with-reservations**

*The syntheses are exceptionally strong and the proposal generation is highly creative. However, the distinction between "diagnostic metrics" and "architectural proposals" must be strictly enforced, and the massive technical hurdle of kernel-switching overhead in hybrid models must be explicitly addressed in the technical mechanisms to move these from "speculative" to "high-confidence" candidates.*