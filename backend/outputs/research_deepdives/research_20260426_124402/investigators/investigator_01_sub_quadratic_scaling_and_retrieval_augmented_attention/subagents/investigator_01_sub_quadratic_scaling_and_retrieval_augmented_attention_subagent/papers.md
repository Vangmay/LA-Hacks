# Papers



## Paper: Attention is All you Need (Seed)

- **Paper ID**: `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (ARXIV:1706.03762)
- **Year**: 2017
- **Source bucket**: seed_metadata
- **Found by**: resolve_arxiv_paper
- **Relation to seed**: Self (Seed Paper)
- **Why it matters**: Introduces the Transformer architecture using multi-head self-attention. This mechanism has $O(N^2)$ scaling, which serves as the primary bottleneck for long-context sequences and motivates the search for sub-quadratic and retrieval-augmented alternatives.
- **Caveat**: While it revolutionized parallelization, the quadratic memory/compute complexity for long sequences is the exact limitation later work (e.g., Sparse Attention, Reformer, FlashAttention) aims to solve.


## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Self (Seed Paper)
- Why it matters: Establishes the standard Transformer architecture based on O(N^2) softmax attention. It is the baseline against which all sub-quadratic and retrieval-augmented scaling claims in this deep dive must be prosecuted for novelty or historical equivalence.
- Caveat: Massive citation count may obscure technically closer prior work in linear attention or fast weights that the authors did not cite.


## Paper: Attention is All you Need

Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
Year: 2017
Source bucket: seed_metadata
Found by: resolve_arxiv_paper
Relation to seed: self
Why it matters: This paper is the foundational architecture for the Transformer. Its core mechanism—Multi-Head Self-Attention—possesses a quadratic complexity $O(N^2)$ with respect to sequence length N. This computational wall prevents standard Transformers from processing very long contexts, necessitating the sub-quadratic and retrieval-augmented innovations investigated in this section.
Caveat: The paper was published before the explosion of 'Long Context' research; thus, it does not explicitly discuss retrieval-augmented attention or modern sub-quadratic alternatives like Linear Attention or State Space Models (SSMs).


## Paper: Convolutional Sequence to Sequence Learning

- Paper ID: 43428880d75b3a14257c3ee9bda054e61eb869c0
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Direct performance/architecture competitor cited for its parallelizability.
- Why it matters: Gehring et al. (2017) utilized CNNs to achieve sub-quadratic (linear) scaling in sequence modeling before the Transformer became dominant. Its use of attention modules in the decoder provides a bridge between pure convolutional modeling and the modern Transformer. Essential for understanding if 'new' sub-quadratic scaling methods are just returning to convolutional/sliding-window inductive biases.
- Caveat: Relies on Gated Linear Units (GLUs), which have seen a resurgence in modern Transformer variants like PaLM and LLaMA.


## Paper: Hierarchically Pruned Attention (HiP)

- **Paper ID**: `428c6bd657229d4f3360b5f5920ad3609739ecdc` (ARXIV:2406.09827)
- **Year**: 2024
- **Source bucket**: relevance_search
- **Found by**: paper_relevance_search
- **Relation to seed**: Direct architectural extension addressing the $O(N^2)$ bottleneck identified in Vaswani (2017).
- **Why it matters**: It achieves sub-quadratic complexity $O(T \log T)$ using a tree-search-like algorithm to estimate top-k key tokens via 'attention locality'. This validates the feasibility of my earlier proposal seed regarding dynamic internal retrieval/pruning and suggests a 'locality' assumption that could be a point of failure in non-sequential data.
- **Caveat**: Being training-free, its performance relies on the quality of a pre-trained model's existing attention distributions; it might not generalize to architectures with highly uniform or non-local attention maps.


## Paper: Linear Transformers Are Secretly Fast Weight Programmers

- Paper ID: 1a703f08da01cf737cce3fb9064259b3f4b44e9c
- Year: 2021
- Source bucket: closest_prior_work
- Found by: paper_relevance_search
- Relation to seed: Formal competitor/equivalence analysis of later-year linear models to pre-Transformer work.
- Why it matters: Schlag et al. (2021) confirm the 'Prosecutor' hypothesis: linearized self-attention is mathematically equivalent to 1990s fast weight controllers. It identifies a fundamental memory capacity limitation in purely additive linearized attention and proposes a delta-rule update (reinforcing the recurrence connection). This effectively 'shrinks' the novelty of sub-quadratic attention to being a re-branding of known RNN mechanisms.
- Caveat: Authored by Schmidhuber's group, which has a known strategic interest in highlighting pre-Transformer lineage.


## Paper: Hierarchically Pruned Attention (HiP)

- Paper ID: 428c6bd657229d4f3360b5f5920ad3609739ecdc
- Year: 2024
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Sub-quadratic scaling descendant ($O(T \log T)$).
- Why it matters: Lee et al. (2024) utilize 'attention locomotion' and tree-search to find top-k tokens for retrieval. From a 'Prosecutor' perspective, this is a hardware-optimized implementation of hierarchical k-Nearest Neighbors (k-NN) or cluster-based retrieval. It bridges the gap between pure attention and external retrieval systems by treating the internal KV cache as a searchable vector database.
- Caveat: Claimed to be training-free, which suggests the 'novelty' is purely algorithmic/data-structural rather than architectural.


## Paper: How Well Can a Long Sequence Model Model Long Sequences?

- **Paper ID**: `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (ARXIV:2407.08112)
- **Year**: 2024
- **Source bucket**: google_scholar_search / relevance_search
- **Found by**: paper_relevance_search
- **Relation to seed**: Direct critique of sub-quadratic alternatives (SSMs/RNNs) to the Transformer seed.
- **Why it matters**: Provides crucial evidence that state-space models and linear recurrent models fail on the 'Needle-in-a-Haystack' (NIAH) task and exhibit 'lost-in-the-middle' symptoms despite theoretical infinite context. It establishes that sub-quadratic scaling does not equate to effective long-range retrieval efficiency, highlighting a significant research gap in architectural inductive biases.
- **Caveat**: The study notes that theoretical capabilities are sound but empirical gaps remain, suggesting the failure might be in the training objective or data exposure rather than just the mathematical mechanism.
