# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: This is the seed paper.
- Why it matters: Introduced the Transformer architecture, replacing recurrence/convolution with self-attention, enabling massive parallelization and the current era of large language models.
- Caveat: Primary focus was on machine translation; does not address the scaling laws or emergent properties found in much larger modern variants.


## Paper: MTMixer: a hybrid Mamba-Transformer architecture for multimodal remote sensing image classification

- Paper ID: f8722d87b9d86f78f1865d51649f8e51255b76d7
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct follow-up/hybrid addressing limitations.
- Why it matters: Addresses the quadratic complexity of Vision Transformers (ViTs) and the unidirectional scan limitation of Mamba by interleaving selective state-space blocks with self-attention layers.
- Caveat: Focused on remote sensing imagery; effectiveness on other high-resolution modalities needs verification.


## Paper: Dual-path Mamba: Short and Long-term Bidirectional Selective Structured State Space Models for Speech Separation

- Paper ID: da9178eae82d1ca5492aaecd0151ba49481cb8b1
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision/precursor.
- Why it matters: Proposes 'dual-path Mamba' to model forward and backward dependencies for speech separation, directly using bidirectional selective SSMs.
- Caveat: Domain-specific (speech separation); may not generalize the architectural efficiency to LLM or general vision tasks.


## Paper: BabyMamba-HAR: Lightweight Selective State Space Models for Efficient Human Activity Recognition on Resource Constrained Devices

- Paper ID: a9f8132b2a5b7726a0cf6da4fe3520b7371f36ff
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision/implementation.
- Why it matters: Uses 'weight tied bidirectional scanning' for Human Activity Recognition (HAR), demonstrating that bidirectional scanning is being explored for efficiency in TinyML.
- Caveat: Specifically optimized for resource-constrained devices and HAR; mechanism details (weight tying) might be a specific optimization rather than a general architecture.


## Paper: Motion Mamba: Efficient and Long Sequence Motion Generation with Hierarchical and Bidirectional Selective SSM

- Paper ID: b9646f057887825d7471ec01664494b0b7ca5a83
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision (domain-specific).
- Why it matters: Implements a 'Bidirectional Spatial Mamba (BSM)' block to enhance motion generation. It uses bidirectional processing for latent poses.
- Caveat: Focused on human motion generation; the bidirectional mechanism is applied to spatial/latent pose data rather than a general sequence-to-sequence transformer replacement.


## Paper: HSIDMamba: Exploring Bidirectional State-Space Models for Hyperspectral Denoising

- Paper ID: d7311d1ae0835cc7442afd2fc296783513d1de36
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision (domain-specific).
- Why it matters: Uses 'Hyperspectral Continuous Scan Blocks' (HCSB) that link forward and backward scans to strengthen spatial-spectral interactions.
- Caveat: Specific to hyperspectral image denoising; architecture is designed for spatial-spectral dependencies.


## Paper: HLX: A Unified Pipelined Architecture for Optimized Performance of Hybrid Transformer-Mamba Language Models

- Paper ID: 7026f38dadeb7f28bb58f944d1f08bed9df0190b
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Complementary (System/Hardware optimization).
- Why it matters: Addresses the hardware efficiency gap in hybrid models. It identifies that shifting bottlenecks between FlashAttention and SSD (State-Space Duality) kernels limit compute utilization. It proposes PipeFlash and PipeSSD to optimize dataflow and reduce memory traffic.
- Caveat: Focuses on hardware/system optimization (pipelining) rather than the mathematical/architectural definition of the SSM itself.


## Paper: Vision Mamba: Efficient Visual Representation Learning with Bidirectional State Space Model

- Paper ID: 38c48a1cd296d16dc9c56717495d6e44cc354444
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision (generic vision backbone).
- Why it matters: Proposes 'Vim', a generic vision backbone using bidirectional Mamba blocks. It achieves significant speedups and memory savings over ViTs (e.g., 2.8x faster than DeiT) by using bidirectional state space models.
- Caveat: While it targets a generic vision task (ImageNet, COCO), it still relies on a bidirectional scan approach that may have the standard $2\times$ overhead associated with dual-pass scanning.


