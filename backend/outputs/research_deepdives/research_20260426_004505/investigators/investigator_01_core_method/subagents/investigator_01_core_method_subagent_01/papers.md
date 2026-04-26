# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: This IS the seed paper.
- Why it matters: Fundamental architecture for modern NLP, introducing the Transformer which replaces recurrence/convolutions with self-attention.
- Caveat: Quadratic complexity O(n^2) relative to sequence length makes it expensive for extremely long contexts.


## Paper: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer

- Paper ID: 510e26733aaff585d65701b9f1be7ca9d5afc586
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Cited by Transformer; establishes conditional computation/MoE techniques used in scaling transformers.
- Why it matters: Introduced Sparsely-Gated MoE, allowing massive parameter counts with controlled computation cost.
- Caveat: Primarily applied to LSTMs in this paper; scaling to Transformer architectures was a later evolution.


## Paper: MoE-DiffuSeq: Enhancing Long-Document Diffusion Models with Sparse Attention and Mixture of Experts

- Paper ID: a1a7e3ce73856fc6cc36c270b7b65a84ff5ea055
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision; integrates sparse attention and MoE for long-document diffusion.
- Why it matters: Shows that the recombination of sparse attention and MoE is being actively researched for efficiency in long-form generation.
- Caveat: Specifically targets diffusion-based models rather than standard autoregressive Transformers.


## Paper: DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model

- Paper ID: 53a803388e83ae89261624099d7be4287ace67cb
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Indirect collision/neighbor; uses Multi-head Latent Attention (MLA) for KV cache compression alongside MoE.
- Why it matters: Represents the modern SOTA approach to combining efficiency (KV cache reduction) with massive model capacity (MoE).
- Caveat: Focuses on compressing the latent representation of KV rather than sparse gating the attention mechanism itself.


## Paper: Mixture of Sparse Attention: Content-Based Learnable Sparse Attention via Expert-Choice Routing

- Paper ID: 2951fcda8cb6a3f5c25f3659f5330ac3f2201bf9
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision; uses 'expert-choice routing' to select tokens for attention heads, reducing complexity from $O(T^2)$ to $O(k^2 + T)$.
- Why it matters: It explicitly uses the MoE concept (expert-choice) to solve the quadratic scaling problem identified in the seed paper.
- Caveat: Focuses on selecting *tokens* (sequence length) rather than selecting *heads* or *sub-networks* of the attention mechanism itself.


## Paper: Mixture of Attention Heads: Selecting Attention Heads Per Token

- Paper ID: 3820231d31540ecb05d94c74d959a2f61d3136ea
- Year: 2022
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision; proposes 'Mixture of Attention Heads (MoA)' where a router selects $k$ heads per token.
- Why it matters: It established the precedent of applying conditional computation (MoE) directly to the multi-head attention component rather than just the FFN layers.
- Caveat: It focuses on selecting heads, whereas more recent work (MoSA 2025) focuses on selecting tokens via expert-choice routing.


## Paper: Adaptive selection of local and non-local attention mechanisms for speech enhancement

- Paper ID: 3762eebc4b95f6ef9f6d00c530479a87acce75f6
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Indirect collision/neighbor; uses an adaptive selection network to route between local and non-local attention for speech tasks.
- Why it matters: Demonstrates that routing between different *types* of attention mechanisms is a viable strategy for specialized domains.
- Caveat: Domain-specific (speech enhancement) and uses reinforcement learning for selection.


## Paper: Mixture-of-Transformers: A Sparse and Scalable Architecture for Multi-Modal Foundation Models

- Paper ID: 18ea06ae95cad35d3c79610d16dd2a3c9ee208a5
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Indirect collision/neighbor; uses MoE to decouple modality-specific parameters (FFNs, attention matrices, layer norm).
- Why it matters: It scales multi-modal Transformers by allowing different parameters for different modalities, effectively routing input through modality-specific 'experts'.
- Caveat: Focuses on modality-specific routing rather than complexity-based routing (sparse vs dense).
