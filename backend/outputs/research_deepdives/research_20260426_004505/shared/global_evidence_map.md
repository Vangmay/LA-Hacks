# Global Evidence Map: Transformer Scaling, Sparsity, and Structural Novelty

This map synthesizes the evidence across three investigative deep dives exploring the architectural bottlenecks, experimental frontiers, and geometric/mathematical evolution of the Transformer.

## 1. Core Architectural Bottlenecks & Scaling
*Focus: Quadratic complexity, sparsity, and the tension between efficiency and representational power.*

| Paper ID | Year | Key Finding / Claim | Search Bucket | Source Investigator(s) |
| :--- | :--- | :--- | :--- | :--- |
| **204e3073870fae3d05bcbc2f6a8e263d9b72e776** | 2017 | Foundational $O(n^2)$ quadratic scaling bottleneck (Attention is All You Need). | `seed_metadata` | All |
| **510e26733aaff585d65701b9f1be7ca9d5afc586** | 2017 | Foundation for conditional computation/MoE (Shazeer et al.). | `foundational` | `inv_01`, `inv_02` |
| **3820231d31540ecb05d94c74d959a2f61d3136ea** | 2022 | **Collision**: Direct head-level routing (MoA). | `collision` | `inv_01` |
| **2951fcda8cb6a3f5c25f3659f5330ac3f2201bf9** | 2025 | **Collision**: Token-level expert-choice routing (MoSA). | `collision` | `inv_01` |
| **53a803388e83ae89261624099d7be4287ace67cb** | 2024 | SOTA neighbor: MLA for KV compression + MoE (DeepSeek-V2). | `sota_neighbor` | `inv_01` |
| **3c0c526d88d0eaa4df75fe0663c7c900fc47c02e** | 2024 | **Gap/Collision**: Identified expressiveness/injectivity failure in linear attention. | `gap_analysis` | `inv_03` |
| **e62198fd44c62b890c99e738e02ec5064cd6ec93** | 2026 | **Collision**: Addressing injectivity via Laplacian kernels (LaplacianFormer). | `collision` | `inv_03` |
| **a7a71daece55f88209e792218fabf3fd75412461** | 2025 | **Constraint**: Hardware-efficiency bottlenecks in sparse attention (BETA). | `efficiency_gap` | `inv_03` |

## 2. Structural, Geometric, and Spectral Mechanisms
*Focus: Inductive biases, attention sinks, and frequency-domain modeling.*

| Paper ID | Year | Key Finding / Claim | Search Bucket | Source Investigator(s) |
| :--- | :--- | :--- | :--- | :--- |
| **10bd38673951f5d7729568284093cbd80482ab16** | 2023 | Identified high-norm "register" tokens as artifacts. | `collision` | `inv_03` |
| **5958e8a8010d39947104efe599b676b9e1d0e040** | 2025 | **Theory**: Sinks as geometric necessity for reference frames. | `theory` | `inv_03` |
| **c9a0674cba7ae85eadc969026bac04500467db2e** | 2025 | **Gap**: Swin-based models struggle with local info capture. | `gap_analysis` | `inv_02` |
| **c719751ab853717aeb3985912d9e3c07b721d092** | 2025 | **Collision**: Frequency-aware modules as task-specific plug-ins (FANet). | `collision` | `inv_02` |
| **0da8568dc1b3dfc781c51881c082a83f731bc89f** | 2024 | **Collision**: Non-causal SSD (VSSD) is vision-centric. | `collision` | `inv_02` |
| **c0650ea8fb4a3cee2eeb975d357abf536df78c99** | 2026 | **Collision**: Momentum attention as a high-pass filter (Maitra). | `collision` | `inv_02` |

## 3. Reliability, Safety, and Information Theory
*Focus: Entropy, stability, and deployment-time diagnostics.*

| Paper ID | Year | Key Finding / Claim | Search Bucket | Source Investigator(s) |
| :--- | :--- | :--- | :--- | :--- |
| **96c6404f0f38b50299017be181a50d6c51e6480d** | 2026 | **Gap**: Structural vulnerabilities in safety-critical domains. | `gap_analysis` | `inv_01` |
| **385c363ea8e450f362d389f401beaeb5b42a0022** | 2023 | **Collision**: Entropy used for training stability, not inference scaling. | `collision` | `inv_01` |
| **1bde7bb16f8e69dff8b5f391b60558c1cafd2d0e** | 2025 | **Theory**: Entropy as a proxy for head redundancy. | `theory` | `inv_01` |
| **276aa3dd297998f415636fd878cbd4801c521712** | 2025 | **Collision**: Joint rank/quantization (MLoRQ) is static, not dynamic. | `collision` | `inv_01` |
| **d71a87fc2f652bf5f03fbf9d986836531234883e** | 2026 | **Collision**: Entropy-based token selection (AdaptToken). | `collision` | `inv_01` |
| **f88c5105e8806105d792d077527ad32bcdd973e7** | 2024 | **Collision**: Attention sensitivity for XAI/importance. | `collision` | `inv_01` |

## Summary of Major Research Gaps (Synthesis)

1.  **Algorithmic vs. Parameter Sparsity**: While parameter/token routing is heavily researched (MoSA, MoA), routing the *computational kernel* (e.g., Full vs. Linear vs. Windowed) remains an underexplored mechanism (`inv_01`).
2.  **Unified Dynamic Optimization**: Existing work separates adaptive rank (TALE) and quantization (MLoRQ). A unified, entropy-modulated control loop for both rank and precision is a significant gap (`inv_01`).
3.  **Real-time Reliability Diagnostics**: A distinction exists between *interpretability* (what is important) and *stability monitoring* (detecting failure via weight fluctuations under noise) (`inv_01`, `inv_03`).
4.  **Non-Causal SSM for LLMs**: Non-causal SSMs are established in vision (VSSD), but efficient, single-pass non-causal mechanisms for language/prefix-LM workloads are missing (`inv_02`).
5.  **Mathematical Repair of Linear Attention**: Most linear-attention fixes are global (kernels); there is a gap in hybrid local-global structures designed specifically to restore the injectivity and "sharpness" lost in approximation (`inv_03`).