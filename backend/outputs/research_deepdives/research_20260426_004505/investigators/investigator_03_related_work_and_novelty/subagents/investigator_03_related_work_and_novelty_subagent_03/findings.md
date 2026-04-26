# Findings



## Finding: RNN limitations in long-sequence generation

- Claim: RNN-based encoder-decoder models often produce repetitive and incoherent phrases when handling long documents or summaries.
- Confidence: high
- Evidence:
  - 032274e57f7d8b456bd255fe76b909b2c1d7458e (A Deep Reinforced Model for Abstractive Summarization, 2017)
- Why it matters: This architectural bottleneck (recurrence-induced incoherence/repetition) serves as a primary motivator for the Transformer's attention-only mechanism, which allows for direct global dependencies.
- Caveat: This is an observation of the preceding paradigm (RNNs) rather than a direct critique of the Transformer itself.


## Finding: Expressiveness Gap in Linear Attention

- Claim: Linear attention mechanisms often lag behind Softmax attention in accuracy due to issues with injectivity and local modeling ability.
- Confidence: high
- Evidence:
  - 3c0c526d88d0eaa4df75fe0663c7c900fc47c02e (Bridging the Divide: Reconsidering Softmax and Linear Attention, 2024)
  - c5de6b78d5e7b668e4b456f1ecbca718c3c35649 (On the Expressiveness of Softmax Attention: A Recurrent Neural Network Perspective, 2025)
- Why it matters: This explains the 'why' behind the performance gap. Specifically, linear attention lacks the 'injective property' (leading to semantic confusion) and the 'effective local modeling' intrinsic to Softmax.
- Caveat: While the gap is identified, the trade-off between computational complexity and representational power is still a primary axis of tension.


## Finding: Collision - LaplacianFormer (Injective Linear Attention)

- Claim: The expressiveness/injectivity problem in linear attention is being addressed by kernel-based methods like LaplacianFormer.
- Confidence: high
- Evidence:
  - e62198fd44c62b890c99e738e02ec5064cd6ec93 (LaplacianFormer, 2026)
- Why it matters: This directly collisions with the 'global stream' part of the IL-LA proposal. LaplacianFormer uses a Laplacian kernel and 'provably injective feature maps' to solve the semantic confusion/injectivity gap. Any new proposal must differentiate itself by targeting what a global kernel approximation *cannot* do (e.g., high-frequency local structural modeling).
- Caveat: LaplacianFormer focuses on the mathematical properties of the kernel; it does not explicitly propose a dual-stream local-global hybrid for structural priors.


## Finding: Collision - Hybrid Local-Global Architectures

- Claim: Many existing hybrid architectures combine local (CNN) and global (Transformer) modules to address inductive bias gaps, but these are mostly applied to standard Vision Transformers (ViT) or CNN-Transformer hybrids, not specifically to solve the expressiveness/injectivity issues of *linear* attention.
- Confidence: high
- Evidence:
  - 40782f438e0b2defcfdb73a918e6c83f39c25cb8 (EViTIB, 2024)
  - 4cdcb855cf083ba7ce0762480e30e21452f93908 (Hybrid-RViT, 2025)
  - d56ba1f607998273da3e61aa1eb10f33e1682dc5 (ConvDeiT-Tiny, 2026)
- Why it matters: This clarifies the novelty boundary. While 'hybrid local-global' is a known pattern for ViTs, applying it specifically to *repair the mathematical failures* of linear attention (injectivity and local feature capture) remains a distinct and open research direction.
- Caveat: The 'hybrid' concept is widely used; the novelty must lie in the *mechanism* of repair (e.g., how the local stream specifically compensates for the linear kernel's lack of injectivity).
