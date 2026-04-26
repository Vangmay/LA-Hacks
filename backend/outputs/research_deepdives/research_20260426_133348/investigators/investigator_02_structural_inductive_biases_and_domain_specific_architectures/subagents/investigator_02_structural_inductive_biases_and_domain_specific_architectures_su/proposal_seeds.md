# Proposal Seeds



## Proposal Seed: Dynamic Relative-Distance Inductive Biases for Structural Auditing

- Status: raw
- Originating taste: Component Efficiency Auditor
- Seed-paper hook: Section 3.5 'Positional Encoding' mentions the model contains no recurrence or convolution, thus using absolute encodings.
- Evidence trigger: The lack of inherent structural awareness in the dot-product attention mechanism relative to tokens.
- Candidate novelty: Replace static sine/cosine encodings with a learned, component-specific relative bias that is gated by task-specific structural signals (e.g., 2D grid distance for images vs sentence dependency distance for text).
- Technical mechanism: Learnt scalar biases added to the attention logit, parameterizing the 'structural hardness' of the block.
- Closest prior-work collision: Relative Positional Encodings (Shaw et al. 2018), ALiBi (Press et al. 2022).
- Closest future-work collision: Rotary Embeddings (RoPE).
- Minimum validation: Measure the entropy of attention maps when the bias is removed vs when it is gated; check if 'structural' layers actually use the distance bias.
- Falsification risk: If the model learns to zero-out the bias on all tasks, then the structural bias is redundant.
- Why this is not generic: It specifically targets the auditor's goal of checking if a structural component (the bias) is 'load-bearing' or just 'prestige complexity'.
- Confidence: low
- Required next search: Search for 'ablation study of relative vs absolute positional encodings' to find where they fail.


## Proposal Seed: Manifold-Preserving Sequence Linearization for Non-Euclidean Transformers

- Status: raw
- Originating taste: Geometric-Invariance Cartographer
- Seed-paper hook: LOOPE: Learnable Optimal Patch Order in Positional Embeddings for Vision Transformers (Chowdhury et al., 2025)
- Evidence trigger: LOOPE shows that standard 2D-to-1D patch ordering in ViTs is sub-optimal and that a 'Three Cell Experiment' reveals a 30-35% performance gap in positional information retention that standard benchmarks miss.
- Candidate novelty: Extending learnable ordering beyond 2D grids to non-Euclidean manifolds (graphs, meshes) where the 'natural' sequence order is non-existent. Current Graph Transformers typically use Laplacian Eigenvectors or Random Walks as PEs, but they don't optimize the *linearization sequence* that the Transformer processes.
- Technical mechanism: Formulate an optimization problem where the 1D ordering of tokens for the attention block is learned as a permutation matrix that minimizes the distortion between the original manifold distance and the 1D sequence distance (e.g., a learnable Hilbert-curve or Fiedler-vector equivalent).
- Closest prior-work collision: Graph Transformer (Dwivedi & Bresson, 2020) uses PEs but fixed token order; LOOPE (2025) optimizes 2D grid order.
- Closest future-work collision: Future iterations of ViT that incorporate 2D spatial locality more deeply (like Swin), though they usually constrain attention rather than the input order.
- Minimum validation: Compare against standard Graph Transformers on ZINC or QM9 using the 'Three Cell Experiment' adapted for graphs (testing if the model can reconstruct adjacency from ordering).
- Falsification risk: If global attention is truly 'all you need,' the 1D ordering might only matter for efficiency/caching, not representation, which would invalidate the need for complex linearization.
- Why this is not generic: It targets the specific mathematical disconnect between non-Euclidean adjacency and the 1D sequential input required by the Transformer's implementation.
- Confidence: low
- Required next search: Search for 'Graph Transformer sequence ordering' or 'Tokenization of manifolds' to see if anyone has optimized the input permutation itself.


## Proposal Seed: Dynamic Inductive Bias Modulation based on Local Focus Ratio

- Status: raw
- Originating taste: Domain-Limit Prospector
- Seed-paper hook: 'The Inductive Bias Gap' (Gong et al., 2026) highlights that ViTs fail in FER because global attention cannot concentrate on local action units.
- Evidence trigger: The 'Local Focus Ratio' metric reveals that CNNs succeed where ViTs fail due to architectural alignment with local features.
- Candidate novelty: Instead of hard-coding convolutions (like ConvDeiT), we propose a 'Structural Saliency Gate' that computes a task-specific sparsity mask over the attention matrix during early layers, effectively 'learning' the convolutional bias.
- Technical mechanism: Implement a lightweight sub-network that predicts a soft-locality mask $(M)$ such that $Attention = Softmax(QK^T / \sqrt{d}) \odot M$. The mask $M$ is constrained by a learned 'Focus Prior' that penalizes long-range tokens in layers where structural scarcity is high.
- Closest prior-work collision: ConvDeiT-Tiny (Waema et al., 2026) uses parallel depthwise convolutions; Swin Transformers use fixed windows.
- Closest future-work collision: 2026 conference work on hybrid ViTs for medical imaging likely uses similar local-global fusions.
- Minimum validation: Test on the FER dataset using the 'Local Focus Ratio' as an ablation metric to see if the learned mask outperforms fixed windows or parallel convolutions.
- Falsification risk: If the gate collapses to either pure global or pure local focus regardless of task, the mechanism is not providing adaptive value.
- Why this is not generic: It bridges the gap between fixed architectural bias (CNN) and zero bias (ViT) by making the 'Inductive Bias' a learnable, task-conditioned parameter derived from spatial saliency.
- Confidence: medium
- Required next search: Search for 'learnable locality constraints in Vision Transformers' or 'dynamic window attention' to ensure this specific gating mechanism hasn't been saturated.


