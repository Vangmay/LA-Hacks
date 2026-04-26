# Proposal Seeds



## Proposal Seed: Bidirectional Quasiseparable Matrix Hybridization for Ultra-Long Video Frames

- Status: raw
- Originating taste: Obscure Frontier Synthesizer
- Seed-paper hook: Attention is All You Need establishes $O(n^2)$ attention as the bottleneck.
- Evidence trigger: Hydra (Hwang et al. 2024) proposes bidirectional SSMs via quasiseparable matrix mixers as a drop-in replacement for self-attention.
- Candidate novelty: Hybrides (SSM + Attention) are recently appearing for diffusion (Hong et al. 2025), but the specific interaction between 'sequence alignment' and 'VRAM-efficient bidirectional mixing' for non-causal visual tasks remains underexplored for multi-hour video sequence contexts.
- Technical mechanism: Replace the global self-attention layer in long-context diffusion models with a hierarchical 'Hydra-Block' that uses quasiseparable matrix mixers for local token alignment and a compressed linear-attention global layer for long-range context, optimizing the recurrent state $h_t$ size for VRAM constrained environments (e.g., <16GB).
- Closest prior-work collision: Hydra (2407.09941), Mamba.
- Closest future-work collision: 'Pushing the Boundaries of SSMs' (2502.00972) by Hong et al.
- Minimum validation: Performance vs. VRAM trade-off on ImageNet-conditional generation vs. 1-minute video frame prediction using a 15GB VRAM limit.
- Falsification risk: SSMs may fail to capture the high-frequency spatial dependencies that self-attention handles via exact dot-products.
- Why this is not generic: It specifically targets the bidirectional 'non-causal' limitation of standard Mamba and the VRAM ceiling of self-attention by leveraging the 'quasiseparable' matrix structure defined in the Hydra paper.
- Confidence: medium
- Required next search: Search for specific 'quasiseparable matrix' implementation optimizations in C++/CUDA to verify actual VRAM savings.


## Proposal Seed: Dynamic Kernels for Recovering Long-Range Expressivity in Linear Attention

- Status: speculative
- Originating taste: Pedigree and Limitation Auditor
- Seed-paper hook: The O(N^2) self-attention mechanism in Vaswani et al. (2017).
- Evidence trigger: The trade-off between the 'memoryless' nature of linear attention and the expressivity of quadratic attention.
- Candidate novelty: Developing a kernel that adaptationally shifts between 'forgetful' (recurrent-like) and 'precise' (attention-like) states based on localized entropy, rather than using a fixed static kernel like standard Linear Transformers.
- Technical mechanism: A time-varying feature map that modifies the feature expansion dimension based on the cumulative information density of the sequence.
- Closest prior-work collision: Katharopoulos et al. (2020) 'Transformers are RNNs'.
- Closest future-work collision: Modern State Space Models (SSMs) like Mamba (Gu & Dao, 2023).
- Minimum validation: Compare performance on the Long Range Arena (LRA) benchmark against standard Linear Attention and Mamba.
- Falsification risk: The overhead of dynamic kernel computation might exceed the VRAM savings of linear complexity at standard sequence lengths.
- Why this is not generic: It specifically targets the 'limitation' of static kernel approximation, which is the primary reason linear transformers often underperform on fine-grained associative tasks.
- Confidence: low
- Required next search: Search for 'limitations of linear attention kernels' and 'dynamic feature maps in transformers'.


## Proposal Seed: Recurrent Quasiseparable Bottlenecks for Memory-Constrained Video Diffusion

- Status: promising
- Originating taste: Obscure Frontier Synthesizer
- Seed-paper hook: Attention is All You Need establishes O(n^2) self-attention as the core scaling bottleneck (VRAM and complexity).
- Evidence trigger: The 'Gamba bottleneck' (Haruna et al. 2025, 2503.21262) and Hydra (Hwang et al. 2024, 2407.09941) suggest that lightweight SSM-based mixers can replace heavy transformer blocks in visual recognition and generation.
- Candidate novelty: Existing Diffusion SSMs (like Hydra-based models in Hong et al. 2025) use SSMs for the main sequence mixing. I propose a 'Recurrent Quasiseparable Bottleneck' (RQB), which specifically targets the interaction between high-resolution spatial patches and long-range temporal dependencies. Unlike standard Mamba, RQB uses a quasiseparable matrix structure to perform bidirectional 'spatial-temporal' mixing in a single pass without the O(n^2) cost of 3D attention.
- Technical mechanism: Implement the sequence mixer as a quasiseparable matrix mixer (per Hydra) but augment it with a low-rank learnable 'temporal recurrent state' that persists across video segments. This allows for 'sliding window' video generation with global consistency, bypassing the KV cache growth of Transformers identified in SCBench.
- Closest prior-work collision: Hydra (Hwang et al. 2024), ViM (Vision Mamba).
- Closest future-work collision: VGamba (Haruna et al. 2025), Pushing Boundaries of SSMs (Hong et al. 2025).
- Minimum validation: Compare VRAM consumption and FID scores on a 5B parameter Diffusion model for 512x512 video frame prediction vs. a standard DiT (Diffusion Transformer) baseline on a single 16GB VRAM GPU.
- Falsification risk: The quasiseparable approximation might lead to 'ghosting' or 'flickering' in video if the recurrent state cannot capture high-frequency motion details as accurately as dot-product attention.
- Why this is not generic: It moves away from 'causal-only' SSMs to non-causal bidirectional mixers specifically optimized for the VRAM-bound video generation task.
- Confidence: medium-high
- Required next search: Technical deep dive into quasiseparable matrix decomposition performance on H100/L40S hardware.