## Paper: VSSD: Vision Mamba with Non-Causal State Space Duality

- Paper ID: 0da8568dc1b3dfc781c51881c082a83f731bc89f
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision (non-causal mechanism).
- Why it matters: Introduces a non-causal format of SSD (State Space Duality). It proposes discarding the magnitude of interactions between hidden states and tokens while preserving relative weights to relieve dependencies on previous tokens. This aims to achieve non-causality more efficiently than simple multi-scan strategies.
- Caveat: The mechanism (discarding magnitude) is a specific mathematical modification to the SSD framework; its generalizability to LLMs or non-vision tasks is an open question.


## Paper: PTM-Mamba: A PTM-Aware Protein Language Model with Bidirectional Gated Mamba Blocks

- Paper ID: 02949dca8d9895f3f93b9b23d69893e3becb2595
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_bulk_search
- Relation to seed: Direct collision (specialized language modeling).
- Why it matters: Applies bidirectional Mamba blocks to protein language modeling (pLMs). This is one of the few examples of bidirectional Mamba being used for a sequence-based modeling task outside of vision.
- Caveat: Focused on proteomic sequences; the specific bidirectional gating mechanism used for amino acids might not translate directly to natural language or general-purpose LLMs.


## Paper: DiffuMamba: High-Throughput Diffusion LMs with Mamba Backbone

- Paper ID: 0e428dc856fe87e0901ba2aaf1d358415b667374
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_bulk_search
- Relation to seed: Direct collision (Language modeling + Bidirectional).
- Why it matters: Introduces a masked diffusion language model built on a bidirectional Mamba backbone. It achieves high inference throughput for long sequences and shows that cache-efficient block diffusion with Mamba mixers is a scalable strategy.
- Caveat: Focuses on the diffusion objective (non-autoregressive) rather than a purely bidirectional language modeling objective (like prefix-LM).


## Paper: InfiniMotion: Mamba Boosts Memory in Transformer for Arbitrary Long Motion Generation

- Paper ID: 2230396c51086ccdaaeffbf7d47c82dea784186f
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_bulk_search
- Relation to seed: Direct collision (language/sequence modeling).
- Why it matters: Introduces 'Bidirectional Mamba Memory' to enhance a Transformer's ability to handle arbitrarily long motion sequences within an autoregressive framework. This is a significant non-vision application of bidirectional SSMs for long-range sequence modeling.
- Caveat: Targeted at motion generation (coordinates/latent poses) rather than natural language tokens; the dependency structure of motion sequences may differ from text.


## Paper: Text-to-Talk: Audio-Language Model Needs Non-Autoregressive Joint Training

- Paper ID: 1416afa3b83d5447cadf25a731879ece1b3378ab
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision (Non-autoregressive + Bidirectional).
- Why it matters: Proposes a hybrid framework (TtT) that uses AR for text and NAR (diffusion) for audio. Crucially, it uses a modality-aware attention mechanism that allows *bidirectional modeling within audio spans*. This shows that in multimodal contexts, non-autoregressive/bidirectional modeling is being used to solve the mismatch between text (causal) and audio (non-causal) dependencies.
- Caveat: This is a hybrid multimodal approach; the bidirectional modeling is applied to the audio modality rather than a unified non-causal language model backbone.


## Paper: Encoder-Decoder or Decoder-Only? Revisiting Encoder-Decoder Large Language Model

- Paper ID: 0c9eef6b3374567df0f4169280972e5531f85c1
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Complementary (Architectural paradigm).
- Why it matters: Re-evaluates the encoder-decoder (RedLLM) vs. decoder-only (DecLLM) paradigm. RedLLM uses prefix language modeling (which allows bidirectional context for the encoder part) and shows strong scaling and context extrapolation, suggesting that the 'encoder-decoder' structure (which inherently allows non-causal/bidirectional processing of the input) remains a powerful and efficient alternative to purely causal decoder-only models.
- Caveat: This is a study on Transformers, not SSMs/Mamba; however, it validates the structural utility of non-causal prefix processing in LLMs.
