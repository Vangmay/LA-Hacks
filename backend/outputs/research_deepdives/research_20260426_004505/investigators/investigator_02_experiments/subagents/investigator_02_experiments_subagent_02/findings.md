# Findings



## Finding: Quadratic vs. Linear Complexity Trade-off

- Claim: Standard Transformer architectures face quadratic computational complexity, limiting their efficiency on high-resolution or long-sequence data, while State-Space Models (SSMs) like Mamba offer linear complexity but at potential costs to context integration.
- Confidence: high
- Evidence:
  - f8722d87b9d86f78f1865d51649f8e51255b76d7 (MTMixer, 2025)
  - 7026f38dadeb7f28bb58f944d1f08bed9df0190b (HLX, 2025)
- Why it matters: This tension drives the current research trend toward hybrid architectures that interleave attention and SSM layers.
- Caveat: The optimal interleaving ratio and placement (e.g., interleaved vs. hierarchical) remain active areas of research.


## Finding: Bidirectional SSMs are an Emerging Trend in Domain-Specific Applications

- Claim: Recent research (2024-2026) is actively addressing the unidirectional scan limitation of SSMs by implementing bidirectional versions for specialized tasks.
- Confidence: high
- Evidence:
  - da9178eae82d1ca5492aaecd0151ba49481cb8b1 (Dual-path Mamba, 2024)
  - a9f8132b2a5b7726a0cf6da4fe3520b7371f36ff (BabyMamba-HAR, 2026)
  - 7a05b0e3cb7613e3d932f5f419adc35508a45332 (MetaMamba, 2026)
- Why it matters: My initial proposal seed (Bidirectional Selective SSMs) has significant collision risk. Novelty must shift from 'can we do it' to 'how can we do it more efficiently or generally'.
- Caveat: Most current implementations are domain-specific (speech, HAR, metasurfaces). A general-purpose, highly efficient bidirectional SSM for LLMs or Vision is still an open challenge.


## Finding: Non-Causal SSM Research is Vision-Centric

- Claim: Current state-of-the-art non-causal SSM architectures (e.g., VSSD, SF-Mamba, Vim) are predominantly focused on vision tasks (image classification, segmentation, etc.), leaving a gap in efficient non-causal mechanisms for language modeling (LLMs).
- Confidence: high
- Evidence:
  - 0da8568dc1b3dfc781c51881c082a83f731bc89f (VSSD, 2024)
  - fc6904cbe402225c7a7b2e35aa69f59064a34566 (SF-Mamba, 2026)
  - 38c48a1cd296d16dc9c56717495d6e44cc354444 (Vision Mamba, 2024)
- Why it matters: This identifies a significant research gap. While non-causality is natural for vision (spatial context), language models traditionally rely on causal/autoregressive modeling. However, tasks like non-autoregressive translation, prefix-LM training, or bidirectional context modeling in LLMs represent a massive opportunity for efficient non-causal SSMs.
- Caveat: Language modeling is fundamentally different in terms of data structure (1D sequence vs 2D spatial) and dependency patterns, so a vision-based non-causal mechanism might not translate directly.


## Finding: Collision Analysis of Bidirectional SSMs

- Claim: While bidirectional scanning in SSMs is an active research area, current implementations are primarily domain-specific (vision, speech, proteins) and often rely on multi-scan/dual-pass strategies that may not scale efficiently to general-purpose LLMs.
- Confidence: high
- Evidence:
  - da9178eae82d1ca5492aaecd0151ba49481cb8b1 (Dual-path Mamba, 2024)
  - 38c48a1cd296d16dc9c56717495d6e44cc354444 (Vision Mamba, 2024)
  - 0da8568dc1b3dfc781c51881c082a83f731bc89f (VSSD, 2024)
- Why it matters: This collision analysis refines the research direction. The novelty is no longer in 'making SSMs bidirectional' (which is being done), but in 'making bidirectional SSMs efficient/single-pass and general-purpose (LLM-ready)'.
- Caveat: A truly single-pass bidirectional mechanism might require a fundamental rethink of the SSM kernel, similar to how VSSD modifies the interaction magnitudes in SSD.
