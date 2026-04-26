# Papers



## Paper: Attention is All You Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed paper itself.
- Why it matters: Establishes the Transformer architecture, which uses self-attention with O(n^2) scaling. This research deep dive focuses on sub-quadratic scaling and linear recurrence convergence as alternatives or improvements to this complexity.
- Caveat: Primarily demonstrates empirical superiority in MT; theoretical scaling limits are the target of this specific sub-agent investigation.


## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper (https://arxiv.org/abs/1706.03762)
- Relation to seed: Root paper defining the Transformer architecture.
- Why it matters: Introduces the O(N^2 * d) self-attention mechanism, creating the quadratic bottleneck that sub-quadratic scaling research (Linformer, Reformer, Performer, Mamba) aims to surpass. Serves as the complexity baseline for my investigation.
- Caveat: Performance gains are based on parallelizability over recurrence, but the N^2 memory and compute cost is the fundamental limit for long-context sequences.


## Paper: Attention is All you Need

- Paper ID: `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (ARXIV:1706.03762)
- Year: 2017
- Source bucket: `seed_metadata`
- Found by: `resolve_arxiv_paper` (initial seed)
- Relation to seed: Root paper defining the Transformer architecture.
- Why it matters: Establishes the O(N^2) attention mechanism that later work seeks to optimize. Its reliance on all-to-all attention creates the quadratic scaling bottleneck this investigation aims to address through sub-quadratic alternatives and recurrence-based approximations.
- Caveat: The original paper does not focus on linear recurrences; rather, it explicitly aims to replace recurrence with parallelizable attention.


## Paper: Mamba-3: Improved Sequence Modeling using State Space Principles

- Paper ID: `02cbf7c87d721ca17b3416d2360350092a21c2c8` (ARXIV:2603.15569)
- Year: 2026
- Source bucket: `recent_followups`
- Found by: `paper_relevance_search`
- Relation to seed: Direct successor in the sub-quadratic scaling lineage, optimizing the recurrence mechanisms derived from State Space Models (SSMs).
- Why it matters: Introduces a complex-valued state update rule and a multi-input, multi-output (MIMO) formulation to solve 'state tracking' failures in earlier linear models. It represents the latest state-of-the-art (SOTA) in tightening the efficiency-performance Pareto frontier for linear recurrences.
- Caveat: Relies on complex discretization which might introduce numerical stability issues in specific deep-stack configurations.


## Paper: On the Complexity of the Skolem Problem at Low Orders

- Paper ID: 33a53331ff99c23997849745cbe4f892316c9e91
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search (query: 'lower bound nth term linear recurrence complexity')
- Relation to seed: Investigates the decidability and complexity thresholds of linear recurrence sequences (LRS).
- Why it matters: The Skolem Problem (determining if an LRS has a zero) is central to understanding the limits of what a linear recurrence can 'detect' or 'represent' over time. Its complexity at low orders provides a ceiling for the expressive power of sub-quadratic architectures like Mamba or Linear Transformers that rely on such recurrences.
- Caveat: Focuses on mathematical decidability/zeros rather than approximate state representation, but high complexity or undecidability results here would imply fundamental bottlenecks in recurrence-based attention alternatives.


## Paper: Formal Synthesis of Lyapunov Neural Networks

- Paper ID: b25eb299067a5447e3afd550909e6127a07a34f5
- Year: 2020
- Source bucket: relevance_search
- Found by: paper_relevance_search (query: linear recurrence stability Control Theory Lyapunov)
- Relation to seed: Addresses the stability of neural-based dynamical systems, which is a key failure mode for linear recurrences attempting to replace quadratic attention.
- Why it matters: Proposes 'Lyapunov Neural Networks' (LNNs) to automatically find Lyapunov functions using SMT solvers. This provides a formal mechanism for ensuring asymptotic stability, which could be 'transplanted' (per my taste) into the weight-initialization or regularization of a sub-quadratic Transformer recurrence.
- Caveat: Focuses on autonomous non-linear systems; needs adaptation for the sequence-dependent inputs (non-autonomous) in Transformer contexts.


## Paper: On Computational Limits of Modern Hopfield Models

- Paper ID: 22910f92c164971ff6ae886ece9c586c703c7153
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search (query: '"sub-quadratic" sequence modeling complexity limits')
- Relation to seed: Direct investigation of computational limits for models that approximate attention (Hopfield/Transformers).
- Why it matters: Establishes a phase transition for efficiency based on the norm of patterns. Crucially, it proves that sub-quadratic variants are only possible under specific criteria (norm constraints), otherwise bounded by the Strong Exponential Time Hypothesis (SETH). This is a 'Sentinel' paper that provides exactly the impossibility framework I was looking for.
- Caveat: SETH-based lower bounds are conditional; however, they provide the strongest available theoretical justification for why sub-quadratic models might fail to replicate full attention performance in certain regimes.


## Paper: A Survey of State Space Models: From Linear Systems to Language

- Source bucket: `surveys`
- Found by: `google_scholar_search`
- Relation to seed: Provides the theoretical taxonomy for State Space Models (SSMs) as the primary linear-recurrence alternative to quadratic attention.
- Why it matters: Explicitly mentions 'Spectral SSMs' (Section 7.2), which validates the existence of literature connecting the spectral properties of linear systems to model performance. This is a crucial grounding for proposals involving eigenvalue-based optimization of recurrences.
- Caveat: This is a survey (Draft/PDF form seen); direct experimental validation of spectral switching may still be the novelty gap.


## Paper: Parallelization of Non-linear State-Space Models: LrcSSM

- Paper ID: e1e98a053a81b96d93c30a5c2b0f0f76b06f9571
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search (query: stability of State Space Models S4 Mamba)
- Relation to seed: Direct successor to the sub-quadratic scaling goal; explicitly contrasts with Mamba and Liquid-S4.
- Why it matters: Claims to solve a key gap identified in my proposal seed: the lack of formal gradient-stability guarantees in input-varying systems like Mamba. Uses a diagonal Jacobian constraint to achieve O(TD) complexity and O(log T) depth while providing a formal stability guarantee. This provides a 'competitor' or 'baseline' for my Lyapunov proposal, showing that stability is a peak research priority for 2025.
- Caveat: Uses diagonal Jacobian as the primary mechanism; my Lyapunov proposal (Proposal Seed 1) targets a more general structural stability constraint that could potentially work with non-diagonal transitions.
