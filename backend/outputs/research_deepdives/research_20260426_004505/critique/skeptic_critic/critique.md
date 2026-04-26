# critique.md

## Blocking Issues
*None. The deep dive is structurally sound and covers the necessary breadth (Scaling, Experiments, and Lineage).*

## Major Issues

1.  **The "Death by Gating" Paradox (Efficiency vs. Overhead):** Across all three syntheses, there is a systemic tendency to propose a "lightweight" secondary mechanism (gating networks, entropy estimators, convolutional mask generators, spectral probes, or dual-stream controllers) to solve efficiency problems. The investigators acknowledge this as a "contradiction," but the proposals themselves do not solve it; they merely rename it. If every "efficient" architecture requires a new sub-network to decide what to compute, the net FLOP savings may be negligible or negative.
    *   *Affected Artifact:* All Proposal Candidates (MoAA, ED-DRP, GLGA, SFGA, IL-LA).
    *   *Failure Mode:* Overlooking the constant-factor overhead and kernel launch latency of the "decision" mechanism.
    *   *Repair Action:* Proposals must include a formal complexity analysis that accounts for the $O(f(n))$ cost of the gating/estimation mechanism itself.

2.  **Mathematical Vagueness in "Single-Pass Non-Causal SSMs":** The proposal for a single-pass non-causal SSM is a massive claim. The "Technical Mechanism" (asymmetric state updates) is currently a hand-wave. In SSM theory, non-causality usually implies either a dual-pass (doubling cost) or a global convolution (which is $O(N \log N)$ but mathematically distinct from the recurrence being optimized).
    *   *Affected Artifact:* Proposal Candidate: Single-Pass Non-Causal SSM.
    *   *Failure Mode:* Attempting to bypass the fundamental causality-efficiency trade-off without a rigorous mathematical derivation.
    *   *Repair Action:* The investigator must perform a "Mathematical Feasibility" search to find if an asymmetric $A$ or $B$ matrix in the SSM state equation can actually achieve bidirectional context in one scan without reverting to $O(N^2)$.

3.  **Categorical Drift (Architecture vs. Evaluation):** Several "Novelty Proposals" are actually "Evaluation Protocols." `ASD` (Attention Stability Diagnostic) and `Intrinsic Spectral Filtering` are not new architectures or algorithms; they are empirical studies of existing ones. In a `novelty_ideation` mode, these should be categorized as "Research Programs" rather than "Spinoff Proposals."
    *   *Affected Artifact:* `ASD` and `Intrinsic Spectral Filtering`.
    *   *Failure Mode:* Mistaking a "question to ask" for a "thing to build."
    *   *Repair Action:* Reframe these as *methods to induce* stability/filtering (e.g., a "Stability-Regularized Training Objective") rather than just observing them.

## Minor Issues
1.  **Collision Ambiguity in IL-LA:** The investigator notes a "High" collision risk with LaplacianFormer but still promotes the idea. If the global part is already solved by LaplacianFormer, the proposal must explicitly define the *interaction* between the local and global streams to ensure it isn't just "LaplacianFormer + a sliding window."
2.  **Hardware/Software Interface Gap:** `MoAA` assumes we can switch kernels on the fly. On modern GPUs, kernel launch overhead is the primary bottleneck for small-to-medium sequences. The proposal needs to address "Batch-level" vs "Token-level" switching.

## Targeted Follow-Up Searches
1.  **Complexity/Overhead Check:** `“overhead of lightweight gating networks in sparse transformers”`, `“Triton kernel launch latency vs computation savings”`.
2.  **Mathematical Verification:** `“asymmetric state-space models bidirectional context single pass”`, `“non-causal recurrence math”`.
3.  **Collision/State-of-the-Art:** `“learned structural sparsity transformer convolution”`, `“joint rank-precision quantization entropy-guided”`.

## Spinoff Proposal Pressure Test

| Proposal | Verdict | Main novelty risk | Closest collision paper | Missing evidence | Concrete repair |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MoAA** | `probably already done` | Hardware latency kills the gain. | ASSENet (2024) / FlashAttention-based sparsity. | Empirical kernel-switching overhead data. | Shift focus to *block-level* kernel selection to minimize launch frequency. |
| **ED-DRP** | `survives` | Precision $\neq$ Rank. | MLoRQ (2025) / TALE (2025). | Correlation between entropy and quantization error. | Define the mapping function $f(\text{entropy}) \to (r, b)$ rigorously. |
| **ASD** | `not technically meaningful` | It's an evaluation metric, not a novelty. | N/A (It's a diagnostic). | N/A | Reframe as a "Stability-aware Loss Function." |
| **GLGA** | `survives but needs search` | Is a conv-mask actually cheaper than a score-mask? | GCAT (2025). | Comparative FLOP analysis of mask-gen vs thresholding. | Define the convolutional topology as a "structural inductive bias." |
| **Non-Causal SSM** | `speculative` | Mathematical impossibility of single-pass bidirectionality. | VSSD (2024) / Dual-path Mamba. | Proof sketch for single-scan non-causal recurrence. | Ground the mechanism in specific asymmetric state-update math. |
| **Intrinsic Filtering** | `too vague` | Observational study, not an invention. | Momentum Attention (2026). | N/A | Reframe as "Frequency-Aware Attention Training." |
| **LCA** | `survives` | Could be redundant with Registers. | Darcet et al. (Registers). | Evidence that LCA is "proactive" vs "reactive." | Contrast "Coordinate Manifold" vs "Input Token" properties. |
| **SFGA** | `speculative` | DCT probe overhead. | FANet (2025). | Latency/Complexity of real-time DCT in Transformer blocks. | Limit DCT application to specific frequency bands. |
| **IL-LA** | `survives but needs search` | LaplacianFormer overlap. | LaplacianFormer (2026). | Clear distinction of the "Local Stream" mechanism. | Formalize the "Injection" part of the hybrid mechanism. |

## Approval Verdict
**approve-with-reservations**

*Reasoning:* The syntheses are high-quality and the literature buckets are well-populated. However, the "Novelty" is currently leaning too heavily on "adding a controller/gate/mask," which threatens the very efficiency it seeks to provide. The investigators must pivot from "how to decide what to compute" to "how to design structures that are inherently efficient/stable/injective." Proceed only if the next stage prioritizes the **Mathematical Feasibility** and **Hardware Overhead** checks identified above.