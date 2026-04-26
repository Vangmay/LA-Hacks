# Synthesis Report: Inductive Bias Restoration and Positional Encoding Novelty

This report synthesizes investigation into the "pure attention" architecture's departure from classical signal processing and the multi-year trajectory of restoring foundational inductive biases through positional encoding (PE) innovations.

## 1. Section Question
How did the removal of recurrence and convolution in the original Transformer create specific inductive bias gaps, and can modern positional encoding failures (extrapolation limits) be resolved by formally restoring classical signal processing properties like translation invariance and spectral decomposition?

## 2. Subagent Coverage Table

| Subagent ID | Archetype | Research Zone | Key Contribution |
| :--- | :--- | :--- | :--- |
| `subagent_01` | Lexical Archeologist | Mathematical Lineage | Linked RPE to Toeplitz/LTI filter theory; identified Yeh (2022) as a theoretical collision for equivariance discovery. |
| `subagent_02` | Void Cartographer | SOTA Failures | Identified the "Redundancy Tension": Causal masks provide implicit global position, while explicit PEs like RoPE cause OOD failure in long contexts (LEDiT, 2025). |

## 3. Literature Buckets

### A. Foundational & Prior Work (Pre-2018)
*   **Vaswani et al. (2017) [ARXIV:1706.03762]**: The seed. Discarded recurrence/convolutions for global attention. Introduced Sinusoidal APE, lacking relative/local bias.
*   **Shaw et al. (2018)**: First Relative Positional Encoding (RPE). Restored local shift-invariance using a clipping distance $k$.

### B. Convergence & Modern Follow-ups (2022-2025)
*   **Haviv et al. (2022)**: Proved causal Transformers learn "implicit" absolute position without any explicit PE.
*   **Yeh et al. (2022)**: Showed equivariance (shift-invariance) can be "discovered" as a learned Toeplitz parameter-sharing scheme.
*   **Baron et al. (2023)**: Proved Vision Transformers can be PE-free if using SSM layers, which satisfy translation/permutation-invariance.
*   **Zhang et al. (2025) (LEDiT)**: Claimed explicit PEs (RoPE) are the "primary obstacle" to length extrapolation because they force models to handle OOD coordinate values.

## 4. Closest Prior/Future Collision Table

| Target Mechanism | Closest Prior Work | Closest Future/SOTA Work | Collision Risk |
| :--- | :--- | :--- | :--- |
| **Toeplitz Bias** | Shaw (2018) | Yeh et al. (2022) | High: Equivariance discovery is known, but dynamic sequence application is open. |
| **Implicit Global Position** | Haviv (2022) | LEDiT (2025) | Moderate: Recent surge in "NoPE" (No Pos-Encoding) interest. |
| **Frequency Scaling** | Su et al. (2021) (RoPE) | NTK-Aware RoPE / YaRN | High: Heuristic scaling is saturated; learned gating is common. |

## 5. Research Gaps with Evidence
1.  **The Redundancy Conflict**: Models use RoPE to provide global position that the causal mask already implicitly encodes (Haviv, 2022). This redundancy causes extrapolation crashes when the explicit global grid reaches unseen values (Zhang, 2025).
2.  **Formal LTI Gap**: While RPE (T5, ALiBi) approximates shift-invariance, few architectures enforce it as a hard Toeplitz constraint derived from Linear Time-Invariant (LTI) system theory.
3.  **Spectral Mismatch**: Current PEs treat all frequencies of the position signal equally during scaling, failing to "hand off" global context to the implicit mask signals.

---

## 6. Proposal Candidate: Spectral Deconfliction of Positional Bias (SD-PB)

*   **Core novelty claim**: Resolves the Transformer length-extrapolation wall by restricting explicit Positional Encodings (RoPE) to *locally high frequencies* (relative ordering) while relying on the causal mask's implicit signal for *globally low frequencies*.
*   **Source subagents**: `subagent_02` (Void Cartographer)
*   **Evidence basis**: LEDiT (2025) claims explicit PE is the primary barrier to OOD length scaling. Haviv (2022) proves causal masks provide implicit global position.
*   **Seed-paper dependency**: Vaswani (2017) Sinusoids target both local and global; RoPE (Su, 2021) does the same but fails when the "global" part of the grid hits OOD coordinates.
*   **Difference from seed**: Replaces the unified positional signal with a split-spectrum approach: High-Pass RoPE + Implicit Global Position.
*   **Closest prior-work collision**: NoPE (removes PE entirely), ALiBi (local linear bias).
*   **Closest future-work/SOTA collision**: LEDiT (2025) (no PE in DiT).
*   **Technical mechanism**: **Frequency-High-Pass RoPE**. Modify the rotary embedding spectrum to zero out frequencies below a threshold $\tau$. This ensures the model uses RoPE for sharp local syntax/relative order but "senses" global context via the causal predecessor count, which naturally scales to infinite length.
*   **Minimum viable validation**: Train a 1B LLM with High-Pass RoPE vs. standard RoPE. Test on "Passkey Retrieval" at 8x training length.
*   **Falsification criteria**: If the causal mask's implicit signal is too "noisy" to resolve global structure in code or long-form reasoning, the model will fail on global benchmarks regardless of extrapolation ability.
*   **Confidence**: High (supported by 2022-2025 convergence).
*   **Required next searches**: Verify if the causal mask's implicit signal strength degrades in non-softmax or linear attention variants.

