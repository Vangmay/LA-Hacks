# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: The seed paper itself
- Why it matters: Foundational work that introduced the Transformer architecture, replacing recurrence and convolution with self-attention mechanisms.
- Caveat: High citation volume may obscure subtle technical lineages.


## Paper: Convolutional Sequence to Sequence Learning

- Paper ID: 43428880d75b3a14257c3ee9bda054e61eb869c0
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Direct contemporary competitor focused on parallelization via CNNs.
- Why it matters: Demonstrates the drive towards parallelizable architectures for seq2seq, a key motivation for the Transformer.
- Caveat: Uses convolutions instead of the pure attention mechanism proposed in the seed paper.


## Paper: GCAT: Gated Convolutional Attention Transformer for Efficient Image Super-Resolution

- Paper ID: 117210c651785f147b962ab731d31517227da412
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: High collision risk. Uses a 'Gated Convolutional Attention Unit' (GCAU) combining Convolutional Transposed Attention and Locally-enhanced Gating.
- Why it matters: Demonstrates that gated convolutional attention is a current SOTA direction for efficient Transformers, specifically in Computer Vision (Super-Resolution).
- Caveat: Focuses on image super-resolution; the mechanism (CTA + LeG) may differ from the proposed MoE-style sparsity routing.


## Paper: Image Inpainting Transformer with Mask-Aware Encoding and Dilated Convolutional Attention

- Paper ID: b0fcbd4bc1516d1a9843f06173f55f8963906bc6
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest related mechanism. Uses a Dilated Convolutional Attention Layer (DCAL) to combine self-attention with dilated convolutions.
- Why it matters: While it doesn't explicitly use a convolution to predict an attention sparsity mask, it explores the hybrid combination of convolutions and attention to capture multi-scale features, which is a key component of the proposed idea.
- Caveat: Application is specific to image inpainting; may not generalize to the proposed general-purpose sparsity routing.


## Paper: A Lightweight Transformer Model with Dynamic Sparse Mask for NMT

- Paper ID: b7bd75ef93cdc372c0a8c9b257c241d6169be206
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: High collision risk for 'dynamic sparse mask'. However, it uses 'percentile thresholds' to select significant attention scores rather than a structural mask predicted by a convolutional layer.
- Why it matters: Demonstrates that dynamic sparsity via thresholding is an active area of research, which necessitates a more precise definition of the proposed 'convolutional-driven structural mask'.
- Caveat: The mechanism is score-based (thresholding) rather than topology-based (convolutional mask prediction).
