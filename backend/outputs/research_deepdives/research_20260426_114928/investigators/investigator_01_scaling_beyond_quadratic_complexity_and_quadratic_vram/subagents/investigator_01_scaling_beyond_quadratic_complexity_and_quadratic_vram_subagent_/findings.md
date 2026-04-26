# Findings



## Finding: The Fundamental Scaling Bottleneck

- Claim: The Transformer architecture is limited by its inherent O(N^2) time and space complexity relative to sequence length due to the pairwise self-attention mechanism.
- Confidence: High
- Evidence:
  - 204e3073870fae3d05bcbc2f6a8e263d9b72e776 (Attention is All you Need, 2017)
- Why it matters: This quadratic dependency creates a 'VRAM wall' that makes long-context modeling (e.g., full books, high-res images) computationally prohibitive, driving the entire sub-field of 'Efficient Transformers'.
- Caveat: Small sequence lengths (e.g., < 512 tokens) often see the overhead of sub-quadratic approximations outweighing their theoretical benefits due to hardware-level optimizations (like FlashAttention) specifically tuned for the standard attention matrix.


## Finding: Information Decay in Purely Linear Models

- Claim: Purely linear models (e.g., Mamba, Linear Transformers) risk performance degradation because they struggle to retain detailed information from distant tokens compared to quadratic attention.
- Confidence: High
- Evidence:
  - 475b1e6491fe4c23f47abfcaa5bbf92d22aaf034 (SCOUT, 2025)
  - 8237f2fc77f3c4b21d3e5c85acb9ee70ed1ba2b8 (LAWCAT, 2025)
- Why it matters: This 'retention gap' is the primary driver for hybrid architectures that re-introduce sparse or compressed quadratic attention to 'refresh' the hidden state, indicating that sub-quadratic scaling often trades off precision for throughput.
- Caveat: The extent of decay is task-dependent; associative retrieval ('needle-in-a-haystack') suffers more than general language modeling.


## Finding: SCBench KV Cache-Centric Analysis of SSM vs Transformer

- **Claim**: In long-context inference, KV cache size is the primary VRAM bottleneck for Transformers, while SSMs and Hybrid models maintain a constant or linear recurrent state that drastically reduces the inference footprint.
- **Confidence**: High
- **Evidence**: 
  - SCBench (Li et al. 2024, ARXIV:2412.10319): Analyzes Transformer, SSM, and Hybrid models on context length effectiveness and identifying memory vs compute bottlenecks.
  - Chowdhury (2026): Notes that at long contexts, KV cache in Transformers like Llama-3 405B can surpass the weight footprint, whereas SSMs avoid this specific quadratic growth.
- **Why it matters**: This confirms the 'novelty pressure' for hybrid models like Hydra or SSM-centric blocks in diffusion. If SSMs can match Transformer quality (as suggested by Hydra), the VRAM savings at 1M+ tokens are game-changing for edge-device (high-end GPU w/ finite VRAM) inference.
- **Caveat**: The efficiency of the 'Hydra' bidirectional mixer specifically in visual generation is still a frontier (2025) and lacks mature benchmarks like those available for causal text modeling.


## Finding: Linear Attention as Online Least Squares (TTR Framework)

- Claim: The most robust mathematical interpretation of successful sub-quadratic models (Mamba-2, DeltaNet, GLA) is that they perform Test-Time Regression (TTR), specifically online least squares updates to a linear map from keys to values.
- Confidence: High
- Evidence:
  - d3944893325ad2906c09870ceef1d2bdb3935229 (Preconditioned DeltaNet, 2026)
  - bf1bef2ac78d20efa5c1f57ff5d503ebdb66ad95 (Comba, 2025)
- Why it matters: This framework identifies why original linear attention (Katharopoulos 2020) failed: it was a first-order approximation that ignored the curvature of the least-squares loss. Modern 'Transformer-killers' are essentially moving toward second-order optimization techniques (preconditioning) implemented as hardware-efficient recurrences.
- Caveat: The TTR framework assumes a linear map; it does not yet clearly explain the advantage of hybrid quadratic/linear systems where the map might be non-linear.
