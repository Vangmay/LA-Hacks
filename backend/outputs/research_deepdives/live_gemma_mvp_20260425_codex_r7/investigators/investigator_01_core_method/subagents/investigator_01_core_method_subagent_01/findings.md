# Findings



## Finding: Architectural Shift to Pure Attention

- Claim: The Transformer architecture enables massive parallelization by replacing recurrent (RNN) and convolutional (CNN) layers with a mechanism based entirely on multi-head attention.
- Confidence: high
- Evidence:
  - 204e3073870fae3d05bcbc2f6a8e263d9b72e776 (Vaswani et al., 2017)
  - 43428880d75b3a14257c3ee9bda054e61eb869c0 (Gehring et al., 2017 - Convolutional alternative)
- Why it matters: This shift removes the sequential dependency bottleneck inherent in RNNs, which is the primary driver for the scalability of modern Large Language Models.
- Caveat: While parallelizable, the quadratic complexity of standard self-attention relative to sequence length remains a significant scaling bottleneck.


## Finding: Divergence in Gating Application

- Claim: Current 'gating' research in attention is highly domain-specific (e.g., causal discovery for trajectory prediction, multimodal fusion for emotion recognition) and lacks a generalized, information-theoretic foundation for scaling sequence-based models.
- Confidence: medium
- Evidence:
  - 2ec42c07250ef4d7cb2d27d7626caf3404d2bbac (Causal Attention Gating for driving)
  - bca9025646cb4cd3c1db62242cda2620e78ee61f (Residual Gating for emotion)
- Why it matters: This suggests a significant research gap: the absence of a principled, differentiable, and general-purpose 'admission control' or 'gating' mechanism for linear attention that uses information-theoretic metrics (like surprisal or entropy) to preserve high-utility tokens while discarding redundancy.
- Caveat: Most existing work is applied to niche domains; a general LLM-focused mechanism might face different scaling and training challenges.
