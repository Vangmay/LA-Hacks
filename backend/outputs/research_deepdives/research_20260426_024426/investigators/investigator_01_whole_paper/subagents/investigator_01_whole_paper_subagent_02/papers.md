# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed paper
- Why it matters: Introduces the Transformer architecture, replacing recurrence and convolution with self-attention, which has become the standard for modern LLMs.
- Caveat: Focused primarily on sequence transduction/translation tasks.


## Paper: ScatterFormer: Efficient Voxel Transformer with Scattered Linear Attention

- Paper ID: 5cc392b47433b24b0c198e781fee287bede1a575
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (efficient variant)
- Why it matters: Uses Scattered Linear Attention (SLA) to handle variable-length voxel sequences in point clouds, avoiding the overhead of fixed-length sorting/padding.
- Caveat: Domain-specific (3D point clouds/voxels).


## Paper: SALAD: Achieve High-Sparsity Attention via Efficient Linear Attention Tuning for Video Diffusion Transformer

- Paper ID: ab42f869ecc9fbe9b83bd7372cd21dc4b0b2297a
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (hybrid architecture)
- Why it matters: Proposes a lightweight linear attention branch in parallel with sparse attention, using a scaling strategy to balance the two. Achieves up to 90% sparsity with minimal speedup/quality loss.
- Caveat: Targeted at video diffusion transformers.


## Paper: Scaling Linear Attention with Sparse State Expansion

- Paper ID: fb03ce4d6deed5eb2a147b90095cf0c6e3233f21
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (state-of-the-art hybrid)
- Why it matters: Addresses the performance degradation of linear attention in retrieval/reasoning by using 'Sparse State Expansion' (SSE). It decouples parameter size from state capacity using multiple partitions and row-sparse updates.
- Caveat: Focuses heavily on the information classification aspect of state updates.


## Paper: TransXSSM: A Hybrid Transformer State Space Model with Unified Rotary Position Embedding

- Paper ID: 838e911ebe009dbadb87e6f78b654460c1cddd3a
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Hybrid architecture collision)
- Why it matters: Addresses the positional encoding mismatch between Transformers (RoPE) and SSMs (implicit/convolutional) by introducing 'Unified RoPE'. It demonstrates that a coherent encoding scheme is critical for successful hybrid integration.
- Caveat: The innovation is focused on the positional encoding layer rather than the fundamental scaling mechanism itself.


## Paper: A Survey of Transformer Optimization Techniques

- Paper ID: 014985747e905fa3e2c182d3e8f132d92936c833
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Survey/Review
- Why it matters: Provides a comprehensive taxonomy of Transformer optimizations, specifically categorizing 'efficient attention mechanisms' as a key structural optimization direction. It also predicts 'unified efficient attention theories' as a forthcoming research direction.
- Caveat: Broad scope covers more than just efficient attention (e.g., PEFT, multimodal fusion).
