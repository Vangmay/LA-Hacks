# Hand-Off: Novelty Ideation for Transformer Structural Priors

## Research Summary
The investigation focused on the tension between the Transformer's 'topology-blind' scalability and the need for structural inductive biases. Initial ideas for per-query learned masks were critically challenged by the discovery of 'Routing Absorption,' where model co-adaptation renders learned gates ineffective. The research pivoted toward a decoupled, hierarchical, and stable topology-learning mechanism.

## Buckets Filled
- `seed_metadata`: Transformer (204e3073870fae3d05bcbc2f6a8e263d9b72e776)
- `closest_prior_work`: Convolutional Seq2Seq (43428880d75b3a14257c3ee9bda054e61eb869c0)
- `direct_followups` & `recent_followups`: VSA (d97deccf2ff8a8f77cb65294b507c26fcf266712), Sparsifiner (19921cefb2470b2f5d984ab9ce92ebb94aedf2ea), HSA-Transformer (526c95957298a04ffcec5aa9a54dd64b7f2dcc10), SVOO (1a1b3666d85208f9773fb04c2b675154ad8cf42f).
- `critiques_limitations`: Routing Absorption (09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a).
- `research_gaps`: The gap between training-free layer-wise profiling and effective end-to-end learned structural priors.

## Top Papers & Why They Matter
- **Routing Absorption (09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a)**: The most important paper in this run. It provides the 'novelty pressure' by proving that naive per-query gating fails due to co-adaptation.
- **VSA (d97deccf2ff8a8f77cb65294b507c26fcf266712)**: Suggests a coarse-to-fine architectural path that may avoid absorption by using stable, low-resolution topology information.
- **SVOO (1a1b3666d85208f9773fb04c2b675154ad8cf42f)**: Demonstrates the utility of layer-wise heterogeneity in sparsity, supporting the shift from per-query to layer/block-wise stability.

## Strongest Novelty Implications
- **From Per-Query to Per-Layer/Block**: Novelty lies in shifting the focus of learned sparsity from volatile per-query tokens to stable, learned structural invariants (topologies) that constrain the attention mechanism.
- **Decoupled Discovery**: The 'Routing Absorption' barrier implies that the discovery of sparsity patterns must be decoupled from the fine-grained representation learning (Q/K/V projections) to prevent co-adaptation.

## Candidate Spinoff Proposal Seeds
### Proposal Seed: Stable Structural Inductive Bias: Decoupled Topology Learning for Transformers
- **Core Idea**: A two-stage mechanism where a lightweight 'Coarse Topology Predictor' learns a stable, layer-wise/block-wise sparse adjacency matrix (a 'topology') that is then used as a structural constraint for fine-grained self-attention.
- **Evidence Basis**: The failure of per-query gating (Routing Absorption) and the success of hierarchical/coarse-to-fine methods (VSA, RocketKV).
- **Mechanism**: Coarse stage (pooling/low-res) $\to$ Topology Predictor $\to$ Stable Mask $\to$ Fine-grained Attention (constrained by mask).
- **Confidence**: Medium (requires proving that the 'topology' can be learned end-to-end without being absorbed itself).

## Contradictions & Uncertainty
- **Absorption in Coarse Stages**: It is uncertain whether a coarse-grained topology predictor is also susceptible to routing absorption, or if the lower resolution of the topology provides enough 'asymmetry' to prevent it.
- **Generalization**: Most current successes in hierarchical/sparse attention are task-specific (video, medical, circuit); generalizing a stable topology learner to general sequence-to-sequence tasks remains unproven.

## Recommended Next Steps for Investigator
1. **Collision Check**: Perform an adversarial search for 'decoupled topology-aware Transformers' or 'stable layer-wise sparse attention' to ensure the 'Decoupled Topology Learning' idea is not already claimed.
2. **Implementation Sketch**: Design a toy experiment comparing a per-query gate (to demonstrate absorption) vs. a layer-wise learned mask (to test stability/convergence) on a simple dependency parsing task.