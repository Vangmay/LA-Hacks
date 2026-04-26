# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: itself
- Why it matters: Foundational work introducing the Transformer architecture, replacing recurrence and convolution with self-attention mechanisms.
- Caveat: N/A


## Paper: Neural Machine Translation by Jointly Learning to Align and Translate

- Paper ID: fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5
- Year: 2014
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: direct ancestor (introduced attention mechanism for NMT)
- Why it matters: Established the concept of an attention mechanism to connect encoder and decoder, a key component later fully embraced/transformed by the Transformer.
- Caveat: Still relied on recurrent architectures (RNNs/LSTMs).


## Paper: Attention Is All You Need for Chinese Word Segmentation

- Paper ID: d4f68b2c033a79fc02f30d8cffb6cbc532cdbd51
- Year: 2019
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: adaptation (applying Transformer to CWS task)
- Why it matters: Demonstrates early rapid adaptation of the Transformer architecture to non-English, specialized NLP tasks (Chinese word segmentation) using variants like the Gaussian-masked Directional Transformer.
- Caveat: Specific to CWS; architectural modifications might not generalize to all sequence transduction tasks.


## Paper: LaplacianFormer: Rethinking Linear Attention with Laplacian Kernel

- Paper ID: e62198fd44c62b890c99e738e02ec5064cd6ec93
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: high collision risk (directly addresses linearizing attention via kernel approximation)
- Why it matters: Proposes using a Laplacian kernel and Nyström approximation to avoid the limitations of Gaussian kernels, aiming to retain fine-grained token information.
- Caveat: Extremely recent/pre-print; specifically targets vision tasks (ImageNet).


## Paper: Technologies on Effectiveness and Efficiency: A Survey of State Spaces Models

- Paper ID: f8aefc5e6e86987ef32d2fb8da79f82f93b277ac
- Year: 2025
- Source bucket: bulk_search
- Found by: paper_relevance_search
- Relation to seed: parallel evolution (alternative to Transformer scaling)
- Why it matters: Provides a systematic overview of SSMs (S4, Mamba), highlighting their ability to handle long sequences with linear complexity, serving as the primary competitor/alternative to the 'Linearized Self-Attention' approach.
- Caveat: Survey paper; provides breadth rather than a single new technical kernel.


## Paper: Jamba: A Hybrid Transformer-Mamba Language Model

- Paper ID: cbaf689fd9ea9bc939510019d90535d6249b3367
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: high collision risk (direct implementation of hybrid architectures)
- Why it matters: A major work that interleaves Transformer and Mamba layers with Mixture-of-Experts (MoE), demonstrating that hybridizing these families can achieve high throughput and long-context capabilities (up to 256K tokens) within manageable memory footprints.
- Caveat: Represents a highly successful, well-funded implementation; novelty must look beyond simple interleaving.


## Paper: A2Mamba: Attention-augmented State Space Models for Visual Recognition

- Paper ID: db1c43397c000b35fe172c67bb20fe8102777dab
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: high collision risk (addresses interaction between Transformer and Mamba)
- Why it matters: Directly addresses the 'simple stacking' limitation of current hybrids by proposing a token mixer (MASS) that integrates multi-scale attention maps into the SSM, creating a structured interaction mechanism.
- Caveat: Focuses on visual recognition (ImageNet, segmentation, detection); general language modeling applicability remains to be seen.


## Paper: Mixture-of-Recursions: Learning Dynamic Recursive Depths for Adaptive Token-Level Computation

- Paper ID: 875418bb21265276be9298b50e52a6c53ff3a202
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: high collision risk (addresses adaptive token-level computation)
- Why it matters: Proposes 'Mixture-of-Recursions' (MoR) which uses lightweight routers to assign different recursion depths to individual tokens. This directly competes with the 'Dynamic Routing' idea, though it focuses on recursion depth rather than routing between Transformer and SSM layers.
- Caveat: Uses a Recursive Transformer architecture, not a hybrid Transformer-Mamba architecture.


## Paper: MambaFormer: Token-Level Guided Routing Mixture-of-Experts for Accurate and Efficient Clinical Assistance

- Paper ID: 8a3ee6b06695a444b63e79d9ff542d1c7c7b947a
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: high collision risk (direct implementation of token-level routing between Transformer and Mamba)
- Why it matters: This paper explicitly implements the core idea of my 'Dynamic Routing' proposal: using a lightweight gating mechanism to route tokens to either a Transformer expert (for complex, short queries) or an SSM expert (for long, high-throughput sequences).
- Caveat: Specifically tailored for clinical assistance (medical QA) and uses a customized 'EMamba'/'ET5' setup; general-purpose LLM routing remains an area for potential divergence.
