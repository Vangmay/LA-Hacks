# Global Evidence Map

This map synthesizes papers, search results, and analytical findings across all investigators and subagents. It tracks the evidentiary basis for sub-quadratic scaling failures and positional encoding redundancy.

## 1. Master Literature Repository

| Paper ID | Year | Short Title | Search Bucket | Primary Source (Investigator/Subagent) |
| :--- | :--- | :--- | :--- | :--- |
| `204e3073870fae3d05bcbc2f6a8e263d9b72e776` | 2017 | Attention is All You Need | `seed_metadata` | All Subagents |
| `43428880d75b3a14257c3ee9bda054e61eb869c0` | 2017 | ConvS2S Learning | `foundational_references` | `inv_01_sub_01` |
| `c8efcc854d97dfc2a42b83316a2109f9d166e43f` | 2018 | Relative Pos. Representations | `closest_prior_work` | `inv_02_sub_01` |
| `1a703f08da01cf737cce3fb9064259b3f4b44e9c` | 2021 | Linear Transformers are Fast Weights | `closest_prior_work` | `inv_01_sub_01` |
| `a2fc77f075f666b462d9350e7576f0ba9845c61b` | 2022 | No-PE Potential | `foundational_references` | `inv_02_sub_02` |
| `c487dd8dabfdc6cd3aed6c03c5d8cddef4980ed7` | 2022 | Equivariance Discovery | `nearby_pub_competitors` | `inv_02_sub_01` |
| `debbb47abc9fb757857f7c06aa86ca558d37c2d7` | 2023 | 2-D SSM spatial layers | `recent_followups` | `inv_02_sub_02` |
| `9c71d178705989cd4371f8e760508f11b18a4bb4` | 2023 | Practical Computational Power | `recent_followups` | `inv_01_sub_01` |
| `fa2f8963df88d8684b38c33aa59cc3ae0927561b` | 2024 | SSM Long Sequence Failures | `critiques_limitations` | `inv_01_sub_02` |
| `428c6bd657229d4f3360b5f5920ad3609739ecdc` | 2024 | Hierarchically Pruned Attention (HiP) | `recent_followups` | `inv_01_sub_01` |
| `23ff21c3608b641c32b5fe191dcc307071e829b5` | 2025 | LEDiT (Length-Extrapolable DiT) | `recent_followups` | `inv_02_sub_02` |
| `11e420bbcd5fce960e737318a8d625095bb61a6a` | 2025 | Approx Diverse k-NN Search | `recent_followups` | `inv_01_sub_01` |

## 2. Integrated Evidence Gaps & Contradictions

### A. The Addressability Conflict (Retreival vs. Recurrence)
*   **Gap:** State-space models and linear transformers (SSMs/RNNs) achieve $O(N)$ scaling but fail on high-precision "pointer" tasks like Needle-In-A-Haystack (NIAH).
*   **Evidence:** `fa2f8963df88d8684b38c33aa59cc3ae0927561b` (Huang 2024) identifies that pure recurrence loses the addressable query-pointer resolution of the KV cache.
*   **Contradiction:** Theoretically infinite context in SSMs vs. empirical "lost-in-the-middle" and NIAH collapse.

### B. The Positional Redundancy Conflict (Implicit vs. Explicit)
*   **Gap:** Models use explicit encodings (RoPE) to solve for position, while the causal mask already encodes global position via predecessor counting. 
*   **Evidence:** `a2fc77f075f666b462d9350e7576f0ba9845c61b` (Haviv 2022) and `23ff21c3608b641c32b5fe191dcc307071e829b5` (Zhang/LEDiT 2025). Explicit PE prevents scaling to OOD coordinate values that the implicit signal naturally handles.
*   **Conflict:** Explicit PE provides high-frequency local syntax ("sharpness") but breaks global sequence extrapolation.

### C. The Locality Trap (Index Pruning vs. Global Dependencies)
*   **Gap:** Sub-quadratic pruning ($O(T \log T)$) typically assumes "attention locality."
*   **Evidence:** `428c6bd657229d4f3360b5f5920ad3609739ecdc` (Lee/HiP 2024). Locality-driven tree search fails when relevant tokens are scattered randomly (e.g., repository-level search).
*   **Conflict:** Scalability is achieved by the very assumption that breaks the model on non-linear datasets.

## 3. Historical Collision & Equivariance Log

| Target Mechanism | Modern SOTA | Mathematical Predecessor / Collision | Collision ID |
| :--- | :--- | :--- | :--- |
| **Linear Attention** | Linear Transformers (2020) | Fast Weight Programmers (1992) | `1a703f08` |
| **Toeplitz Bias** | T5 / ALiBi Relative Bias | Discrete Convolutions / LTI Filters | `c487dd8d` |
| **Approx. Attention** | HiP Pruning / H2O | Approximate k-NN / HNSW (2018) | `11e420bb` |
| **Invariance** | Vision SSMs | Shift-Invariant Filters | `debbb47a` |

## 4. Missing Search Zones & Novelty Risks

*   **RoPE vs. Absolute PE on Locality:** Subagent `inv_01_sub_02` noted it is unknown if "attention locality" is an inherent task property or an artifact of the Rotary Positional Embeddings (RoPE) itself.
*   **The "NoPE" Causal Resolution:** `inv_02_sub_02` identified a missing theoretical proof for the "resolution" of the causal mask's implicit positional signal. If the signal is too coarse, removing explicit PE (LEDiT approach) will fail on precise symbolic reasoning.
*   **Sub-Quadratic Gating Equivalence:** `inv_01_sub_02` recommended a search to determine if "addressability decay" in SSMs can be solved via better gating (Selective Scan) rather than external storage (ASSR proposal).

## 5. Investigator Coverage Summary

*   **Investigator 01:** Focused on compute complexity and retrieval failures. Mapped the convergence of attention and vector database search (k-NN). Surfaced the **ASSR** and **Differentiable HNSW** proposal seeds.
*   **Investigator 02:** Focused on signal processing properties (Toeplitz) and positional bias. Surfaced the contradiction between explicit PE and extrapolation. Surfaced the **SD-PB (Spectral Deconfliction)** and **Toeplitz Kernel** proposal seeds.