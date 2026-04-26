# Synthesis Report: Scaling Beyond Quadratic Complexity and VRAM

**Section Question:** How can sequence modeling architectures bypass the $O(n^2)$ complexity and VRAM bottlenecks of the Transformer without sacrificing the expressive precision required for long-context associative retrieval?

## Subagent Coverage
| Subagent | Taste/Archetype | Key Contribution |
| :--- | :--- | :--- |
| **Subagent 01** | Pedigree & Limitation Auditor | Identified the "TTR" framework (2026) and ancestral failures of linear attention (2020). |
| **Subagent 02** | Obscure Frontier Synthesizer | Surfaced Quasiseparable Matrix Mixers (2024) and Segment Compression (2025). |

## Literature Buckets

### Foundational & Prior Work (Pre-2024)
- **Attention is All You Need (2017)** [204e3073...]: Established the $O(n^2)$ baseline.
- **Transformers are RNNs (2020)** [6f68e1bb...]: First major linear-attention reformalization; identified kernel associativity as the path to $O(n)$.
- **Mamba (2023)**: Popularized State Space Models (SSMs) as the primary sub-quadratic competitor.

### Recent & SOTA Follow-ups (2024-2025)
- **Hydra (2024)** [ea507df0...]: Introduced bidirectional quasiseparable matrix mixers for non-causal tasks.
- **SCBench (2024)** [Li et al.]: Empirical proof that KV cache (not just compute) is the 1M-token VRAM killer.
- **SCOUT (2025)** [475b1e64...]: Proposed segment compression to mitigate information decay in linear models.
- **LAWCAT (2025)**: Hybrid quadratic-linear attention to "refresh" hidden states.
- **Comba (2025)** [bf1bef2a...]: Early bridge between SSMs and regression frameworks.

### The Frontier (2026)
- **Preconditioned DeltaNet (2026)** [d3944893...]: Postulated the "Test-Time Regression" (TTR) framework; solved "curvature neglect" via second-order preconditioning in linear recurrences.

## Closest Prior/Future Collision Table
| Seed Paper / Mechanism | Potential Collision | year | Conflict Type |
| :--- | :--- | :--- | :--- |
| **Linear Attention** | Katharopoulos et al. | 2020 | Ancestry; fails on high-precision retrieval. |
| **Hydra (Bidirectional SSM)** | ViM (Vision Mamba) | 2024 | Competitor; Hydra uses quasiseparable matrices instead of simple scans. |
| **Preconditioned DeltaNet** | Mamba-2 / GLA | 2023/24 | DeltaNet claims superior expressivity via curvature awareness (TTR). |
| **Segment Compression** | SWA (Sliding Window) | <2023 | SCOUT adds compression/hierarchical states to SWA. |

## Research Gaps with Evidence
1. **The "Curvature-Decay" Contradiction**: While DeltaNet (2026) fixes expressivity locally via preconditioning, it does not explicitly address long-range information decay identified in SCOUT (2025). Evidence suggests a gap in *hierarchical* TTR models.
2. **Bidirectional VRAM Scaling for Visual Diffusion**: Hydra (2024) solves the bidirectional limitation, but the specific VRAM footprint of quasiseparable mixers at video-scale (3D volumes) compared to 2D is underexplored.
3. **Entropy-Aware State Allocation**: Most sub-quadratic models use static state-size $h_t$. Evidence from medical/long-context benchmarks shows information density is non-uniform, suggesting a gap for *elastic* state sizes.

## Proposal Seed Inventory
- **Seed: Dynamic Entropy Kernels** (Auditor): Adaptive shifts in kernel feature maps to recover precision in high-entropy context.
- **Seed: Adaptive Curvature Preconditioning** (Auditor): Scaling preconditioning factors based on information density.
- **Seed: Bidirectional Quasiseparable Hybrids** (Synthesizer): Video-frame alignment via matrix mixers.
- **Seed: Recurrent Quasiseparable Bottlenecks (RQB)** (Synthesizer): Temporal state persistence for sliding-window video.

## Rejected or Weak Ideas
- **"Mamba for Everything"**: Rejected as too generic. Analysis requires specific mechanisms (like quasiseparable matrix mixers) to differentiate from 2023 SOTA.
- **"Make linear attention faster"**: Rejected; current hardware-aware implementations (FlashAttention-3) are already highly optimized. The bottleneck is now expressive precision, not raw speed.

## Surviving Proposal Candidates

