# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (Seed Paper)
- Why it matters: Foundational architecture that introduced the Transformer, dispensing with recurrence and convolutions in favor of self-attention, enabling massive parallelization.
- Caveat: High citation density means most recent work is likely a direct descendant or minor modification.


## Paper: Convolutional Sequence to Sequence Learning

- Paper ID: 43428880d75b3a14257c3ee9bda054e61eb869c0
- Year: 2017
- Source bucket: reference
- Found by: get_references
- Relation to seed: Closest competitor/ancestor (CNN-based seq2seq approach)
- Why it matters: Represents the primary alternative to RNNs for parallelizable sequence transduction that the Transformer aims to surpass using pure attention.
- Caveat: Uses gated linear units and separate attention modules, showing that attention was already being integrated into non-recurrent architectures.


## Paper: A Novel Sparse-Aware Topology Reconstruction and Global Dependency Enhanced Method...

- Paper ID: 71e3403b4a09b3e52cde7daa5298079c5c411583
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong collision/related work. Uses a 'domain transformer' (DAFormer) with soft masking to enhance dependency modeling while preserving graph topology.
- Why it matters: Demonstrates that incorporating graph topology via masking is a viable way to improve transformer performance in structured domains (microbe-disease).
- Caveat: The topology is likely derived from the domain-specific graph rather than learned end-to-end from raw input sequences.


## Paper: Sparsifiner: Learning Sparse Instance-Dependent Attention...

- Paper ID: 19921cefb2470b2f5d984ab9ce92ebb94aedf2ea
- Year: 2023
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong collision. Uses a 'connectivity predictor module' to estimate connectivity scores between token pairs to learn instance-dependent patterns.
- Why it matters: Shows that learning sparse patterns is possible and efficient, but focuses on 'connectivity' (which can be semantic/spatial) rather than explicit 'topology' (graph/tree structures).
- Caveat: Primarily targets Vision Transformers (ViT) and focuses on FLOP reduction via sparsity.


## Paper: Routing Absorption in Sparse Attention: Why Random Gates Are Hard to Beat

- Paper ID: 09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Critical theoretical collision/limitation.
- Why it matters: Identifies 'routing absorption'—a phenomenon where Q/K/V projections co-adapt to a learned mask, making the learned gates perform no better than random ones. This directly threatens the feasibility of learning sparse attention patterns end-to-end.
- Caveat: The paper highlights that this is particularly severe in Transformers because shared Q/K/V parameters allow for cross-layer compensation.


## Paper: VSA: Faster Video Diffusion with Trainable Sparse Attention

- Paper ID: d97deccf2ff8a8f77cb65294b507c26fcf266712
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong related work/potential solution to absorption. Uses a coarse-to-fine stage (pooling tokens into tiles to find critical tokens) rather than per-query token-level gating.
- Why it matters: It achieves end-to-end training efficiency for sparse attention in video diffusion by using a multi-stage approach, which may avoid the 'routing absorption' seen in fine-grained gating.
- Caveat: Specifically optimized for Video Diffusion Transformers (DiTs) and utilizes a hardware-efficient block computing layout.


## Paper: HSA-Transformer: An Efficient Visual Transformer Model...

- Paper ID: 526c95957298a04ffcec5aa9a54dd64b7f2dcc10
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong collision for hierarchical sparse attention. Uses multi-scale window segmentation for local attention and a 'learnable sparse gating module' for global filtering.
- Why it matters: It directly implements the concept of hierarchical sparse attention to reduce complexity to O(N log N). It is a direct example of the mechanism I proposed, but it focuses on the gating mechanism which, as noted in the 'Routing Absorption' finding, might be susceptible to co-adaptation issues.
- Caveat: The gating module is 'learnable' and 'dynamic', so its exact implementation (whether it is per-query or per-layer/per-block) is critical to whether it suffers from routing absorption.


## Paper: TAM-GT: Topology-Aware Multi-Modal Graph Transformer...

- Paper ID: 50857c35dd11f5a1603e82573bcb7bcfeada4fcb
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong related work. It uses a 'physics-biased attention mechanism' to explicitly model circuit topology as an attributed graph.
- Why it matters: Demonstrates that integrating domain-specific structural constraints (like Kirchhoff's laws) into attention can lead to high accuracy in graph-structured tasks. It uses 'graph-based topology extraction' to build the structure.
- Caveat: This is a task-specific application (analog circuit netlist generation) and the topology is likely provided by an external extraction step rather than being learned from a raw, unstructured sequence.


## Paper: RocketKV: Accelerating Long-Context LLM Inference via Two-Stage KV Cache Compression

- Paper ID: f014aa430c330d263b0e7dd0fe5820a2978cac7e
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Strong related work on two-stage compression. It uses a coarse-grain permanent eviction followed by a fine-grain top-k sparse attention.
- Why it matters: It demonstrates that a two-stage hierarchy (coarse $\to$ fine) can significantly improve efficiency (up to 400x compression) in long-context scenarios without massive accuracy loss. This supports the architectural feasibility of a hierarchical/multi-scale approach to sparsification.
- Caveat: This is specifically for KV cache compression in LLM inference, rather than end-to-end training of the attention mask itself.


## Paper: SVOO: Training-Free Sparse Attention via Offline Layer-Wise Profiling

- Paper ID: 1a1b3666d85208f9773fb04c2b675154ad8cf42f
- Year: 2026
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Direct evidence of layer-wise sparsity, but it is *training-free* and *offline*. It profiles layer-wise sensitivity to derive pruning levels.
- Why it matters: It confirms that 'layer heterogeneity' (the idea that different layers have different optimal sparsity levels) is a real and useful property. However, because it is training-free and relies on offline profiling, it leaves a massive research gap: *Can we learn these layer-wise or block-wise sparsity patterns end-to-end during training without falling into the routing absorption trap?*
- Caveat: The method is specific to Video Diffusion Transformers and is explicitly designed to be training-free.


## Paper: RainFusion2.0: Temporal-Spatial Awareness and Hardware-Efficient Block-wise Sparse Attention

- Paper ID: 157148b963e4d1f665c7cf153f8b258a2eabdea9
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest collision for block-wise sparse attention. It uses block-wise mean values for sparse mask prediction.
- Why it matters: It addresses both the overhead of prediction and hardware efficiency, but like many others, it focuses on 'online adaptive' (likely per-instance/per-input) prediction, which still risks 'Routing Absorption' if the prediction is high-resolution/per-query.
- Caveat: Targets generative models (video/image) and emphasizes hardware-agnostic performance.
