# Unresolved Conflicts

## 1. Technical Contradictions & Uncertainties

| Conflict Type | Description | Evidence/Papers Involved | Status |
| :--- | :--- | :--- | :--- |
| **Convergence vs. Divergence** | Uncertainty regarding whether kernel-based linear attention is converging toward the SSM approach or remains a distinct mathematical path for $O(n)$ modeling. | `subagent_01` Open Question; `fb03ce4d6deed5eb2a147b90095cf0c6e3233f21` (SSE) | **Unresolved** |
| **Hybrid Necessity** | Ongoing debate on whether "true" linear attention can eventually match quadratic reasoning/retrieval or if hybridity (combining sparse/full attention with linear/SSM) is a fundamental, permanent requirement for high-fidelity modeling. | `subagent_02` Contradictions; `ab42f869ecc9fbe9b83bd7372cd21dc4b0b2297a` (SALAD) | **Unresolved** |
| **Positional Encoding Dominance** | Tension between whether the success of hybrid models (e.g., TransXSSM) is driven by the mathematical integration of the architecture or the specific alignment of positional encodings (e.g., Unified RoPE). | `838e911ebe009dbadb87e6f78b654460c1cddd3a` (TransXSSM) | **Unresolved** |

## 2. Weak Evidence & Empirical Gaps

*   **The "Break-even" Point**: There is a lack of empirical data quantifying the exact sequence length $N$ where the efficiency gains of SSMs/Linear Attention outweigh the representational accuracy loss compared to $O(N^2)$ Transformers.
*   **Hardware-Kernel Parity**: Current evidence is insufficient to determine if Transformer dominance is due to architectural superiority or the existence of highly optimized kernels (e.g., FlashAttention) compared to emerging SSM kernels (e.g., Selective Scan).
*   **Hybrid Failure Modes**: While hybrid models (SALAD, TransXSSM) show promise, there is no documented analysis of "negative results," specifically regarding new bottlenecks such as pipeline stalls or synchronization delays introduced by branching between attention and SSM blocks.

## 3. Missing Literature Buckets

*   **Negative Results / Failure Analysis**: Literature explicitly analyzing where hybrid architectures or linear approximations fail in standard LLM benchmarks.
*   **Cross-Hardware Benchmarking**: Comparative studies of SSM vs. Transformer throughput across diverse hardware profiles (Edge/Mobile vs. H100/High-end Data Center).
*   **Long-Range Arena (LRA) Comparative Studies**: Comprehensive, head-to-head benchmarks of the newest hybrid models (SALAD, TransXSSM) against the standard LRA benchmark suite.

## 4. Failed Searches & Search Deficiencies

*   **Failed Specificity**: `paper_relevance_search` for "limitations of linear attention in context retrieval and reasoning" returned 0 results, suggesting a need to pivot toward broader "performance degradation" or "retrieval-gap" terminology.
*   **Failed Taxonomy**: The attempt to find a direct "limitations" comparison between linear and sparse attention via `paper_relevance_search` was unsuccessful, indicating these concepts may be buried in general "efficiency" or "optimization" surveys.

## 5. Required Follow-up Searches

To achieve confidence in architectural claims, the following searches are required:

1.  **Empirical Benchmarking**: `benchmarks comparing hybrid SSM-Transformer models on Long Range Arena (LRA) for retrieval tasks`
2.  **Kernel Throughput Analysis**: `implementation comparison FlashAttention vs Selective Scan kernel throughput on H100 vs edge devices`
3.  **Positional Encoding Validation**: `comparative study of RoPE vs convolutional positional encoding robustness in hybrid architectures`
4.  **Mechanism Deep-Dive**: `technical mechanisms and ablation studies of Sparse State Expansion (SSE) in linear attention`