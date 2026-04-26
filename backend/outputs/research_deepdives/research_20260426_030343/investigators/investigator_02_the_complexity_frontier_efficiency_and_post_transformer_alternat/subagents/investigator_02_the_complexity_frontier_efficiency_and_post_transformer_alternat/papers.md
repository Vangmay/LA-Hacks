# Papers



## Foundational SSMs

## Paper: Mamba: Linear-Time Sequence Modeling with Selective State Spaces

- Paper ID: 7bbc7595196a0606a07506c4fb1473e5e87f6082
- Year: 2023
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: foundational_work
- Why it matters: Addresses the inability of previous SSMs to perform content-based reasoning by making SSM parameters functions of the input (selective SSMs). Enables linear-time sequence modeling with high throughput and performance competitive with Transformers.
- Caveat: The efficiency gains are heavily tied to specific hardware-aware parallel algorithms in recurrent mode.


## Minitron-SSM

## Paper: Minitron-SSM: Efficient Hybrid Language Model Compression through Group-Aware SSM Pruning

- Paper ID: ARXIV:2504.11409
- Year: 2025
- Source bucket: serpapi
- Found by: google_scholar_search
- Relation to seed: recent_followup
- Why it matters: Investigates efficient SSM pruning for hybrid language models, specifically addressing long-context support and linear-time complexity. Directly relevant to the 'efficiency' and 'post-transformer' search targets.
- Caveat: Focused on compression/pruning rather than fundamental architecture design.


## Foundational SSMs

## Paper: Efficiently Modeling Long Sequences with Structured State Spaces

- Paper ID: ac2618b2ce5cdcf86f9371bcca98bc5e37e46f51
- Year: 2021
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: foundational_work
- Why it matters: Introduces the Structured State Space (S4) model. Uses a new parameterization (low-rank correction to the A matrix) to allow stable diagonalization and efficient computation via Cauchy kernels. Solves the long-range dependency problem that previous SSMs struggled with.
- Caveat: The efficiency is contingent on the specific structured parameterization of the state matrix A.


## PerfMamba

## Paper: PerfMamba: Performance Analysis and Pruning of Selective State Space Models

- Paper ID: ARXIV:2511.22849
- Year: 2025
- Source bucket: serpapi
- Found by: google_scholar_search
- Relation to seed: recent_followup
- Why it matters: Analyzes and prunes Selective State Space Models (SSMs) like Mamba, focusing on their linear scaling and efficient sequence modeling. Relevant to the efficiency/compression aspect of post-transformer alternatives.
- Caveat: Primarily focuses on pruning/compression of existing SSMs.


## Foundational SSMs

## Paper: How to Train Your HiPPO: State Space Models with Generalized Orthogonal Basis Projections

- Paper ID: a30ac45ac5b7bd2148d3fb80ee7f3c29724e3170
- Year: 2022
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: foundational_work
- Why it matters: Introduces the HiPPO (High-order Polynomial Projection Operators) framework, which provides a principled way to initialize state-space models to capture long-range dependencies via orthogonal polynomial projections. This is a key mathematical building block for S4.
- Caveat: The complexity of the HiPPO initialization must be managed to remain efficient in deep learning training.


## UniQL

## Paper: UniQL: Unified Quantization and Low-rank Compression for Adaptive Edge LLMs

- Paper ID: ARXIV:2512.03383
- Year: 2025
- Source bucket: citation
- Found by: get_citations (Minitron-SSM)
- Relation to seed: recent_followup
- Why it matters: Provides a unified framework for quantization and low-rank compression across Transformers, SSMs, and hybrid models (e.g., Nemotron-H, Bamba-v2). Highlights the move towards adaptive, edge-deployable hybrid models.
- Caveat: Focuses on post-training compression rather than pre-training architectural efficiency.


## Recent Mathematical Formalisms

## Paper: Mathematical Formalism for Memory Compression in Selective State Space Models

- Paper ID: e9790ffb00166c9174bff0efd29c8080f49946b4
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Provides a rigorous mathematical framework for understanding how selective gating allows for memory compression. Uses information-theoretic tools (mutual information, rate-distortion theory) to bound information retention and derives theorems for stability and convergence in selective SSMs.
- Caveat: Focuses on the mathematical formalization of compression rather than the hardware-aware implementation details.


## Nemotron Elastic

## Paper: Nemotron Elastic: Towards Efficient Many-in-One Reasoning LLMs

- Paper ID: ARXIV:2511.16664
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: direct_match
- Why it matters: Proposes a 'nested submodel' framework where multiple scales (e.g., 12B, 9B, 6B) coexist in a single parent model. Introduces 'group-aware SSM elastification' for hybrid Mamba-Attention models, significantly reducing training costs for model families. This represents a shift from post-training compression to architecturally-integrated elasticity.
- Caveat: Focuses on scaling the model family via nesting rather than reducing the base cost of a single-scale model.


## Foundational Lineage Bridges

## Paper: On the Relation of State Space Models and Hidden Markov Models

