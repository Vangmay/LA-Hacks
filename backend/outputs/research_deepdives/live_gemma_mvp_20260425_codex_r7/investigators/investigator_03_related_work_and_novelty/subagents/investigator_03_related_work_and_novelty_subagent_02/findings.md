# Findings



## Finding: Complexity-Scaling Tension (Attention vs. SSMs)

- Claim: A fundamental tension exists between the $O(N^2)$ associative retrieval capability of Transformers and the $O(N)$ efficient long-sequence compression of State Space Models (SSMs).
- Confidence: high
- Evidence:
  - Paper: VL-Mamba (2024) identifies Transformer quadratic complexity as a bottleneck for multimodal long-sequence modeling.
  - Paper: Mamba-360 (2024) categorizes SSMs as a paradigm shift to address $O(N^2)$ challenges in NLP and beyond.
  - Paper: MoE-Mamba (2024) suggests SSMs need Mixture of Experts (MoE) to match the scaling potential of Transformer-based LLMs.
- Why it matters: This tension is the primary driver for current architectural innovation. Novelty can be found in hybridizing these two (e.g., combining Attention's precise retrieval with SSM's efficient state management) or in proving the limits of one over the other in specific reasoning tasks.
- Caveat: While SSMs scale linearly, they may lack the 'perfect memory' or precise needle-in-a-haystack retrieval capabilities inherent in the attention mechanism.


## Finding: The Hybridization Gap (Sequential vs. Dynamic)

- Claim: Current hybrid Transformer-SSM architectures primarily follow two patterns: sequential/fixed-layering (e.g., Mamba $\rightarrow$ Transformer) or interleaved architectures (e.g., Jamba), but lack content-dependent, per-token kernel routing.
- Confidence: high
- Evidence:
  - MetaMamba-Aesthetic (2025) uses a sequential hybrid (Mamba for features $\rightarrow$ Transformer for reasoning).
  - Jamba-style architectures (implicit in general literature) use fixed interleaving of blocks.
  - DELTA (2025) and SkipGPT (2025) focus on *sparsifying* or *pruning* existing layers rather than switching the fundamental computational kernel (Attention vs. SSM) based on token importance.
- Why it matters: This represents a significant opportunity for novelty. A model that can dynamically decide, 'this token is a high-entropy key term, use Attention' versus 'this token is low-entropy background, use SSM' would potentially achieve the 'best of both worlds' (precise retrieval + linear scaling) more effectively than fixed-ratio hybrids.
- Caveat: The complexity of implementing a real-time, hardware-efficient gating mechanism might outweigh the theoretical efficiency gains.
