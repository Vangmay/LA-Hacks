# critique.md

## Blocking Issues
*None identified that prevent the deep dive from proceeding, but a systemic risk regarding hardware-awareness must be addressed before finalization.*

## Major Issues

1.  **The Efficiency Paradox (Systemic across all Investigators):** There is a recurring failure to provide a formal cost-benefit analysis for the "efficiency" mechanisms. `MoAA` (Inv 01), `GLGA` (Inv 02), `SFGA` (Inv 03), and `ED-DRP` (Inv 01) all propose auxiliary modules (gating networks, entropy estimators, spectral probes, convolutional controllers) to save FLOPs. However, none of the syntheses provide a complexity bound for these controllers. If the controller is $O(n)$ or $O(n \log n)$, it may negate the $O(\text{sparse})$ gains. 
    *   **Affected Artifact:** All Spinoff Proposals.
    *   **Failure Mode:** Theoretical efficiency that is negative in practice due to overhead.
    *   **Repair Action:** Every proposal must include a "Complexity Budget" section specifying the asymptotic cost of the mechanism compared to the savings.

2.  **Attribution Ambiguity in Robustness/Stability (Inv 02 & 03):** The proposals `ASD` (Attention Stability Diagnostic) and `Intrinsic Spectral Filtering` assume that attention weight fluctuations are meaningful proxies for model reliability or signal processing capability. However, the literature (and the investigators themselves) acknowledges that FFNs and residual connections carry significant information.
    *   **Affected Artifact:** `ASD` and `Intrinsic Spectral Filtering` proposals.
    *   **Failure Mode:** Measuring the "wrong" part of the model; finding high attention stability while the model fails due to FFN instability.
    *   **Repair Action:** Proposals must include a "Differential Attribution" plan—how to isolate the attention component's contribution to the signal (e.g., via ablation of the attention path vs. the residual path).

3.  **The "Single-Pass" Mathematical Impossibility (Inv 02):** The `Single-Pass Non-Causal SSM` proposal sits on a very thin theoretical ledge. In state-space models, "non-causal" usually implies a look-ahead or a dual-pass (bidirectional) scan. Claiming a "single-pass" bidirectional kernel without re-introducing quadratic complexity or significant constant-factor overhead is a massive claim that lacks a specific mathematical mechanism in the current synthesis.
    *   **Affected Artifact:** `Single-Pass Non-Causal SSM` proposal.
    *   **Failure Mode:** The mechanism is mathematically impossible or just a re-skinned dual-pass.
    *   **Repair Action:** The proposal must move from "modified SSD kernel" to a specific "asymmetric state update" or "look-ahead weighting" definition.

## Minor Issues
1.  **Hardware-Awareness Gap:** `MoAA` (Inv 01) identifies kernel switching as a risk but does not mention specific implementation frameworks (e.g., Triton or CUDA graph management) that could mitigate launch latency.
2.  **Search Granularity:** In `Inv 03`, the "Sink Contradiction" is well-identified, but the search for "geometric necessity vs. computational artifact" needs more formal topological literature to move beyond "speculative."

## Targeted Follow-Up Searches
1.  **Complexity Analysis:** "Asymptotic complexity of lightweight gating networks for sparse attention" and "overhead of real-time entropy estimation in inference."
2.  **Hardware Profiling:** "Kernel launch latency comparison: Triton vs. standard CUDA for varying sequence lengths" to provide empirical grounding for `MoAA`.
3.  **Mathematical Foundation:** "Asymmetric state-space models for non-causal sequence modeling" and "non-monotonic kernel injectivity in linear attention."
4.  **Direct Collision Check:** "Learned structural sparsity transformer" and "convolutional attention topology prediction" (to validate `GLGA`).

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
|---|---|---|---|---|---|
| **MoAA** | `probably already done` | Implementation/Hardware | ASSENet (2024) / FlashAttention | Evidence that kernel switching latency < sparse savings. | Specify a Triton-based implementation strategy. |
| **ED-DRP** | `survives` | Correlation Failure | MLoRQ (2025) | Correlation data between $\text{H}(Attn)$ and quantization error. | Add a "Correlation Validation" step in the min-validation. |
| **ASD** | `speculative` | Attribution Error | Agarwal (2024) | Proof that attention stability $\neq$ FFN stability. | Include a "Residual-Ablation" validation. |
| **GLGA** | `survives but needs more search` | Collision with "Learned Sparsity" | Asadi et al. (2025) | Distinction from "score-based" learned sparsity. | Define the *topological* nature of the mask vs. score masks. |
| **Non-Causal SSM**| `speculative` | Mathematical impossibility | VSSD (2024) | Mathematical definition of "single-pass bidirectional." | Provide a specific asymmetric recurrence formula. |
| **Intrinsic Filter**| `speculative` | Attribution Error | Momentum Attention (2026) | Proof that attention is the primary filter. | Use "Attention-only" vs "Full-Model" SNR tests. |
| **LCA** | `survives` | Implementation Complexity | Registers (2023) | Proof that proactive anchors > reactive registers. | Benchmark LCA against Register-ViT on stability. |
| **SFGA** | `survives but needs more search` | DCT Overhead | Swin / FANet | Complexity of DCT-based spectral probe. | Define a "Fast-DCT" or "Approximated Spectral" probe. |
| **IL-LA** | `not actually novel` | High Collision | LaplacianFormer (2026) | Distinction from Laplacian's global kernel. | Focus specifically on the *Local* stream's precision. |

## Approval Verdict
**approve-with-reservations**

*Reasoning:* The syntheses are high-quality and the proposals are sophisticated. However, the entire set of spinoffs suffers from a "systemic efficiency oversight." They propose complex controllers to save computation without acknowledging the cost of those controllers. The `Non-Causal SSM` and `Intrinsic Filtering` proposals are currently too speculative to be considered high-confidence research directions. If the investigators address the **Complexity Budget** and **Differential Attribution** requirements, this can be promoted to `approve`.