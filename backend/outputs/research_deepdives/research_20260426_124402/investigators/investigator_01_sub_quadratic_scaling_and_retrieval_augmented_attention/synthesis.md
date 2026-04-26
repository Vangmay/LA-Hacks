# Synthesis Report: Sub-Quadratic Scaling and Retrieval-Augmented Attention

**Section Question:** How can sub-quadratic architectures overcome the "addressability decay" and "locality traps" that cause performance degradation in long-context retrieval compared to the standard $O(N^2)$ Transformer?

## 1. Subagent Coverage

| Subagent ID | Archetype | Key Zone | Status |
| :--- | :--- | :--- | :--- |
| `subagent_01` | Lineage Auditor | Historical Equivalence | **Complete** |
| `subagent_02` | Gap Synthesizer | Future Bottleneck Mining | **Complete** |

## 2. Literature Buckets

| Bucket | Count | Key Paper IDs |
| :--- | :--- | :--- |
| `seed_metadata` | 1 | `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (Vaswani 2017) |
| `foundational_references` | 1 | `43428880d75b3a14257c3ee9bda054e61eb869c0` (Gehring 2017) |
| `closest_prior_work` | 1 | `1a703f08da01cf737cce3fb9064259b3f4b44e9c` (Schlag 2021) |
| `recent_followups` | 3 | `428c6bd657229d4f3360b5f5920ad3609739ecdc`, `fa2f8963df88d8684b38c33aa59cc3ae0927561b` |
| `critiques_limitations` | 1 | `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (Huang 2024) |

**Missing Buckets:**
- `near_publication_competitors`: Missing explicit coverage of 2019-2020 efficient transformers (e.g., Reformer, Longformer).
- `surveys`: No formal survey papers (e.g., Tay et al. "Efficient Transformers") were explicitly processed.

## 3. Prior vs. Future Work Collision Table

| Mechanism | Prior Work (Pre-2017 / 90s) | Modern "Sub-Quadratic" Successor | Collision Risk |
| :--- | :--- | :--- | :--- |
| **Linear Attention** | Fast Weight Programmers (Schmidhuber 1992) | Linear Transformers (Katharopoulos 2020) | **High**: Mathematically equivalent kernels. |
| **State Compression** | LSTMs / RNN Hidden States | Mamba / SSMs (2024) | **Medium**: Recurrent update vs. Selective Scan. |
| **Pruned Attention** | Convolutional Stacks (Gehring 2017) | HiP Attention (Lee 2024) | **Medium**: "Locality" bias vs. tree search. |

## 4. Research Gaps with Evidence

### Gap 1: The Addressability Decay in Compressed States
- **Evidence:** `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (Huang 2024) identifies that SSMs (Mamba) fail at "Needle-in-a-Haystack" (NIAH) tasks despite theoretical infinite context.
- **Description:** Purely recurrent models lack the "pointer" capability of the explicit KV-cache, failing when retrieval requires precise indexing rather than semantic summary.

### Gap 2: The Locality Trap in Pruning Heuristics
- **Evidence:** `428c6bd657229d4f3360b5f5920ad3609739ecdc` (HiP 2024) assumes "attention locality."
- **Description:** If relevant tokens are scattered randomly (e.g., log file analysis or repo-level code search), locality-based pruning ($O(T \log T)$) creates a performance floor that cannot be bypassed without $O(N^2)$ re-evaluation.

## 5. Proposal Seed Inventory

1. **Addressable State-Space Retrieval (ASSR):** Quantizing SSM snapshots for random-access memory lookup.
2. **Selective Fragment Retrieval Attention:** Dynamically loading fragments into a small quadratic window.
3. **Formal Equivalence analysis (Linear/Gated RNN):** Theoretical deep dive (Prosecutor taste).
4. **Hardware-Aware Fast-Weight Triton Kernels:** Resurrecting 90s delta-rule theory with modern CUDA-fused kernels.
5. **Differentiable HNSW Layer:** Replacing sparse masks with a learnable graph index.

## 6. Rejected or Weak Proposal Seeds

- **Title: Formal Equivalence Analysis of Linear Attention and Gated RNNs**
  - **Reason:** While valuable for clarity, it is primarily analytical/historical. It does not propose a new research *object* (artifact/system/benchmark) but rather an interpretation of existing ones.
- **Title: Selective Fragment Retrieval Attention**
  - **Reason:** Too adjacent to existing "Sliding Window + Global Token" patterns (BigBird). Weakened by the emergence of "Differentiable HNSW" which provides a more robust mechanism for the same goal.

---

## 7. Surviving Proposal Candidates

### Proposal Candidate: Addressable State-Space Retrieval (ASSR)

- **Core novelty claim:** Restores NIAH (Needle-In-A-Haystack) performance to sub-quadratic SSMs by retrieving from a latent-state snapshot bank rather than raw text.
- **Source subagents:** `subagent_02` (Gap Synthesizer).
- **Evidence basis:** `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (Huang 2024 - SSM retrieval failure).
- **Seed-paper dependency:** Vaswani 2017 (for the "addressability" baseline).
- **Difference from seed:** Reintroduces state management to a "non-recurrent" lineage to handle ultra-long sequences where pure attention is too costly and pure recurrence is too lossy.
- **Closest prior-work collision:** Jamba (AI21) - uses full attention blocks. ASSR retrieves *intermediate SSM states*.
- **Closest future-work/SOTA collision:** Mamba-2 (State Space Duality).
- **Technical mechanism:** A quantization-trigger based on state-entropy; when entropy spikes, the SSM "checkpoint" is pushed to a k-NN index. Querying is done via an attention-over-states cross-attention layer.
- **Minimum viable validation:** Performance on NIAH with 128k context using Mamba-2.8B base.
- **Falsification criteria:** If the failure in SSM retrieval is due to "projection loss" (encoding) rather than "state decay" (storage), external state retrieval will not improve accuracy.
- **Confidence:** High (Evidenced by clear SOTA failure in Huang 2024).

