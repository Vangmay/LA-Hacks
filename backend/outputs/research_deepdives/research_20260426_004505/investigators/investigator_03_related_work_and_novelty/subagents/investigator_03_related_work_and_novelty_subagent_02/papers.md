# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (This is the seed paper)
- Why it matters: Establishes the Transformer architecture, which replaces recurrence/convolution with self-attention, serving as the foundation for the entire investigation.
- Caveat: Highly influential; most research will build upon or react to this.


## Paper: Research on Improved Swin Transformer-Based Single Object Tracking Algorithms

- Paper ID: c9a0674cba7ae85eadc969026bac04500467db2e
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Explicitly identifies 'limitations in local information capture' in Swin-based tracking and proposes Dynamic Window Attention (DWA) to address adaptive spatial modeling. This directly supports the premise that standard Swin windows may struggle with dynamic or fine-grained local detail.
- Caveat: Focuses on Single Object Tracking (SOT), which is a specific downstream task.


## Paper: Learning Local-Global Representation for Scribble-Based RGB-D Salient Object Detection via Transformer

- Paper ID: 9c727a96b81563ee67e75c272c93d840e6822924
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Explicitly states that using local representations (CNNs or Transformers) alone is ineffective at capturing global contexts in cluttered regions, necessitating a 'local-global representation learning framework' using dual Transformer decoders.
- Caveat: Domain-specific (Salient Object Detection).


## Paper: PlgFormer: parallel extraction of local-global features for AD diagnosis on sMRI using a unified CNN-transformer architecture

- Paper ID: 976c1a5243eaa6820fc88c46a67c9fe45d805897
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Uses a CNN-Transformer architecture to extract local and global context, featuring an adaptive gating mechanism in the decision-making layer to select context features. This is a direct collision for the 'dynamic gating' technical mechanism.
- Caveat: Domain-specific (Alzheimer's diagnosis using sMRI).


## Paper: FANet: Frequency-Aware Attention-Based Tiny-Object Detection in Remote Sensing Images

- Paper ID: c719751ab853717aeb3985912d9e3c07b721d092
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Uses a 'Multi-Scale Frequency Feature Enhancement Module' to adaptively highlight contour/texture details. This is a collision for 'frequency-aware' mechanisms, but it focuses on *detection modules* rather than *attention-gating within a Transformer block* for general dense prediction.
- Caveat: Domain-specific (Remote Sensing).
