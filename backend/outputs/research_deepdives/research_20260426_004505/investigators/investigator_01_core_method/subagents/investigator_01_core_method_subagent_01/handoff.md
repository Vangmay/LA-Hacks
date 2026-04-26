# Hand-Off: Transformer Scaling & Sparsity Research

## Search Summary
- **Ancestry Mapping**: Traced the transition from RNN/CNN to pure attention and identified the MoE (2017) paper as the foundational mechanism for conditional computation.
- **Collision Searching**: Conducted extensive searches for 'sparse attention + MoE' recombinations. Found direct collisions in head-selection (MoA 2022) and token-selection (MoSA 2025).
- **Complexity/Modality Pivot**: Explored routing between different attention types (local vs. non-local in speech) and different modalities (Mixture-of-Transformers 2024).

## Top Papers & Relevance
- **Attention is All You Need (2017)**: The seed paper; established the $O(n^2)$ attention bottleneck.
- **Shazeer et al. (2017) [MoE]**: Foundation for conditional computation and sparse routing.
- **MoA (2022)**: Direct collision for head-level routing.
- **MoSA (2025)**: Direct collision for token-level routing (expert-choice).
- **DeepSeek-V2 (2024)**: Modern SOTA neighbor using MLA (latent attention) for KV compression.
- **MoT (2024)**: Neighboring work on modality-specific parameter routing.

## Strongest Novelty/Gap Implications
- **The "What" Gap**: Most research focuses on *what* to attend to (heads or tokens). There is a gap in routing *how* to attend (the attention mechanism itself).
- **Mechanism Selection**: Instead of just selecting a subset of heads, a model could dynamically route between different attention *algorithms* (e.g., Global Dense Attention, Sliding Window Attention, or Dilated Attention) based on the information density or structural requirements of the token.
- **Adaptive Complexity**: Routing between dense kernels and sparse/quantized kernels to manage the trade-off between precision and computational cost in real-time.

## Candidate Spinoff Proposal Seeds

### 1. Mixture of Attention Algorithms (MoAA)
- **Core Idea**: A router that selects the attention *kernel* (e.g., Full Self-Attention vs. Flash-Attention-style Windowed vs. Linear Attention) per layer or per block.
- **Evidence Basis**: ASSENet (2024) showed adaptive selection of local/non-local mechanisms in speech; MoSA/MoA cover token/head selection but not kernel selection.
- **Collision Risk**: Low; existing sparse methods usually fix the sparsity pattern rather than choosing the algorithm.
- **Next Search**: "Dynamic attention kernel selection" or "adaptive attention mechanism routing".

### 2. Complexity-Aware Token Routing
- **Core Idea**: Instead of selecting $k$ tokens (MoSA), route tokens to different "complexity levels" of attention (e.g., high-precision dense attention for core entities, low-precision/sparse attention for filler words).
- **Evidence Basis**: Information density varies significantly in natural language (Zipf's law).
- **Next Search**: "Information-density driven attention" or "token-level precision routing".

## Uncertainties & Contradictions
- **Routing Overhead**: The primary risk is that the gating mechanism required to select between complex attention algorithms might consume more FLOPs than the savings provided by the sparse/local choice.
- **Hardware Alignment**: Selecting different attention algorithms may break the performance benefits of highly optimized kernels (like FlashAttention) which rely on predictable, static patterns.

## Recommended Next Steps for Investigator
1. **Verify Kernel Switching**: Check if current GPU kernels (Triton/CUDA) allow for efficient per-block or per-token switching of attention algorithms without massive launch overhead.
2. **Refine MoAA**: Develop a formalization for a 'Mixture of Kernels' that can be trained end-to-end with standard Transformer objectives.