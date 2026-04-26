# Findings



## Finding: Architectural Motivation for Transformers

- Claim: The shift toward Transformer architectures was fundamentally driven by the need for greater parallelization in sequence transduction compared to recurrent and convolutional models.
- Confidence: high
- Evidence:
  - Paper 43428880d75b3a14257c3ee9bda054e61eb869c0 (Convolutional Seq2Seq) notes that computations can be fully parallelized during training, easing optimization.
  - Seed paper (204e3073870fae3d05bcbc2f6a8e263d9b72e776) explicitly proposes dispensing with both recurrence and convolutions to achieve superior quality and parallelization.
- Why it matters: Establishes the Transformer not just as a new model, but as the culmination of a trend toward removing sequential dependencies in NMT architectures.
- Caveat: While parallelization is a major advantage, the Transformer's performance gain is also attributed to the specific way the attention mechanism models long-range dependencies.


## Finding: The Routing Absorption Barrier

- Claim: End-to-end learning of sparse attention masks via per-query gating is fundamentally hindered by 'routing absorption,' where the model co-adapts to the mask, rendering learned gates no better than random ones.
- Confidence: high
- Evidence:
  - Paper 09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a (Routing Absorption in Sparse Attention) demonstrates that differentiable soft gating converges to similar perplexity regardless of whether the gate is learned or random.
  - The paper highlights that shared Q/K/V parameters in Transformers allow for cross-layer compensation, making this absorption more severe than in MoE.
- Why it matters: This finding provides a critical 'novelty pressure' for any proposal involving learned sparsity. A simple 'connectivity predictor' module is likely to fail if it follows the end-to-end gating paradigm.
- Caveat: The paper suggests that decoupling representation learning from sparsification (post-hoc approaches) can sidestep this, providing a clear direction for research.


## Finding: Coarse-to-Fine Sparsification as an Alternative to Per-Query Gating

- Claim: Two-stage or hierarchical (coarse-to-fine) sparsification mechanisms may circumvent the 'Routing Absorption' problem inherent in fine-grained, per-query gating.
- Confidence: medium
- Evidence:
  - Paper d97deccf2ff8a8f77cb65294b507c26fcf266712 (VSA) uses a coarse stage to identify critical tokens before fine-grained attention, allowing for end-to-end training in video diffusion.
  - Paper f014aa430c330d263b0e7dd0fe5820a2978cac7e (RocketKV) employs a coarse-grain permanent eviction followed by fine-grain top-k attention for LLM KV cache compression.
- Why it matters: This suggests that instead of trying to learn a complex, high-resolution mask for every query (which causes co-adaptation), research should focus on learning a more stable, low-resolution 'topology' or 'coarse mask' that then guides fine-grained attention.
- Caveat: While these papers show success, they are specialized (video diffusion, KV cache) or use specific hardware/task constraints. Generalizing this to an end-to-end Transformer architecture for general sequence transduction requires ensuring the coarse stage itself doesn't fall prey to absorption or excessive complexity.
