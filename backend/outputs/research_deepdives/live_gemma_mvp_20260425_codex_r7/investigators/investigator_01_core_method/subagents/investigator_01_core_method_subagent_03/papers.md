# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: This is the seed paper.
- Why it matters: Introduces the Transformer architecture, which uses only attention mechanisms and avoids recurrence/convolutions.
- Caveat: N/A


## Paper: A Deep Reinforced Model for Abstractive Summarization

- Paper ID: 032274e57f7d8b456bd255fe76b909b2c1d7458e
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: Pre-Transformer work addressing summarization issues (repetitive/incoherent phrases) via RL and intra-attention.
- Why it matters: Highlights the challenges of RNN-based seq2seq before Transformer's dominance.
- Caveat: N/A


## Paper: Off-Policy Self-Critical Training for Transformer in Visual Paragraph Generation

- Paper ID: 0f8934f5e17a1e9d7592c641305477fe630a0fbb
- Year: 2020
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong collision. Addresses the difficulty of combining Transformers with RL (due to sampling costs) by using an off-policy approach with a GRU-based behavior policy.
- Why it matters: Provides a specific technical solution to the sampling efficiency problem that would otherwise make the proposed idea hard to implement.
- Caveat: Focuses on visual paragraph generation rather than general NMT/summarization.


## Paper: Recovery Should Never Deviate from Ground Truth: Mitigating Exposure Bias in Neural Machine Translation

- Paper ID: 2ef10559f59f3877ff7b3babfcc12972ceee842e
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong collision/Related work. Directly addresses exposure bias in NMT, which is the primary application domain of the Transformer.
- Why it matters: Represents the current state-of-the-art (SOTA) effort in NMT to mitigate exposure bias, likely using techniques that compete with the proposed RL-based seed.
- Caveat: Need to check if it uses RL or a different mechanism (e.g., scheduled sampling or a new loss function).


## Paper: Scheduled Sampling for Transformers

- Paper ID: 6b6befbff611ddc98ef268b3c51353593bb07e77
- Year: 2019
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Technical collision. Proposes a two-pass decoding strategy specifically to adapt scheduled sampling to the Transformer's non-recurrent architecture.
- Why it matters: Shows that 'vanilla' scheduled sampling is not trivial for Transformers and that architectural adaptations are required.
- Caveat: Primarily focuses on the architectural mechanism for sampling rather than the optimization objective (like RL or contrastive learning).


## Paper: Contrastive Preference Learning for Neural Machine Translation

- Paper ID: db0ef40e1985037eebde306bd91a1bc71836b3e1
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong technical collision/alternative. Introduces Contrastive Preference Learning (CPL) using list-wise preferences to align models with sequence-level quality, specifically targeting the discrepancy between token-level MLE and sequence-level expectations (exposure bias).
- Why it matters: It provides a highly competitive, modern alternative to RL-based sequence optimization by using a contrastive framework.
- Caveat: Uses list-wise preferences and an indicator function; the novelty of the RL proposal must clearly differentiate itself from this specific preference-based alignment approach.


## Paper: Direct Preference Optimization for Neural Machine Translation with Minimum Bayes Risk Decoding

- Paper ID: 6c6d2ac4f7c94b30ceef79ba3e72840d0f4ba1d0
- Year: 2023
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong technical collision. Applies DPO to NMT to achieve the benefits of Minimum Bayes Risk (MBR) decoding without the inference-time cost.
- Why it matters: Represents the current SOTA direction of using preference-based optimization (DPO) to bridge the gap between token-level and sequence-level objectives in NMT.
- Caveat: DPO is a derivative of RL (effectively bypassing the explicit RL reward modeling step); the proposed seed must distinguish between 'standard DPO alignment' and 'addressing exposure bias via policy-gradient-based reward optimization for error recovery'.
