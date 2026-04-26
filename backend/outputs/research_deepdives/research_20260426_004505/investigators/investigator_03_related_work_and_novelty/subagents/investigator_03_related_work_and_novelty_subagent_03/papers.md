# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (this is the seed paper)
- Why it matters: Establishes the Transformer architecture based solely on attention mechanisms, replacing recurrence and convolutions. Highly influential foundational work.
- Caveat: None


## Paper: A Deep Reinforced Model for Abstractive Summarization

- Paper ID: 032274e57f7d8b456bd255fe76b909b2c1d7458e
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Pre-dates/contemporaneous work using RNNs and reinforcement learning for summarization.
- Why it matters: Highlights the limitations of RNN-based models (repetitive/incoherent phrases) and the use of RL to combat exposure bias.
- Caveat: Uses RNNs, which the Transformer seeks to replace.


## Paper: Convolutional Sequence to Sequence Learning

- Paper ID: 43428880d75b3a14257c3ee9bda054e61eb869c0
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: A major contemporaneous approach using CNNs for sequence modeling, emphasizing parallelization over RNNs.
- Why it matters: Provides the 'convolutional' alternative to the Transformer's 'attention-only' approach, highlighting the trade-offs in parallelization and inductive biases.
- Caveat: Uses convolutions, which have local receptive fields, unlike the global scope of self-attention.


## Paper: Bridging local and global representations: An inter-and intra-window based transformer for unsupervised depth completion

- Paper ID: f1a19290eb68ae169a2fd86e279e5025f71ffc8a
- Year: 2026
- Source bucket: recent_followups
- Found by: get_citations
- Relation to seed: Modern application/extension using inter- and intra-window based transformers for specific computer vision tasks.
- Why it matters: Shows the evolution of Transformer architectures toward handling local vs. global representation trade-offs, a key area for efficiency and specialization.
- Caveat: Focused on unsupervised depth completion.


## Paper: Peri-LN: Revisiting Normalization Layer in the Transformer Architecture

- Paper ID: b1e62f72336064184edb998eb39115fc9b6a6243
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Investigates the placement of normalization layers (LN) within the Transformer block.
- Why it matters: Identifies 'Peri-LN' as a promising strategy to stabilize training and improve gradient flow by placing LN peripherally around sublayers, addressing the limitations of Pre-LN and Post-LN.
- Caveat: Analytical foundation is provided, but the mechanism is still being 'unexplored' by the broader community.


## Paper: BETA: A Bit-Grained Transformer Attention Accelerator With Efficient Early Termination

- Paper ID: a7a71daece55f88209e792218fabf3fd75412461
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Addresses hardware efficiency of sparse attention.
- Why it matters: Proposes an algorithm-architecture co-design (bit-grained prediction, adaptive thresholding) to overcome the hardware inefficiency of the extra prediction stage in dynamic sparse attention.
- Caveat: Focuses on hardware acceleration/co-design rather than purely algorithmic complexity reduction.


## Paper: AV-LocoFiLM: Audio-Visual Speech Enhancement Using FiLM-Based Fusion and Hybrid Local–Global Transformers

- Paper ID: 03c6c820a05a22d73ce980c580f2e9df608eaa0d
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Uses a hybrid local-global transformer architecture for speech enhancement.
- Why it matters: Demonstrates the trend of using alternating local convolutional operations and global self-attention, though applied to audio-visual fusion rather than fixing the linear attention expressiveness gap directly.
- Caveat: Domain-specific (audio-visual speech enhancement).


## Paper: LaplacianFormer: Rethinking Linear Attention with Laplacian Kernel

- Paper ID: e62198fd44c62b890c99e738e02ec5064cd6ec93
- Year: 2026
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Addresses expressiveness and injectivity in linear attention via a Laplacian kernel and provably injective feature maps.
- Why it matters: It is a direct collision/competitor to the 'IL-LA' proposal. It tackles the 'injectivity' issue specifically with 'provably injective feature maps' and uses a Laplacian kernel to improve token interaction. This means the 'global stream' part of my proposal needs to be further differentiated (e.g., by the specific kernel type or the way the local stream is integrated).
- Caveat: Uses Nyström approximation and Newton-Schulz iteration for efficiency.
