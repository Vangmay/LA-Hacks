# Findings



## Finding: Foundational Recurrence vs. Attention Disruption

- Claim: The Transformer explicitly claims to dispense with recurrence entirely to achieve parallelization, implicitly framing sub-quadratic sequence models (RNNs) as a predecessor to be replaced.
- Confidence: high
- Evidence:
  - 204e3073870fae3d05bcbc2f6a8e263d9b72e776 / 'Attention is All you Need' / 2017 / seed_metadata
- Why it matters: This serves as the prosecution baseline. If current 'sub-quadratic' scaling methods (like SSMs or Linear Attention) achieve their efficiency by reintroducing recurrence or state-space updates, they may be mathematically equivalent to the systems the Transformer claimed to obsolete.
- Caveat: The paper acknowledges that attention can be seen as a way to relate far-apart positions, but characterizes prior work like ByteNet and ConvS2S as having O(N) or O(log N) path lengths, whereas attention is O(1).


## Finding: Locality-Driven Sub-Quadratic Scaling Constraints

- **Claim**: Modern sub-quadratic Transformers (e.g., HiP) rely on the 'attention locality' hypothesis—that tokens close in index space share similar attention scores—to enable $O(T \log T)$ pruning.
- **Confidence**: high
- **Evidence**:
  - `428c6bd657229d4f3360b5f5920ad3609739ecdc` (HiP, 2024, relevance_search)
- **Why it matters**: If this 'locality' assumption fails (e.g., in complex code base reasoning or non-linear multi-document retrieval where relevant indices are scattered randomly), the tree-search pruning mechanism will likely fail to retrieve critical long-range dependencies, creating a performance floor for sub-quadratic models.
- **Caveat**: The 'attention locality' property may be an artifact of absolute or rotary positional embeddings rather than an inherent property of the task themselves; models without local bias might break this optimization.


## Finding: Mathematical Equivalence of Linear Transformers and 1990s RNNs

- Claim: Linearized attention mechanisms are formally equivalent to Fast Weight Programmers (FWPs) from the early 1990s.
- Confidence: high
- Evidence:
  - 1a703f08da01cf737cce3fb9064259b3f4b44e9c / 'Linear Transformers Are Secretly Fast Weight Programmers' / 2021 / closest_prior_work
  - 9c71d178705989cd4371f8e760508f11b18a4bb4 / 'Practical Computational Power of Linear Transformers' / 2023 / recent_followups
- Why it matters: This severely constrains the 'novelty' of current sub-quadratic scaling efforts. Most methods that linearize the O(N^2) softmax into an O(N) update are essentially re-parameterizing 30-year-old state-space or fast-weight theories. The 'novelty' belongs to the training efficiency (parallelism) rather than the sequence modeling mechanism itself.
- Caveat: While mathematically equivalent, the modern versions benefit from hardware-aware kernels and massive scale that the 1992 versions lacked, which might be a 'functional novelty' despite theoretical equivalence.


## Finding: Convergence of Attention Pruning and Vector Retrieval

- Claim: Modern sub-quadratic 'training-free' attention mechanisms are functionally equivalent to approximate k-Nearest Neighbor (Ak-NN) search algorithms on the KV cache.
- Confidence: high
- Evidence:
  - 428c6bd657229d4f3360b5f5920ad3609739ecdc / 'Hierarchically Pruned Attention (HiP)' / 2024 / recent_followups
  - 11e420bbcd5fce960e737318a8d625095bb61a6a / 'Approximate Diverse k-nearest Neighbor Search' / 2025 / recent_followups
- Why it matters: This collapses the distinction between 'Retrieval-Augmented Generation' (external) and 'Sub-Quadratic Attention' (internal). If attention is just k-NN, then novelty in sub-quadratic scaling may be reduced to known advancements in vector database indexing (HNSW, IVFPQ) rather than new neural architectures.
- Caveat: The 'novelty' may reside in the differentiable integration of these indices into the backpropagation path, which classical Ak-NN lacks.


## Finding: Practical vs Theoretical Long-Context Gap in SSMs

- **Claim**: Sub-quadratic State-Space Models (SSMs) and linear recurrent families fail to match Transformer retrieval accuracy on non-local tasks (e.g., Needle-in-a-Haystack) despite theoretical infinite context support.
- **Confidence**: high
- **Evidence**:
  - `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (Huang, 2024, context-extrapolation critique)
- **Why it matters**: This finding exposes a fundamental 'inductive bias' failure: theoretical sub-quadratic scaling does not solve the retrieval quality bottleneck. It suggests that compressed states in SSMs lose the 'addressability' that explicit KV-caches provide in Transformers.
- **Caveat**: The failure may be partially attributable to token-positional decay in recurrent states rather than an inherent architectural impossibility.
