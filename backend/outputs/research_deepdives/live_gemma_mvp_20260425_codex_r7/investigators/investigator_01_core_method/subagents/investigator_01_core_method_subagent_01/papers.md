# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Self
- Why it matters: Foundational paper introducing the Transformer architecture, which replaces recurrence and convolutions with attention mechanisms, enabling high parallelization and superior performance in sequence transduction.
- Caveat: Primarily validated on machine translation and constituency parsing; applicability to non-sequential or extremely long-range dependencies requires further investigation.


## Paper: Deep Residual Learning for Image Recognition

- Paper ID: 2c03df8b48bf3fa39054345bafabfeff15bfd11d
- Year: 2015
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Ancestor/Building Block
- Why it matters: Introduced residual connections (skip connections) to mitigate vanishing gradients in deep networks; a critical architectural component used in Transformer blocks to allow information flow across layers.
- Caveat: Developed for computer vision (ResNet), but the principle of identity mapping is fundamental to the Transformer's stability.


## Paper: MSF-DET: Multiscale Spectral Fusion Detection Framework for Low-Light Object Detection in Urban Intelligent Transportation

- Paper ID: 1e1d19c1ace5e206147546655a4ef44094bec371
- Year: 2026
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Orthogonal/Mechanism Example
- Why it matters: Demonstrates the application of 'polarized bilateral linear attention (PBLA)' to achieve linear computational complexity in a computer vision context (object detection). Shows that linear attention mechanisms can be specialized for specific domain needs (low-light/multiscale).
- Caveat: Focused on CV/object detection, not LLM sequence transduction.


## Paper: IRIS: Interpretable Retrieval-Augmented Classification for Long Interspersed Document Sequences

- Paper ID: 43bcbee70b6f143b4df44c3af0488f5772d8cdf7
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Closest-future-work collision
- Why it matters: Addresses long-text processing complexity by combining retrieval (RAG-style) with a linear attention mechanism to aggregate retrieved embeddings. This represents a hybrid approach (Retrieval + Linear Attention) to the long-context problem.
- Caveat: Primary application is classification, not generative sequence transduction.


## Paper: MSA: Memory Sparse Attention for Efficient End-to-End Memory Model Scaling to 100M Tokens

- Paper ID: 51c0861aebcc7042be27d64da9a08f3b939875d5
- Year: 2026
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: High-collision/Recent SOTA
- Why it matters: Proposes 'Memory Sparse Attention' (MSA) to scale context to 100M tokens. Aims to solve precision degradation and latency in hybrid linear/RAG systems by using an end-to-end trainable memory model. This is a direct competitor to the general idea of linear/sparse attention for long context.
- Caveat: Highly recent (2026); mechanism details (end-to-end training of memory) are crucial for determining if it covers the proposed 'kernel-based' or 'low-rank' paths.


## Paper: SLA: Beyond Sparsity in Diffusion Transformers via Fine-Tunable Sparse-Linear Attention

- Paper ID: 806efc65e30ec0854634a404ea0a2950791e9e69
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: High-collision/Mechanism Hybrid
- Why it matters: Proposes 'Sparse-Linear Attention' (SLA) which fuses sparse and linear attention by classifying weights into critical (full), marginal (linear), and negligible (skipped). This provides a concrete technical mechanism for weight-based attention decomposition.
- Caveat: Specifically optimized for Diffusion Transformers (DiT) and video generation latency; applicability to LLM autoregressive decoding may differ.


## Paper: Alleviating Forgetfulness of Linear Attention by Hybrid Sparse Attention and Contextualized Learnable Token Eviction

- Paper ID: c43c714fb65f982264bdbc417f0e9da6954f704a
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: High-collision/Mechanism Example
- Why it matters: Specifically targets the 'forgetfulness' (precision degradation) of linear-attention models by interleaving token mixers with sparse attention and learnable token eviction. It uses a lightweight CNN to adaptively retain critical KV-pairs.
- Caveat: Focuses on 'retrieval-intensive tasks' and uses sliding-window attention combined with eviction; the complexity of the CNN/eviction mechanism must be weighed against the linear benefits.


## Paper: LoLA: Low-Rank Linear Attention With Sparse Caching

