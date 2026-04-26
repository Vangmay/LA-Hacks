# Proposal Seeds



## Proposal Seed: Structural Inductive Bias via Differentiable Topology Masks

- Status: raw
- Originating taste: Citation-Ancestry Cartographer
- Seed-paper hook: The Transformer (204e3073870fae3d05bcbc2f6a8e263d9b72e776) succeeds by removing structural priors (recurrence/convolution), but this 'topology-blind' nature may be an inefficiency for structured data.
- Evidence trigger: The tension between the scalability of the Transformer and the high performance of `Structured Attention Networks` (13d9323a8716131911bfda048a40e2cde1a76a46) which incorporates richer structural dependencies at a potential cost to scale.
- Candidate novelty: Instead of unconstrained self-attention, use a mechanism that learns a sparse, differentiable structural mask (a topology) that constrains attention to a meaningful graph/tree, maintaining parallelization while re-introducing inductive bias.
- Technical mechanism: A lightweight topology-predictor (e.g., using hierarchical pooling or a small MLP over latent representations) that outputs a sparse adjacency matrix, which is then used as a mask for the self-attention operation.
- Closest prior-work collision: Graphormer, Tree-Transformer, or various sparse attention models (e.g., BigBird, Reformer).
- Closest future-work collision: Efficient attention mechanisms that incorporate structural knowledge.
- Minimum validation: Comparative study on dependency parsing or hierarchical document classification tasks, measuring whether learned masks improve sample efficiency or convergence rate compared to a vanilla Transformer.
- Falsification risk: The learned topology might collapse to a local sliding window (effectively becoming a CNN) or an identity matrix, providing no benefit over existing sparse attention methods.
- Why this is not generic: It specifically addresses the 'topology-blindness' of the Transformer by attempting to merge the scalability of unstructured attention with the expressive structural priors of early attention-based graphical models.
- Confidence: low
- Required next search: Collision search for 'learned sparse attention masks' and 'topology-aware Transformers' to differentiate from Graphormer and sparse attention variants.


## Proposal Seed: Stable Structural Inductive Bias: Decoupled Topology Learning for Transformers

- Status: promising
- Originating taste: Citation-Ancestry Cartographer
- Seed-paper hook: The Transformer (204e3073870fae3d05bcbc2f6a8e263d9b72e776) is topology-blind. While learned sparse attention (e.g., Sparsifiner) attempts to recover this, it risks 'Routing Absorption' (09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a) due to per-query co-adaptation.
- Evidence trigger: The 'Routing Absorption' finding shows that per-query gates are ineffective, but 'Coarse-to-Fine' architectures (VSA, RocketKV) and 'Layer-wise Profiling' (SVOO) show that stable, multi-scale structural information is a viable and efficient way to manage complexity.
- Candidate novelty: Instead of per-query token-level gating, learn a **stable, layer-wise or block-wise structural mask** (a 'topology') that is decoupled from the fine-grained Q/K/V projections. This topology is discovered in a coarse-grained stage and then applied as a non-differentiable or weakly-differentiable mask in the fine-grained stage.
- Technical mechanism: A two-stage 'Topology Discovery' module: (1) A lightweight 'Coarse Topology Predictor' (e.g., operating on pooled/low-res features) that outputs a sparse, structured adjacency matrix (e.g., a tree or a sparse graph) for each layer. (2) A 'Fine-Grained Attention' module that uses this stable layer-wise mask to constrain token-level attention, ensuring that the structural prior is a stable architectural constraint rather than a volatile per-query signal.
- Closest prior-work collision: Graphormer (uses fixed/domain graphs), Sparsifiner (uses per-query gating), HSA-Transformer (uses dynamic gating).
- Closest future-work collision: Research into 'post-hoc sparsification' or 'hardware-aware routing' that decouples representation from sparsity.
- Minimum validation: Compare 'Stable Topology Masking' against vanilla Transformers and 'Per-Query Gated' Transformers on tasks requiring structural reasoning (e.g., dependency parsing, hierarchical document classification). Measure convergence rate and sample efficiency to prove the avoidance of 'Routing Absorption'.
- Falsification risk: The 'stable' topology might be too coarse to capture necessary fine-grained dependencies, or the 'Topology Predictor' itself might become a bottleneck.
- Why this is not generic: It specifically targets the *methodological failure* of end-to-end per-query gating by proposing a decoupled, hierarchical, and stable structural discovery mechanism.
- Confidence: medium
- Required next search: Collision search for 'layer-wise learned structural priors' and 'decoupled topology-aware Transformers'.
