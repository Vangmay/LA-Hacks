# Papers



## Paper: Attention is All you Need

- Paper ID: `204e3073870fae3d05bcbc2f6a8e263d9b72e776` 
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Root seed paper
- Why it matters: Introduces the Transformer architecture, the foundational model for this dive into sparse and dynamic computation. Key features include Scaled Dot-Product Attention and Multi-Head Attention, which replaced recurrence with a global dependency modeling mechanism that is notoriously O(n^2) in sequence length, motivating subsequent sparse-attention research.
- Caveat: Primarily addresses sequence transduction (translation) and parsing; sparse mechanisms are often follow-ups to combat its heavy memory/computation footprint in long-context scenarios.


## Paper: A Comprehensive Survey On Efficient Transformers

- Paper ID: `f8224bfd21a9c1f3d763a22c9a4d3d24e8676a2e` 
- Year: 2023
- Source bucket: surveys
- Found by: paper_relevance_search
- Relation to seed: Comprehensive overview of efficient attention mechanisms (sparse, linearized, low-rank) that evolved from the seed.
- Why it matters: Expressly identifies a gap in benchmark datasets for specific challenges like hierarchical reasoning on long-range sequences and key phrase extraction, which are critical for evaluating whether sparse mechanisms actually preserve reasoning capabilities.
- Caveat: Focuses on efficiency/performance; may lack the deepest hardware-level kernel optimization details preferred for mechanistic novelty.


## Paper: ReHub: Linear Complexity Graph Transformers with Adaptive Hub-Spoke Reassignment

- Paper ID: `593edb51e3f96e1d6624f91f99ee88e767187f45` 
- Year: 2024
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Evolution of the Transformer for graph-structured data using dynamic sparsity.
- Why it matters: Introduces a 'hub-and-spoke' model where nodes (spokes) are dynamically reassigned to virtual nodes (hubs). This 'adaptive reassignment' based on hub-hub similarity is a concrete technical mechanism for maintaining linear complexity while using a large number of 'global' hubs, bypassing the O(n*H) bottleneck of fixed virtual node models.
- Caveat: Evaluated on Large Graph Benchmark (LRGB); transferability to standard long-context NLP Transformers (which lack explicit graph priors) remains an open research question.


## Paper: MDSA-UNet: Multi-Scale Dynamic Sparse Attention UNet

- Paper ID: `478c30abad8d886ddb4fe14683ba8ebb205e311c` 
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Leverages the multi-scale potential of attention while introducing dynamic filtering of key-value pairs.
- Why it matters: Introduces a core mechanism for 'coarse-to-fine' filtering: irrelevant key-value pairs are filtered at a coarse-grained level before fine-grained self-attention. This hierarchical filtering is a strong technical parallel to the 'hub-spoke' reassignment seen in graph transformers, but applied to spatial/feature maps. It suggests that hierarchical 'gating' of attention is becoming a standard way to maintain performance in 2024-2025 models.
- Caveat: Applied to medical image segmentation; the challenge for LLMs is mapping this spatial 'coarse' filtering to temporal or semantic 'coarse' filtering in text.


## Paper: SADIMM: Accelerating Sparse Attention via Hardware-Software Co-design

- Paper ID: `6955f5609bb3a1d8bad8367c7db5ed63c88b28b2` 
- Year: 2025
- Source bucket: hardware_benchmarks
- Found by: paper_bulk_search
- Relation to seed: Addresses the memory-intensive nature of the Transformer's attention mechanism through near-memory processing (NMP).
- Why it matters: Identifies a critical software-level failure in 2024-2025 sparse models: 'token-based dataflow' leads to severe load imbalance on hardware after pruning weakly connected tokens. Specifically proposes a 'dimension-based dataflow' to restore load balancing. This is a vital feasibility check for any dynamic proposal (like SOHRA) because it suggests that semantic clustering will fail on current GPUs unless implemented with dimension-parallelism in mind.
- Caveat: Requires NMP-based hardware for full efficiency gains (48x speedup), but the dimension-based dataflow principles are applicable to standard high-bandwidth memory (HBM) systems.