- Paper ID: 4b85bd2479cbbca6535159fa0d390697231aec3e
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: High-collision/Mechanism Example
- Why it matters: Proposes a three-tier memory system for linear attention: (i) local sliding window, (ii) sparse global cache for 'difficult-to-memorize' pairs, and (iii) recurrent hidden state for generic pairs. Significantly improves associative recall (pass-key retrieval).
- Caveat: Uses a 'self-recall error metric' to manage memory, which is an additional architectural complexity.


## Paper: Sparse Attention Mechanisms in Large Language Models: Applications, Classification, Performance Analysis, and Optimization

- Paper ID: 137002965ee8893397823dbae54fba629941f64a
- Year: 2024
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: Survey/Classification
- Why it matters: Provides a classification framework (global, local, hybrid) for sparse attention strategies. It confirms that while sparse attention reduces complexity, maintaining performance is the central challenge, pointing towards 'anchor-based' and 'multimodal potential' as future research directions.
- Caveat: Primarily a survey and performance analysis paper, not a novel architecture proposal itself.


## Paper: Understanding Factual Recall in Transformers via Associative Memories

- Paper ID: efd8e78da04749113fd7c50a499a2cc9fe61992d
- Year: 2024
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: Closest-prior-work collision (Theoretical insight)
- Why it matters: Provides theoretical grounding that Transformers (both linear and MLP-based) can function as associative memories. It suggests a trade-off between using value matrices (attention) or MLPs to store facts, which is highly relevant to understanding where 'memory' is actually held in efficient architectures.
- Caveat: Focuses on synthetic factual recall tasks and capacity scaling rather than long-context sequence transduction performance.


## Paper: KV Admission: Learning What to Write for Efficient Long-Context Inference

- Paper ID: 327d3bb056e1456bb96ff711a2ec54317ca61feb
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: High-collision/Mechanism Example
- Why it matters: Introduces 'KV Admission' (WG-KV), a lightweight mechanism that learns to predict token utility *before* cache entry. This shifts the paradigm from post-hoc eviction to proactive admission control, significantly reducing memory usage and improving speed. It provides a concrete precedent for learning-based memory management.
- Caveat: Primarily focuses on the KV cache in standard Transformer-based LLMs rather than the internal associative memory of linear attention models.


## Paper: SAGA: Selective Adaptive Gating for Efficient and Expressive Linear Attention

- Paper ID: da9f32757b5bf7878ad77268a71a38f828b34fc2
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: High-collision/Mechanism Example
- Why it matters: Directly addresses the 'low-rank bottleneck' of linear attention using input-adaptive learnable gates to modulate information aggregation into the KV feature map. This mechanism enhances semantic diversity and alleviates the low-rank constraint, providing a highly relevant precedent for 'gated' or 'rank-aware' attention.
- Caveat: Primarily evaluated on vision tasks (ImageNet) and high-resolution image processing; specific dynamics in LLM text-based sequence transduction need verification.


## Paper: DFTopK: Differentiable Fast Top-K Selection for Large-Scale Recommendation

- Paper ID: 9f01bc4c428ccc30a9127354494d62c296bc7f47
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: Technical Mechanism Inspiration
- Why it matters: Proposes a differentiable Top-K operator with O(n) complexity that avoids sorting-based gradient conflicts. While applied to recommendation, the core technical contribution—a closed-form, linear-time differentiable selection operator—is a highly relevant primitive for implementing 'rank-aware' or 'utility-based' selection in attention mechanisms without the O(n log n) overhead of sorting.
- Caveat: Designed for recommendation systems/ranking; its application to the high-dimensional feature space of LLM attention requires careful scaling considerations.


## Paper: Content Reduction, Surprisal and Information Density Estimation for Long Documents

- Paper ID: 0502ad3507b437af48afb3cd8bb4c2d1875bcbff
- Year: 2023
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: Conceptual/Mechanism Inspiration
- Why it matters: Explores information density using surprisal, entropy, and uniform information density for long documents. This provides a theoretical framework for using 'information density' as a metric for deciding which tokens are critical for the linear attention state, potentially replacing heuristic-based gating with information-theoretic gating.
- Caveat: Primarily a linguistic/informational study, not an architectural proposal for LLMs.
