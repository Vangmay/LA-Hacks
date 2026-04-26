# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed
- Found by: arXiv resolution
- Relation to seed: N/A (Seed Paper)
- Why it matters: Establishes the Transformer architecture, replacing RNNs and CNNs with self-attention mechanisms, enabling massive parallelization and scaling.
- Caveat: This is the baseline for the entire investigation.


## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: resolve_arxiv_paper
- Found by: Initial resolution of seed URL
- Relation to seed: Seed Paper
- Why it matters: Foundational Transformer architecture that dispenses with recurrence and convolutions in favor of pure attention mechanisms, enabling massive parallelization.
- Caveat: Highly influential; provides the baseline for nearly all modern LLM architectures.


## Paper: Long Short-Term Memory

- Paper ID: 2e9d221c206e9503ceb452302d68d10e293f2a10
- Year: 1997
- Source bucket: get_references
- Found by: Reference list of seed paper
- Relation to seed: Ancestor (Recurrent Primitive)
- Why it matters: Foundational work for gated recurrent units, establishing the era of sequential processing that Transformers eventually superseded.
- Caveat: Strictly recurrent; suffers from sequential dependency and vanishing gradient issues in very long sequences.


## Paper: Bridging local and global representations: An inter-and intra-window based transformer for unsupervised depth completion

- Paper ID: f1a19290eb68ae169a2fd86e279e5025f71ffc8a
- Year: 2026
- Source bucket: citation
- Found by: get_citations
- Relation to seed: direct_followup (architectural evolution)
- Why it matters: Represents the contemporary trend of modifying Transformer architectures to balance local context (intra-window) with global context (inter-window), addressing the spatial resolution/complexity trade-off in vision tasks.
- Caveat: This is a specific application in depth completion; generalizability to other vision/sequence tasks should be verified.


## Paper: Neural Machine Translation by Jointly Learning to Align and Translate

- Paper ID: fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5
- Year: 2014
- Source bucket: get_references
- Found by: Reference list of seed paper
- Relation to seed: Ancestor (Attention-augmented RNN)
- Why it matters: Introduced the attention mechanism as a way for RNNs to focus on specific parts of the input sequence, addressing the bottleneck of fixed-length context vectors.
- Caveat: Still relies on recurrent architectures (LSTMs/GRUs) for sequence modeling.


## Paper: Convolutional Sequence to Sequence Learning

- Paper ID: 43428880d75b3a14257c3ee9bda054e61eb869c0
- Year: 2017
- Source bucket: get_references
- Found by: Reference list of seed paper
- Relation to seed: Near-publication competitor
- Why it matters: Explores using convolutional layers for sequence-to-sequence tasks, offering a middle ground between the sequential nature of RNNs and the pure attention mechanism of Transformers, with a focus on parallelization.
- Caveat: Primarily focuses on capturing local dependencies via convolutions rather than the global dependencies enabled by self-attention.


## Paper: Optimizing Transformer Based Inference Efficiency Using CMM-D

- Paper ID: 11f23c5b7a5ca470f6f6c72698bf50bf14372059
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: downstream_optimization
- Why it matters: Highlights the 'GPU memory wall' and 'DDR memory wall' as fundamental hardware constraints that limit Transformer scaling. It suggests hardware-level solutions (CMM-D, CXL) to address the gap between model parameter growth and memory bandwidth/capacity.
- Caveat: Focuses on system-level inference efficiency rather than architectural changes to the attention mechanism itself.


## Paper: A Structured Self-attentive Sentence Embedding

- Paper ID: 204a4a70428f3938d2c538a4d74c7ae0416306d8
- Year: 2017
- Source bucket: get_references
- Found by: Reference list of seed paper
- Relation to seed: Near-publication competitor / Ancestor of self-attention mechanisms
- Why it matters: Directly utilizes a self-attention mechanism to create interpretable sentence embeddings via a 2-D matrix, demonstrating the utility of attention for capturing structural information within a single sequence before the full Transformer paradigm was established.
- Caveat: Focuses on sentence embeddings rather than sequence-to-sequence transduction.


## Paper: Advancing Intelligent Sequence Modeling: Evolution, Trade-offs, and Applications of State-Space Architectures from S4 to Mamba

- Paper ID: 124374e44e4eb63248d303c2623671626ffc7354
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: paradigm_shift_candidate
- Why it matters: Provides a comprehensive evolutionary view of SSMs, tracing the lineage from S4 to Mamba, and explicitly discusses how they address Transformer limitations (quadratic complexity, sequential bottlenecks).
- Caveat: It is a survey/evolutionary paper, so it synthesizes rather than introduces a single novel mechanism, but it's crucial for mapping the divergence.