## 7. Proposal Candidate: Hard-Constrained Toeplitz Attention Kernels

*   **Core novelty claim**: Explicitly enforces translation equivariance in self-attention by constraining the positional bias matrix to be a formal Toeplitz operator, ensuring the attention mechanism behaves as a sequence of dynamic shift-invariant filters.
*   **Source subagents**: `subagent_01` (Lexical Archeologist)
*   **Evidence basis**: Yeh et al. (2022) (Equivariance discovery); Baron et al. (2023) (SSM-based invariance restoration).
*   **Seed-paper dependency**: Reverses the 2017 decision to use "free" APE by re-imposing the structural constraints of convolutions.
*   **Difference from seed**: Moves from "adding sinusoids" to "restricting the attention logit geometry."
*   **Closest prior-work collision**: Shaw et al. (2018) (Relative bias is a soft-learned version of this).
*   **Closest future-work/SOTA collision**: Yeh et al. (2022) (Learned parameter sharing for equivariance).
*   **Technical mechanism**: Impose the constraint $A = QK^T + B$ where $B_{i,j} = \mathcal{T}(i-j)$. $\mathcal{T}$ is a learned continuous function or a structured kernel that models the LTI filter properties. This prevents the model from ever "learning" position-dependent biases that break equivariance.
*   **Minimum viable validation**: Compare parity with CNNs on shift-heavy synthetic tasks (e.g., bit-string pattern matching) where the pattern occurs at arbitrary absolute indices.
*   **Falsification criteria**: If the model requires *breaking* shift-invariance to perform well (e.g., identifying the "beginning" of a document), the hard constraint will degrade performance compared to soft relative biases.
*   **Confidence**: Medium (Strong theory, but soft biases like T5/RoPE might already approximate this "well enough").

---

## 8. Rejected or Weak Ideas

*   **Context-Adaptive Rotary Base Scaling (CARBS)**:
    *   *Reason*: Likely incremental. Modern scaling (YaRN, NTK-aware) already provides robust heuristic interpolation. A learned MLP for the "base frequency" (10k) adds complexity without a clear evidence-backed gap over existing NTK-scaling.
    *   *Status*: **Speculative/Weak**.
*   **PE-Free LLMs for Everything**:
    *   *Reason*: LEDiT (2025) shows success in Diffusion, but NLP papers (Haviv, 2022) suggest that while PE-free models are "competitive," they lack the high-frequency "sharpness" needed for complex reasoning or code.
    *   *Status*: **Rejected (Too broad; replaced by the SD-PB hybrid proposal)**.

## 9. Novelty-Risk Matrix

| Proposal | Theoretical Novelty | Implementation Risk | Collision Risk |
| :--- | :--- | :--- | :--- |
| **SD-PB** | 5/5 (Redundancy Pruning) | 2/5 (Easy spectrum mod) | 3/5 (LEDiT/NoPE) |
| **Toeplitz Attention** | 4/5 (Hard Mechanism) | 4/5 (Efficient mat ops) | 4/5 (Yeh 2022) |

## 10. Contradictions and Weak Spots
*   **The Implicit Signal Mystery**: There is no mathematical proof of the "resolution" of the causal mask's implicit positional signal. If it is only coarse (e.g., "I am roughly in the middle"), SD-PB will fail on tasks requiring precise absolute indexing.
*   **Equivariance vs. Performance**: The 2017 Transformer specifically *broke* equivariance to allow models to learn context-specific position meanings. Restoring it might be a regression in capacity, even if it helps extrapolation.

## 11. Recommended Next Search
*   Perform an adversarial search for **"Discrete Toeplitz Constraint in Relative Attention."** Check if anyone has moved the "Toeplitz Discovery" (Yeh, 2022) specifically into the self-attention logit $B$ as a hard structural constraint.
*   Search for **"Spectral Analysis of RoPE Failure"** to see if the "high-pass" intuition has been empirically tested for length extrapolation already.