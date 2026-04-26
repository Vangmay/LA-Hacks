# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (The seed paper itself)
- Why it matters: Foundation of the Transformer architecture, dispensing with recurrence and convolutions for attention-based transduction.
- Caveat: High computational cost for very long sequences due to quadratic complexity of self-attention.


## Paper: A Primer in BERTology: What We Know About How BERT Works

- Paper ID: bd20069f5cac3e63083ecf6479abc1799db33ce0
- Year: 2020
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Follow-up/Extension (BERT is a Transformer variant)
- Why it matters: Surveys knowledge on BERT's internal workings, addressing overparameterization and compression. Provides potential gaps in understanding mechanism and efficiency.
- Caveat: Focused primarily on BERT; findings may not generalize to all Transformer architectures.


## Paper: Research on Transformer Model Compression and Hardware-Friendly Deployment Based on EBSP+GQSA Fusion Method

- Paper ID: bdd083c89b8ccc00f7587ad681eb4ba1e532edec
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Compression research)
- Why it matters: Proposes a fusion method (EBSP+GQSA) specifically tailored to the Transformer's attention weights, addressing the inadequacy of traditional quantization/sparsity methods for this architecture.
- Caveat: Focuses on specific fusion algorithms; broader applicability to all transformer variants is not explicitly proven.


## Paper: Exploiting Information Redundancy in Attention Maps for Extreme Quantization of Vision Transformers

- Paper ID: 1bde7bb16f8e69dff8b5f391b60558c1cafd2d0e
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Compression/Quantization)
- Why it matters: Proposes using Shannon entropy to identify low-entropy (redundant) attention heads for targeted quantization. This provides a specific mechanism (entropy-based pruning/quantization) for reducing complexity.
- Caveat: Focuses on Vision Transformers (ViT) and uses entropy as the metric, which might differ from LLM attention behavior.


## Paper: Towards Economical Inference: Enabling DeepSeek's Multi-Head Latent Attention in Any Transformer-based LLMs

- Paper ID: 4cbf0b9fd18a1850ce588244b073927c372a0d4f
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Compression/Efficiency)
- Why it matters: Proposes MHA2MLA, a data-efficient way to transition standard Multi-Head Attention (MHA) models to Multi-Head Latent Attention (MLA), drastically reducing KV cache size (92.19% reduction for Llama2-7B).
- Caveat: Requires a specific fine-tuning strategy (MHA2MLA) and is tied to the MLA architecture design.


## Paper: MLoRQ: Bridging Low-Rank and Quantization for Transformer Compression

- Paper ID: 276aa3dd297998f415636fd878cbd4801c521712
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Compression/Optimization)
- Why it matters: Introduces a two-stage optimization (intra-layer and inter-layer) to determine optimal bit-width and rank assignments simultaneously, rather than treating them as separate tasks. This addresses the complexity of joint low-rank and quantization optimization.
- Caveat: Focused on Vision Transformers (ViT); scaling to LLMs with massive KV caches may require different considerations.


## Paper: Adaptive Gradient Compression: An Information-Theoretic Analysis of Entropy and Fisher-Based Learning Dynamics

- Paper ID: 730df23d380cc955f057f471f1ababf1173b0bb8
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Information-theoretic optimization)
- Why it matters: Demonstrates that entropy-based compression can significantly reduce gradient density (33.8x) in ResNet models while maintaining stability. This provides a conceptual bridge for using entropy to selectively preserve or compress model parameters/gradients during training or inference.
- Caveat: Focused on gradient compression for training, not model weight/attention compression for inference.


## Paper: TALE: Token-Adaptive Low-Rank KVCache Approximation with Reconstruction Elimination

- Paper ID: 7921b2bd977084f49cf0d0602c5a3301b72ae10f
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Low-rank approximation/KV Cache)
- Why it matters: Proposes a token-adaptive low-rank approximation for KV Cache that varies ranks based on token significance, reducing KV cache size by 9.1x. This establishes that rank-adaptivity is a viable strategy for LLM inference efficiency.
- Caveat: Focuses on token-adaptive rank for KV cache rather than the entropy-based selection mechanism proposed in the seed.


## Paper: AdaptToken: Entropy-based Adaptive Token Selection for MLLM Long Video Understanding

- Paper ID: d71a87fc2f652bf5f03fbf9d986836531234883e
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior work (Entropy-based selection)
- Why it matters: Uses model response entropy as a global control signal for token selection in long-video understanding. This provides strong evidence that entropy is a reliable signal for determining informational relevance in Transformers.
- Caveat: Specifically applied to Multi-modal Large Language Models (MLLMs) for video tasks.