## Paper: A Survey of Retentive Network

- Paper ID: 85e5a69d4718ea5289afb5d369bba9ca0a64865d
- Year: 2025
- Source bucket: paper_relevance_search
- Found by: Keyword search for Transformer limitations
- Relation to seed: Successor / Architectural alternative
- Why it matters: Discusses RetNet as a way to unify the inductive bias of recurrence with the global modeling of attention, specifically addressing the quadratic complexity bottleneck of the Transformer.
- Caveat: This is a survey paper, providing a high-level overview of a specific alternative rather than primary research on the mechanism itself.


## Paper: HyMaTE: A Hybrid Mamba and Transformer Model for EHR Representation Learning

- Paper ID: e23885d06cd2864134aaa7aa8520170a4aab14af
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: hybrid_evolution
- Why it matters: Provides concrete evidence of the 'hybridization' trend. It explicitly notes that while SSMs (Mamba) excel at sequence-level information, they may lack the channel-level modeling capabilities of Transformers, leading researchers to combine them (HyMaTE) to capture both long-range dependencies and nuanced multivariate relationships.
- Caveat: This is a domain-specific application (EHR data); the architectural synergy observed might vary in other data modalities.


## Paper: A Benchmark of State-Space Models vs. Transformers and BiLSTM-based Models for Historical Newspaper OCR

- Paper ID: 60bf0ddd1232b84d86bf6a1fae86aca872d5fd86
- Year: 2026
- Source bucket: paper_relevance_search
- Found by: Keyword search for SSM/Mamba vs Transformer
- Relation to seed: Successor / Architectural divergence (Linear-time SSM)
- Why it matters: Provides empirical evidence that Mamba-based models can maintain competitive accuracy while halving inference time and offering superior memory scaling compared to Transformers in long-sequence tasks (OCR).
- Caveat: Focused on a specific domain (OCR) and historical newspaper datasets.


## Paper: Transformer Encoder vs. Mamba SSM: Lightweight Architectures for Machining Stability-Induced Surface-Quality Categorization

- Paper ID: 98708063b6891c8173d49fdd9c721276527b066e
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: direct_comparison
- Why it matters: Provides a direct comparative study between Transformer encoders and Mamba SSMs in a high-frequency, real-time industrial context. It highlights the need for compact architectures in domains where inference latency must be extremely low (~0.001s), positioning SSMs as a viable alternative for efficiency-critical applications.
- Caveat: This study is applied to sensor signals in manufacturing; results may not translate directly to natural language or vision tasks.


## Paper: TransXSSM: A Hybrid Transformer State Space Model with Unified Rotary Position Embedding

- Paper ID: 838e911ebe009dbadb87e6f78b654460c1cddd3a
- Year: 2025
- Source bucket: paper_relevance_search
- Found by: Keyword search for hybrid architectures
- Relation to seed: Successor / Hybrid Integration
- Why it matters: Addresses the positional encoding incompatibility between Transformers (RoPE) and SSMs (implicit convolution) through a 'Unified RoPE', enabling a more coherent hybrid architecture that outperforms standard Transformers in speed and accuracy.
- Caveat: Focuses on a specific positional encoding solution as the driver for hybrid success.


## Paper: The Computational Limits of State-Space Models and Mamba via the Lens of Circuit Complexity

- Paper ID: 8fd3b55e1699bd183c98f88b53dfadb422d7f026
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: theoretical_critique
- Why it matters: Provides a rigorous theoretical challenge to the assumption that SSMs/Mamba are inherently more expressive than Transformers. It uses circuit complexity to argue that Mamba resides in the same $\mathsf{TC}^0$ complexity class as Transformers, meaning they face similar fundamental computational limits on certain problem types (e.g., arithmetic/boolean formulas).
- Caveat: This is a theoretical complexity analysis; it does not necessarily negate the empirical performance/efficiency advantages observed in practical deep learning tasks.


## Paper: On the Intrinsic Limits of Transformer Image Embeddings in Non-Solvable Spatial Reasoning

- Paper ID: d1ef0fb8a211bf407270a6f2fdc3d51383ea0c2a
- Year: 2026
- Source bucket: citation
- Found by: get_citations (for 8fd3b55e1699bd183c98f88b53dfadb422d7f026)
- Relation to seed: complexity_critique
- Why it matters: Directly links the $\mathsf{TC^0}$ complexity bound of constant-depth Transformers to a failure in spatial reasoning (e.g., 3D rotations). It provides empirical and theoretical evidence that the architectural limitations identified in complexity theory manifest as specific cognitive-like failures in vision tasks.
- Caveat: Focuses on 'non-solvable' groups; applicability to general semantic reasoning is an open question.