### Proposal Candidate: Differentiable HNSW Attention Layer

- **Core novelty claim:** Replaces the $O(N^2)$ attention matrix with a graph-traversal layer that is end-to-end differentiable, achieving $O(N \log N)$ during training.
- **Source subagents:** `subagent_01` (Lineage Auditor), `subagent_02` (Gap Synthesizer).
- **Evidence basis:** `428c6bd657229d4f3360b5f5920ad3609739ecdc` (HiP 2024 - k-NN attention convergence).
- **Seed-paper dependency:** Vaswani 2017 (attention logic).
- **Difference from seed:** Changes the dense dot-product to a navigable small-world graph search within the KV cache.
- **Closest prior-work collision:** Malkov (2018) - HNSW (non-differentiable); Reformer (LSH-based).
- **Closest future-work/SOTA collision:** H2O (Heavy-Hitter Oracle) - uses heuristics, not a differentiable graph.
- **Technical mechanism:** Uses Gumbel-Softmax on edge selection to build a Navigable Small World graph of activations at each layer. Gradients flow through the "best-path" found during graph traversal.
- **Minimum viable validation:** Training a 1B parameter model from scratch on the Pile and comparing perplexity/$O(N^2)$ parity.
- **Falsification criteria:** Gradient vanishing during long-context traversal or search overhead exceeding quadratic cost for $N < 32k$.
- **Confidence:** Medium-High.

---

## 8. Novelty-Risk Matrix

| Proposal | Theoretical Risk | Implementation Risk | Collision Risk |
| :--- | :--- | :--- | :--- |
| **ASSR** | Low (Solid gap) | Medium (Triton scans) | Low (New state focus) |
| **Differentiable HNSW** | High (Gradients) | High (Graph build cost) | Medium (LSH/Sparse) |
| **Fused Delta-Rule Kernels** | Low (Old theory) | Medium (Kernel opt) | High (Schmidhuber labs) |

## 9. Contradictions and Weak Spots
- **Positional Encoding Artifacts:** Subagent 01 noted it is unclear if "attention locality" is an inherent task property or an artifact of RoPE (Rotary Positional Embeddings). If it is an artifact, the "Locality Trap" gap might be solved simply by better positional embeddings rather than architectural changes.
- **Mathematical Equivalence:** The finding that Linear Attention $\equiv$ 1990s RNNs suggests that many "novel" sub-quadratic results may just be better-tuned versions of old architectures, casting doubt on any claim of a "new" sequence modeling paradigm.

## 10. Recommended Next Search
- **Query:** "Effect of RoPE vs Absolute Positional Embeddings on Attention Locality in Transformers."
- **Query:** "Differentiable Hierarchical Navigable Small World (HNSW) for Neural Networks."
- **Focus:** Determining if the "addressability decay" in SSMs can be solved via better gating in the "Selective Scan" rather than external state storage.