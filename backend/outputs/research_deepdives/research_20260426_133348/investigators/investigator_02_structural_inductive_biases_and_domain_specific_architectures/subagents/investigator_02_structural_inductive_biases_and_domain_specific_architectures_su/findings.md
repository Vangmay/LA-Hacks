# Findings



## Finding: Reliance on Positional Encodings due to Permutation Invariance

- Claim: The Transformer's core structural bias is permutation invariance, necessitating external positional encodings to capture sequence order.
- Confidence: high
- Evidence:
  - 204e3073870fae3d05bcbc2f6a8e263d9b72e776 (Attention is All you Need, 2017)
- Why it matters: This is the primary structural 'failure' or 'omission' that subsequent domain-specific architectures (vision, graph) must address by injecting task-specific inductive biases (e.g., 2D coordinates or adjacency priors).
- Caveat: While permutation invariance is a 'feature' for sets, it requires heavy engineering for time-series or linguistic structures.


## Finding: Transformer Architecture-Task Mismatch in Fine-Grained Tasks

## Finding: Transformer Architecture-Task Mismatch in Fine-Grained Tasks

- Claim: Standard Vision Transformers (ViTs) often underperform compared to CNNs in tasks requiring precise local feature localization, such as Facial Expression Recognition (FER), due to a lack of task-aligned inductive bias.
- Confidence: high
- Evidence:
  - c16ab403e6ad7c01870a60f3e11f817c198a9e65 / "The Inductive Bias Gap: A Local-Focus Analysis of CNN’s Superiority over ViT in Facial Expression Recognition" / 2026 / relevance_search
- Why it matters: This highlights a structural limitation in the original Transformer's global multi-head self-attention mechanism when applied to domains where specific local action units (eyes, mouth) are critical. It suggests a gap for domain-specific structural biases.
- Caveat: This might be mitigated by massive scale (data/parameters), but the study shows persistent efficiency gaps in data-limited or detail-oriented settings.


## Finding: Domain-Specific Bias vs. Global Attention Efficiency

- Claim: Standard Transformers' lack of explicit geometric bias (e.g., SO(3) equivariance) is increasingly mitigated by moving the attention mechanism into specialized domains like spherical Fourier space.
- Confidence: high
- Evidence:
  - `e624095a92845f8bab49c00090f52d129d0f583b` (Equivariant Spherical Transformer, 2025)
  - `c39c90d9f70b0906e94ecf9e586739807dfea7d6` (Spacetime E(n)-Transformer, 2024)
- Why it matters: This indicates a shift from using Transformers as 'blank slates' to 'structured processors' where the math of the attention itself matches the group-theoretic properties of the input manifold. It reduces the computational 'inductive tax' of complex tensor products (like Clebsch-Gordan).
- Caveat: Theoretical proof of equivariance in these models often relies on specific sampling strategies (e.g., uniform spherical sampling) which might introduce aliasing errors not present in pure tensor-product GNNs.


## Finding: MHA Redundancy and Post-Training Prunability

- Claim: A significant proportion of attention heads in trained Transformers can be removed at inference time with minimal performance loss, often reducing layers to a single head.
- Confidence: High
- Evidence:
  - b03c7ff961822183bab66b2e594415e585d3fd09 (Are Sixteen Heads Really Better than One?, 2019)
- Why it matters: This serves as an empirical contradiction to the 'multi-head is essential' design choice. It suggests that the inductive bias of multi-head attention serves more as an optimization regularizer or 'lottery ticket' generator during training than as a structural necessity for the final representation.
- Caveat: The paper focuses on inference-time pruning; the structural necessity for the training phase remains an open question.


## Finding: Graph-Based Projection as a Substitute for Local Attention Bias

## Finding: Graph-Based Projection as a Substitute for Local Attention Bias

- Claim: Utilizing graph convolutional projection based on spatial adjacency matrices can effectively compensate for the lack of inductive bias in ViTs when trained on small datasets from scratch.
- Confidence: high
- Evidence:
  - 0c990d583635071db03565b9199ec9edfd80629c / "Graph-based vision transformer with sparsity for training on small datasets from scratch" / 2025 / relevance_search
- Why it matters: This indicates that the failure of global attention (as noted in Gong et al. 2026) can be mitigated not just by windowing, but by changing the projection mechanism to be graph-aware (local adjacency). This supports the possibility of more flexible 'learned' inductive biases.
- Caveat: Graph-pooling and projection might introduce computational overhead compared to standard windowed attention or depthwise convolutions.


## Finding: Inter-module vs Intra-module Redundancy

- Claim: While full head pruning (inter-module) was the early focus, modern evidence suggests that intra-module redundancy—specifically transitional activations within MHA and MLP blocks—is a more precise target for structural efficiency.
- Confidence: Medium (based on 2024 work on LLaMA)
- Evidence:
  - c2d2dbb6b2d82308a7a354468574623a378c4cc0 (TransAct, 2024)
- Why it matters: This shifts the 'Efficiency Auditor' focus from 'removing heads' to 'low-ranking the internals'. It implies that the 2017 Transformer's fixed-rank attention projections are an inflexible inductive bias that fails to adapt to varying layer-wise information density.
- Caveat: The efficacy of intra-module pruning may depend on the specific pre-training regime or scale of the model (e.g., LLaMA vs original Transformer).