- Paper ID: 71dc8a8a75f19b87e9b1712de70979d2b22e1ac9
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Provides a systematic comparison between classical probabilistic models (HMMs, Kalman filtering) and modern deterministic NLP SSMs (S4, Mamba). Clarifies equivalence and divergence points between control theory/probabilistic modeling and deep learning sequence models.
- Caveat: High-level theoretical comparison; may not detail modern hardware-specific optimizations.


## Theoretical Foundations

## Paper: Theoretical Foundations of Deep Selective State-Space Models

- Paper ID: 917096f28209ef90c9e6363cf49438341120af5e
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Provides a breakthrough mathematical connection between selective SSMs and **Rough Path Theory**. It shows that the hidden state in models like Mamba is a low-dimensional projection of the **signature** of the input, which captures non-linear interactions between tokens at different timescales. This provides a formal grounding for why selectivity enables high expressivity.
- Caveat: The connection is theoretical and uses complex mathematical objects (signatures) that might be difficult to directly optimize or interpret in standard training loops.


## Jamba-1.5

## Paper: Jamba-1.5: Hybrid transformer-mamba models at scale

- Paper ID: ARXIV:2408.12570
- Year: 2024
- Source bucket: serpapi
- Found by: google_scholar_search
- Relation to seed: direct_match
- Why it matters: Discusses hybrid Mamba-2 and Attention architectures at scale. Notes that hybrid architectures can outperform pure Mamba-2, providing empirical evidence for the viability of hybrid designs in large-scale models.
- Caveat: Focuses on scale/performance rather than a deep dive into specific reasoning bottlenecks.


## Tiny recursive reasoning

## Paper: Tiny recursive reasoning with mamba-2 attention hybrid

- Paper ID: ARXIV:2602.12078
- Year: 2026
- Source bucket: serpapi
- Found by: google_scholar_search
- Relation to seed: recent_followup
- Why it matters: Investigates whether reasoning capabilities can be maintained in much smaller scales by replacing Transformer blocks with Mamba-2 hybrid operations. Challenges the 'massive scale' requirement for reasoning.
- Caveat: Very recent work; results may need broader validation.


## Recent Architectures

## Paper: SeRpEnt: Selective Resampling for Expressive State Space Models

- Paper ID: 4f7f40e068887ece27b2dc26b5467a223f4b5062
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Proposes an architecture that exploits selectivity to compress sequences in an information-aware fashion using a resampling mechanism. It claims that selective time intervals in Mamba act as linear approximators of information.
- Caveat: It is a very recent work (2025) and its long-term impact on the field is yet to be seen.


## Apriel-h1

## Paper: Apriel-h1: Towards efficient enterprise reasoning models

- Paper ID: ARXIV:2511.02651
- Year: 2025
- Source bucket: serpapi
- Found by: google_scholar_search
- Relation to seed: recent_followup
- Why it matters: Explores hybrid LLMs combining Transformer attention and SSMs for enterprise reasoning tasks. Suggests that large-scale hybrid models are a viable path for efficient reasoning.
- Caveat: Focuses on enterprise efficiency rather than fundamental architecture theory.


## Unified Frameworks

## Paper: Understanding the differences in Foundation Models: Attention, State Space Models, and Recurrent Neural Networks

- Paper ID: 9036b781226f584c89c04fc2b447752e3324c084
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Introduces the **Dynamical Systems Framework (DSF)**, a common representation for comparing Attention, SSMs, and RNNs. It provides conditions under which linear attention and selective SSMs are equivalent and discusses how softmax attention can be approximated by other classes.
- Caveat: Focuses on establishing the common framework and conditions of equivalence rather than the deep architectural optimization of each.


## Nemotron Nano 2

## Paper: NVIDIA Nemotron Nano 2: An Accurate and Efficient Hybrid Mamba-Transformer Reasoning Model

- Paper ID: ARXIV:2508.14444
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: direct_match
- Why it matters: Demonstrates that a hybrid Mamba-Transformer architecture (Nemotron-Nano-9B-v2) can achieve on-par or better accuracy on reasoning benchmarks while providing up to 6x higher inference throughput in long-context reasoning settings (8k input, 16k output). This is a primary piece of evidence for the effectiveness of hybrid models in the reasoning domain.
- Caveat: Performance is specifically noted for long-context/long-thinking-trace workloads.


## Unified Frameworks

## Paper: How Many Heads Make an SSM? A Unified Framework for Attention and State Space Models

- Paper ID: 83485e76d4cfebcdbb277b5c4f6044285b58b41c
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: recent_followup
- Why it matters: Proposes a unified framework using an input-dependent effective interaction operator. It establishes the **Interaction Rank Gap** (attention-style mixing is constrained to low-dimensional operator spans) and an **Equivalence (Head-Count) Theorem** (representing a $k$-dimensional linear SSM requires $H=k$ heads). It also highlights a fundamental trade-off: attention layers allow distance-independent gradient paths, while stable linear dynamics (SSMs) exhibit distance-dependent gradient attenuation.
- Caveat: The framework is high-level and formalizes trade-offs rather than providing specific implementation heuristics.
