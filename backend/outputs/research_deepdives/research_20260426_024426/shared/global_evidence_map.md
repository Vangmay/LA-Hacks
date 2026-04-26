# Global Evidence Map

## Research Objective: `literature_review`
**Theme:** Transformer Architectural Evolution & The Efficiency-Expressiveness Trade-off.

---

## 1. Literature Mapping by Search Bucket

### Foundational & Ancestry (Pre-2017)
*Focus: Transition from recurrence/convolution to pure attention.*

| Paper ID | Year | Key Finding | Surfaced By |
| :--- | :--- | :--- | :--- |
| `2e9d221c206e9503ceb452302d68d10e293f2a10` | 1997 | Foundational LSTM/Recurrence mechanism; the paradigm Transformer bypassed. | `subagent_01` |
| `cea967b59209c6be22829699f05b8b1ac4dc092d` | 2014 | Established Seq2Seq framework using LSTMs. | `subagent_01` |
| `fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5` | 2014 | Introduced foundational alignment/attention in NMT. | `subagent_01` |
| `2c03df8b48bf3fa39054345bafabfeff15bfd11d` | 2015 | Structural analogue: Introduced residual connections (ResNet). | `subagent_01` |
| `43428880d75b3a14257c3ee9bda054e61eb869c0` | 2017 | Near-publication competitor: Parallelizable CNN-based Seq2Seq. | `subagent_01` |

### Modern Competitors: SSMs & Linear Models (2024–2025)
*Focus: $O(N)$ scaling and the "Retrieval/Reasoning Gap".*

| Paper ID | Year | Key Finding | Surfaced By |
| :--- | :--- | :--- | :--- |
| `ba4c5a116d07b37dea1046b6d16a60cb2d01cd47` | 2024 | Mamba-360: Taxonomy of SSMs as Transformer alternatives. | `subagent_01` |
| `124374e44e4eb63248d303c2623671626ffc7354` | 2025 | SSM Evolution Survey: Mapping S4 to Mamba. | `subagent_01` |
| `e1e98a053a81b96d93c30a5c2b0f0f76b06f9571` | 2025 | Stability: Parallelization of non-linear SSMs for scale. | `subagent_01` |
| `fb03ce4d6deed5eb2a147b90095cf0c6e3233f21` | 2025 | Mitigating the reasoning gap via Sparse State Expansion (SSE). | `subagent_02` |

### Hybrid & Specialized Architectures (2024–2026)
*Focus: Merging global efficiency with local precision.*

| Paper ID | Year | Key Finding | Surfaced By |
| :--- | :--- | :--- | :--- |
| `838e911ebe009dbadb87e6f78b654460c1cddd3a` | 2025 | TransXSSM: Resolves positional encoding mismatch via Unified RoPE. | `subagent_02` |
| `ab42f869ecc9fbe9b83bd7372cd21dc4b0b2297a` | 2026 | SALAD: High-sparsity hybrid (Sparse + Linear attention). | `subagent_02` |
| `5cc392b47433b24b0c198e781fee287bede1a575` | 2024 | ScatterFormer: Efficient voxel-based linear attention. | `subagent_02` |
| `7da115e0faa8fc7693e7595f846e6530f84eb378` | 2025 | FLASepformer: Applying linear attention to speech separation. | `subagent_01` |
| `e48a7076e51e851b6d5e74d902135f61043824a2` | 2026 | TactileFormer: CNN-Transformer hybrid for sensory perception. | `subagent_01` |

### Surveys & Taxonomies
| Paper ID | Year | Focus Area | Surfaced By |
| :--- | :--- | :--- | :--- |
| `014985747e905fa3e2c182d3e8f132d92936c833` | 2025 | Comprehensive taxonomy of Transformer optimization. | `subagent_02` |

---

## 2. Technical Synthesis: Tensions & Gaps

| Dimension | Technical Conflict / Tension | Evidence Basis |
| :--- | :--- | :--- |
| **Scaling Complexity** | $O(N^2)$ global expressiveness (Attention) vs. $O(N)$ efficiency (SSM). | `204e3073870fae3d05bcbc2f6a8e263d9b72e776` vs `ba4c5a116d07b37dea1046b6d16a60cb2d01cd47` |
| **Cognitive Fidelity** | The "Retrieval/Reasoning Gap": Linear models struggle with high-precision context retrieval. | `fb03ce4d6deed5eb2a147b90095cf0c6e3233f21` |
| **Structural Integration** | Positional Encoding Mismatch: RoPE (explicit) vs. SSM (implicit/convolutional) states. | `838e911ebe009dbadb87e6f78b654460c1cddd3a` |
| **System Stability** | Maintaining gradient flow/stability in non-linear SSMs during LLM-scale training. | `e1e98a053a81b96d93c30a5c2b0f0f76b06f9571` |

---

## 3. Missing Evidence & Underserved Search Areas

### 🔴 Critical Gaps (Insufficient Data)
* **Empirical Break-even Points**: Need quantitative data on the exact sequence length $N$ where SSM efficiency outweighs Transformer accuracy for specific reasoning tasks.
* **Hardware-Kernel Benchmarking**: Lack of head-to-head comparison between "Selective Scan" (SSM) kernels and "FlashAttention" kernels across diverse hardware (Edge vs. H100).
* **Hybrid Failure Modes**: Missing "negative results" regarding where hybridization (e.g., SALAD) introduces pipeline stalls or memory bottlenecks.

### 🔍 Recommended Search Vectors
1. **`benchmarks comparing hybrid SSM-Transformer models on Long Range Arena (LRA)`** (To address the reasoning gap).
2. **`implementation comparison FlashAttention vs Selective Scan kernel throughput`** (To address hardware-awareness).
3. **`comparative study of RoPE vs convolutional positional encoding in hybrid architectures`** (To validate Unified RoPE).
4. **`technical mechanisms of Sparse State Expansion in linear attention`** (To deepen understanding of SSE).