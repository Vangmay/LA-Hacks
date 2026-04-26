# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (Seed Paper)
- Why it matters: Introduces the Transformer architecture, which relies entirely on attention mechanisms and has become the foundation for almost all modern large language models.
- Caveat: N/A


## Paper: Long Short-Term Memory

- Paper ID: 2e9d221c206e9503ceb452302d68d10e293f2a10
- Year: 1997
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Ancestor (the recurrence/LSTM mechanism that Transformer replaces/dispenses with)
- Why it matters: Established the LSTM architecture, which was the standard for sequential modeling for decades before the Transformer.
- Caveat: N/A


## Paper: Neural Machine Translation by Jointly Learning to Align and Translate

- Paper ID: fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5
- Year: 2014
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Technical Ancestor (introduced the concept of attention in NMT)
- Why it matters: While the Transformer uses 'self-attention' without recurrence, this paper introduced the foundational idea of using an attention mechanism to align source and target sequences, which was a precursor to the Transformer's mechanism.
- Caveat: It still relied on an underlying RNN/LSTM architecture.


## Paper: Convolutional Sequence to Sequence Learning

- Paper ID: 43428880d75b3a14257c3ee9bda054e61eb869c0
- Year: 2017
- Source bucket: near_publication_competitors
- Found by: batch_get_papers
- Relation to seed: Near-publication competitor (alternative parallelizable architecture using CNNs instead of pure attention)
- Why it matters: Demonstrated that convolutional architectures could also provide the parallelization benefits missing in RNNs, providing a strong alternative path for sequence transduction before the Transformer dominance.
- Caveat: Uses gated linear units and attention modules, partially overlapping with Transformer components.


## Paper: Sequence to Sequence Learning with Neural Networks

- Paper ID: cea967b59209c6be22829699f05b8b1ac4dc092d
- Year: 2014
- Source bucket: foundational_references
- Found by: batch_get_papers
- Relation to seed: Technical Ancestor (standardized the encoder-decoder LSTM framework that Transformer improved upon)
- Why it matters: Established the core end-to-end sequence-to-sequence paradigm using LSTMs, providing the benchmark against which the Transformer was compared.
- Caveat: Limited by the sequential nature of LSTMs, making training slower than the Transformer's parallelizable architecture.


## Paper: Deep Residual Learning for Image Recognition

- Paper ID: 2c03df8b48bf3fa39054345bafabfeff15bfd11d
- Year: 2015
- Source bucket: structural_analogues
- Found by: batch_get_papers
- Relation to seed: Structural Analogue (residual connections/skip connections used in Transformer blocks)
- Why it matters: Introduced residual learning, which is a critical architectural component used in the Transformer to enable much deeper networks by facilitating gradient flow.
- Caveat: Originally developed for computer vision (CNNs) but successfully transferred to Transformer architectures.


## Paper: TactileFormer: A feature-fused CNN-Transformer model for few-shot tactile perception

- Paper ID: e48a7076e51e851b6d5e74d902135f61043824a2
- Year: 2026
- Source bucket: direct_followups
- Found by: get_citations
- Relation to seed: Direct Follow-up (Hybridized CNN-Transformer for specialized sensory perception)
- Why it matters: Shows the ongoing trend of combining the local feature extraction strengths of CNNs with the global modeling of Transformers, specifically in the niche of tactile perception.
- Caveat: Represents a highly specialized domain application rather than a general architectural advancement.


## Paper: FLASepformer: Efficient Speech Separation with Gated Focused Linear Attention Transformer

- Paper ID: 7da115e0faa8fc7693e7595f846e6530f84eb378
- Year: 2025
- Source bucket: direct_followups
- Found by: paper_relevance_search
- Relation to seed: Direct Follow-up (Applying focused linear attention to solve the quadratic complexity in speech separation)
- Why it matters: Demonstrates the practical application of linear attention in handling long-duration audio sequences where standard Transformers fail due to memory/speed constraints.
- Caveat: Specific to speech separation; effectiveness in other domains may vary.


## Paper: Advancing Intelligent Sequence Modeling: Evolution, Trade-offs, and Applications of State-Space Architectures from S4 to Mamba

- Paper ID: 124374e44e4eb63248d303c2623671626ffc7354
- Year: 2025
- Source bucket: surveys
- Found by: paper_relevance_search
- Relation to seed: Competitor/Alternative (systematic evolution of SSMs as a transformer alternative)
- Why it matters: Provides a comprehensive overview of the transition from RNNs/Transformers to SSMs (S4, Mamba, etc.), highlighting the trade-offs in efficiency and long-range dependency modeling.
- Caveat: A survey paper, representing a high-level synthesis rather than a single new architectural contribution.


## Paper: Parallelization of Non-linear State-Space Models: Scaling Up Liquid-Resistance Liquid-Capacitance Networks for Efficient Sequence Modeling

- Paper ID: e1e98a053a81b96d93c30a5c2b0f0f76b06f9571
- Year: 2025
- Source bucket: direct_followups
- Found by: paper_relevance_search
- Relation to seed: Competitor/Alternative (Non-linear SSM that claims better stability and parallelization than Mamba)
- Why it matters: It targets the specific weaknesses of current SSMs (like Mamba) regarding training dynamics and gradient stability, while maintaining linear complexity.
- Caveat: Focuses on non-linear recurrent models; may have different inductive biases than pure attention.


## Paper: Mamba-360: Survey of State Space Models as Transformer Alternative for Long Sequence Modelling

- Paper ID: ba4c5a116d07b37dea1046b6d16a60cb2d01cd47
- Year: 2024
- Source bucket: surveys
- Found by: paper_relevance_search
- Relation to seed: Competitor/Alternative (Survey of architectures designed to overcome Transformer limitations)
- Why it matters: Provides a taxonomical view of the SSM landscape (gating, structural, recurrent architectures) and categorizes them as primary candidates to replace or augment the Transformer for long-sequence tasks.
- Caveat: Being a survey, it synthesizes existing work rather than presenting a single new technical breakthrough.