### Proposal Candidate 1: Hierarchical Preconditioned Recurrence (HPR) for 1M+ Context
- **Core novelty claim**: Combines second-order Test-Time Regression (TTR) with segment-based compression to solve the "decay-precision" trade-off.
- **Source subagents**: Subagent 01 (Preconditioning) + Subagent 02 (Segment Compression).
- **Evidence basis**: DeltaNet (2026) for curvature handling; SCOUT (2025) for segment efficiency; SCBench (2024) for VRAM bottleneck proof.
- **Technical mechanism**: Implement a "Delta-Segment-Tree." Each segment's hidden state is updated using a curvature-aware preconditioned delta rule, but segments are managed in a hierarchical structure where parent nodes store a compressed, second-order summary of child-state gradients.
- **Minimum viable validation**: Needle-in-a-haystack and Long Range Arena (LRA) at 1M context vs. standard Mamba-2 and DeltaNet.
- **Falsification criteria**: If the hierarchical overhead (memory for summary gradients) exceeds the KV cache size of a hybrid-SWA Transformer, the method fails on VRAM efficiency.
- **Confidence**: High (supported by 2026 theory).

### Proposal Candidate 2: Bidirectional Quasiseparable Temporal Latents (BQTL)
- **Core novelty claim**: First non-causal bidirectional mixer for video diffusion that bypasses "ghosting" by using quasiseparable matrix structures to bridge spatial and temporal patches in a single recurrent pass.
- **Source subagents**: Subagent 02.
- **Evidence basis**: Hydra (2024) [ea507df0...]; Hong et al. (2025) Diffusion SSMs.
- **Difference from seed**: Moves from Hydra’s general matrix mixing to a specific video-optimized state $h_t$ that persists across temporal chunks.
- **Technical mechanism**: Replaces 3D attention with a Quasiseparable Matrix Mixer (QMM) where the matrix defines both spatial adjacency and temporal precedence. Uses a low-rank temporal latent filter that "slips" across the sequence to maintain identity during sliding-window inference.
- **Falsification criteria**: Failure to outperform standard Diffusion Transformers (DiT) on FID/FVD scores within a 16GB VRAM constraint.
- **Confidence**: Medium.

### Proposal Candidate 3: Entropy-Steered Elastic Kernels (ESEK)
- **Core novelty claim**: Dynamically Scales the hidden state dimension $d$ and kernel expansion $\phi$ based on localized token entropy, treating "compressed state" as a variable-length memory.
- **Source subagents**: Subagent 01.
- **Evidence basis**: Katharopoulos (2020) kernel failure; DeltaNet (2026) curvature analysis.
- **Technical mechanism**: A controller sub-network predicts "state-pressure" (entropy). When entropy is high, the ESEK block expands the kernel projection dimension to prevent information collision in the $O(1)$ state.
- **Minimum viable validation**: Performance on "dense retrieval" tasks where many key-value pairs are semantically similar.
- **Confidence**: Medium (Speculative).

## Novelty-Risk Matrix
| Idea | Foundational Risk | SOTA Collision Risk | Data/Compute Risk |
| :--- | :--- | :--- | :--- |
| **HPR** | Math complexity of hierarchical TTR | Push from DeltaNet 2 authors | High (needs 1M+ context training) |
| **BQTL** | Numerical stability of QMMs | VGamba (2025) / Hong et al. | Medium (Diffusion-specific) |
| **ESEK** | Kernel overhead vs. VRAM | Adaptive gate papers (2022-24) | Low (Architectural change) |

## Contradictions and Weak Spots
- **Theory vs. Hardware**: Theoretical $O(n)$ complexity in DeltaNet (2026) and Hydra (2024) often loses to $O(n^2)$ FlashAttention-3 on Blackwell/H100 GPUs for sequences under 32k due to the high constant factor of recurrent scans and preconditioning.
- **State Compression vs. Hallucination**: There is a documented trade-off where "compressed" states (SCOUT, SSMs) lead to lower factual calibration in medical/legal tasks compared to full KV caches.

## Recommended Next Searches
- **"VGamba" (2025) Deep Dive**: Check if the bidirectional temporal persistence proposed in BQTL was already solved by Haruna et al. (2025).
- **CUDA/Triton implementation for Preconditioned DeltaNet**: Verify if the curvature-aware preconditioning can be implemented as a fused kernel to match FlashAttention performance.
- **"State-Space MoE"**: Investigate if the "Elastic Kernel" idea can be reformulated as a Mixture-of-Experts where experts are different state-sizes.