## Proposal Seed: Spectral-Domain Attention for Riemannian Manifold Transformers

- Status: promising
- Originating taste: Geometric-Invariance Cartographer
- Seed-paper hook: Equivariant Spherical Transformer (An et al., 2025)
- Evidence trigger: EST (2025) successfully applies attention in the Fourier domain for SO(3) equivariance on spheres, but current models are limited to specific, highly-symmetric groups like SE(3)/SO(3).
- Candidate novelty: Generalizing Fourier-domain attention to arbitrary Riemannian manifolds using the Laplace-Beltrami operator's eigenfunctions. While 'spectral graph convolution' exists, 'spectral manifold attention'—performing the attention reduction step across the manifold's spectral coefficients—remains underexplored for non-graph, continuous manifold data.
- Technical mechanism: Compute the Laplace-Beltrami spectrum for a given manifold; transform the input signal into this spectral basis; define an attention mechanism where the 'keys' and 'queries' are low-pass filtered spectral coefficients. This ensures that the attention mechanism is invariant to the coordinate-system choice on the manifold (isometry invariance).
- Closest prior-work collision: Spectral Graph Transformers (e.g., Kreuzer et al., 2021) use spectral PEs but perform attention in the spatial/node domain. EST (2025) performs attention in the spectral domain but only for spheres.
- Closest future-work collision: Geometric deep learning papers moving toward general SE(n) or Gauge equivariance.
- Minimum validation: Test on 3D shape matching (FAUST/SCAPE) where isometries are common. Compare against standard ViTs and Spatially-operating GNNs.
- Falsification risk: The computational cost of computing the Laplace-Beltrami spectrum may outweigh the efficiency gains of Fourier-domain attention compared to spatial attention with positional encodings.
- Why this is not generic: It moves the core Transformer operation (reduction over dependencies) into the manifold's intrinsic coordinate system, unlike general 'manifold deep learning' which usually just applies CNNs to local patches.
- Confidence: medium
- Required next search: Search for 'Manifold Laplace-Beltrami Transformer' or 'Intrinsic attention on manifolds'.


## Proposal Seed: Manifold-Constrained Geometric Transformers for Global Shape Consistency

- Status: promising
- Originating taste: Domain-Limit Prospector
- Seed-paper hook: Buzea et al. (2026) show that Transformers/GANs fail on Euclidean shapes (global consistency) while succeeding on fractals (local self-similarity).
- Evidence trigger: Huang et al. (2024) use manifold constraints to align CNN and Transformer features for medical segmentation, suggesting that raw attention lacks the geometric rigidity needed for structured domains.
- Candidate novelty: We propose a 'Differential Geometric Regularizer' that penalizes attention maps that violate the projected manifold curvature of the underlying task (e.g., 3D skeleton in FER or medical volumes).
- Technical mechanism: Define a manifold-aware loss $\mathcal{L}_{geo}$ that computes the pairwise distance between tokens in a pre-trained embedding space $(E)$ and enforces that the Attention weights $(A)$ must satisfy the triangle inequality or a graph-Laplacian constraint relative to $(E)$. This forces global attention to respect the 'Euclidean geometry' that Buzea et al. found missing.
- Closest prior-work collision: VGGT (Visual Geometry Grounded Transformer, Lee et al. 2025) uses loop closure and SVD for scaling, but does not regularize the attention mechanism internally for shape consistency.
- Closest future-work collision: Huang et al. (2024) uses manifold constraints for inter-student alignment, not as an internal structural bias for the attention weights themselves.
- Minimum validation: Replicate the 'Euclidean shapes' failure case from Buzea et al. (2026) and show that the manifold-constrained attention reduces the global consistency violations.
- Falsification risk: The regularizer might be too rigid, causing the model to lose its 'scale-repeating' advantage on fractal-like natural data.
- Why this is not generic: It specifically targets the 'global-local' asymmetry identified in recent generative failure studies by introducing a formal metric-space constraint into the attention dot-product.
- Confidence: medium-high
- Required next search: Search for 'Riemannian transformers' or 'attention regularization via manifold learning' to ensure the internal weight penalty approach is novel.


## Proposal Seed: Rank-Adaptive Attention Projections via Structural Gating

- Status: promising
- Originating taste: Component Efficiency Auditor
- Seed-paper hook: Section 3.2.2 'Multi-Head Attention' uses fixed-rank projections (d_k = d_v = d_model / h).
- Evidence trigger: TransAct (2024) shows intra-module redundancy exists in modern MHA, and Michel et al. (2019) show full-head redundancy at inference.
- Candidate novelty: Instead of post-training pruning or fixed low-rank layers, implement a 'structural gate' that dynamically adjusts the rank (k) of the key/query projections during training based on a sparsity-inducing regularizer.
- Technical mechanism: Decompose W_q, W_k, W_v into U*S*V (SVD-like) where S is a learned diagonal gate; apply L1 penalty to S to identify which rank dimensions are 'load-bearing'.
- Closest prior-work collision: LoRA (Hu et al. 2021) for fine-tuning; but this proposal targets the *pre-training* or initial architecture to find the 'minimal necessary structure'.
- Closest future-work collision: Matryoshka Embeddings / Adaptive Rank LLMs.
- Minimum validation: Train on GLUE/WMT14; compare performance vs parameter count when gating is active; visualize the 'rank profile' of each layer to see if early/late layers naturally prefer lower rank.
- Falsification risk: If the model always learns full-rank projections despite the penalty, then the 2017 Transformer's fixed rank is actually optimal.
- Why this is not generic: It moves beyond 'improving efficiency' to 'auditing the internal rank requirement' of the Attention mechanism itself.
- Confidence: medium
- Required next search: Search for 'rank-adaptive pre-training transformers' to check for existing collisions.
