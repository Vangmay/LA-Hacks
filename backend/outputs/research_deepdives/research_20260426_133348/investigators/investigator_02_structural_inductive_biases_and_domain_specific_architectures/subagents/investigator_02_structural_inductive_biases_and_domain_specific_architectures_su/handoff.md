# Hand-Off

## Research Overview
Investigated the **structural inductive biases** of the Transformer architecture, focusing on identifying redundant components and exploring their necessity. The research followed an 'Ablation-to-Theory' path, moving from empirical pruning evidence to architectural design proposals.

## Top Papers & Evidence
- **Vaswani et al. (2017) [204e30738]**: The seed paper. Established the reliance on positional encodings due to the permutation-invariant nature of self-attention.
- **Michel et al. (2019) [b03c7ff96]**: 'Are Sixteen Heads Really Better than One?' - Provided critical evidence that multi-head attention is massively redundant post-training, with many layers reducible to a single head.
- **Shen et al. (2024) [c2d2dbb6b]**: 'TransAct' - Identified that redundancy persists in modern LLMs (LLaMA) at the intra-module activation level, suggesting the fixed-rank projection bias is a primary efficiency bottleneck.

## Key Findings
1.  **MHA as a Regularizer**: Multi-head attention may act more as an optimization/training aid (the 'lottery ticket' effect) than as a structural necessity for the final representation.
2.  **Intra-Module Slack**: There is significant 'unstructured' redundancy within the projection weights of MHA, which can be compressed into low-rank forms without damaging performance.
3.  **Positional Encoding Fragility**: The requirement for external positional information remains the architecture's most sensitive structural bias, yet it is often handled with generic sine/cosine functions rather than being task-audited.

## Proposal Seeds

### ## Proposal Seed: Rank-Adaptive Attention Projections via Structural Gating
- **Core Idea**: Use sparsity-inducing SVD-like gates on W_q, W_k, W_v during training to dynamically determine the 'minimal necessary rank' for each layer.
- **Evidence Basis**: Based on Michel et al. (2019) head redundancy and Shen et al. (2024) intra-module low-rank findings.
- **Novelty Claim**: Moves from post-training pruning to dynamic 'structural auditing' during pre-training to find the minimalist version of the Transformer for a specific task.
- **Confidence**: Medium (Requires search for pre-training collisions).

### ## Proposal Seed: Dynamic Relative-Distance Inductive Biases
- **Core Idea**: Audit if 'structural hardness' biases (like distance-based gates) are load-bearing by implementing them as gated components that can be zeroed out.

## Recommended Next Steps
1.  **Collision Search**: Search specifically for 'rank-adaptive pre-training' to see if SVD-gates have been applied during initial LLM training.
2.  **Multi-Modal Audit**: Investigate if the same redundancy patterns hold in Vision Transformers (ViT) or if the 2D inductive bias makes heads more load-bearing.