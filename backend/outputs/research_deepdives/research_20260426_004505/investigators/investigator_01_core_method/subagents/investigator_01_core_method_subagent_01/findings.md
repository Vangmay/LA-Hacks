# Findings



## Finding: Architectural Transition to Pure Attention

- Claim: The Transformer architecture marks a departure from the heavy reliance on recurrence (RNNs) and convolutions (CNNs) that characterized sequence transduction models in 2017.
- Confidence: high
- Evidence:
  - 43428880d75b3a14257c3ee9bda054e61eb869c0 (Convolutional Sequence to Sequence Learning) - demonstrated parallelization via CNNs.
  - 032274e57f7d8b456bd255fe76b909b2c1d7458e (A Deep Reinforced Model for Abstractive Summarization) - utilized RNN-based encoder-decoder models.
  - 13d9323a8716131911bfda048a40e2cde1a76a46 (Structured Attention Networks) - attempted to add richer structure to basic attention mechanisms.
- Why it matters: This transition was driven by the need for better parallelization (unlike RNNs) and more efficient long-range dependency modeling (improving upon CNNs/RNNs).
- Caveat: While it dispensed with recurrence/convolution, it introduced new complexities like quadratic attention scaling.


## Finding: Collision Analysis of Sparse-Gated Attention

- Claim: The idea of combining MoE with attention is actively being explored via head selection and token selection.
- Confidence: high
- Evidence:
  - 3820231d31540ecb05d94c74d959a2f61d3136ea (MoA 2022) - Selects attention heads per token.
  - 2951fcda8cb6a3f5c25f3659f5330ac3f2201bf9 (MoSA 2025) - Uses expert-choice routing to select tokens for attention.
  - 53a803388e83ae89261624099d7be4287ace67cb (DeepSeek-V2 2024) - Uses Multi-head Latent Attention (MLA) to compress KV cache in conjunction with MoE.
- Why it matters: The initial proposal (routing queries to experts) has significant collision risk. Novelty must move beyond simple head or token selection.
- Caveat: The specific mechanism of *what* is being routed (heads vs tokens vs latent vectors) is the key differentiator.
