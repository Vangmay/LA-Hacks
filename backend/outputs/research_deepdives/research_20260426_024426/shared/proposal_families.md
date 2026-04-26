# Proposal Families

## Family 1: Hybrid Efficiency Mechanisms
*This family focuses on resolving the fundamental tension between the $O(N^2)$ expressiveness of Transformers and the $O(N)$ efficiency of SSMs/Linear Attention through structural modularity.*

### Seed 1.1: Dual-Branch Sparse-Linear Hybridization
*   **Mechanism**: Implementing a parallel architectural split where a high-sparsity attention branch handles localized, high-precision tokens while a linear/SSM branch manages long-range global context.
*   **Evidence Support**: 
    *   `ab42f869ecc9fbe9b83bd7372cd21dc4b0b2297a` (SALAD) demonstrates that scaling a lightweight linear branch alongside sparse attention can achieve 90% sparsity with minimal quality loss.
    *   `5cc392b47433b24b0c198e781fee287bede1a575` (ScatterFormer) suggests that structured/scattered patterns can optimize linear attention for specific data geometries.
*   **Closest-Prior/Future-Work Collision Risks**: 
    *   *Collision*: Directly competes with the architectural approach of SALAD (2026). 
    *   *Mitigation*: Shift focus from "video diffusion" (SALAD's domain) to "general-purpose reasoning" or "multi-modal" applications.
*   **Validation Path**: Benchmark on the **Long Range Arena (LRA)** to quantify the trade-off between sparsity levels and retrieval accuracy.

### Seed 1.2: Unified Positional-State Integration
*   **Mechanism**: Developing a cohesive encoding scheme that reconciles explicit rotational embeddings (RoPE) with the implicit, convolutional-style state updates used in SSMs to prevent information degradation during hybrid inference.
*   **Evidence Support**: 
    *   `838e911ebe009dbadb87e6f78b654460c1cddd3a` (TransXSSM) identifies "Unified RoPE" as a critical component for functional hybrid Transformer-SSM models.
*   **Closest-Prior/Future-Work Collision Risks**: 
    *   *Collision*: High risk of redundancy with TransXSSM (2025).
    *   *Mitigation*: Focus on the *stability* of these embeddings during extreme sequence length scaling (e.g., $>1M$ tokens) rather than just the unification mechanism.
*   **Validation Path**: Comparative study of perplexity and positional robustness in hybrid models vs. pure Transformers as $N$ scales.

---

## Family 2: Expressiveness-Enhanced Linear Models
*This family targets the "Retrieval/Reasoning Gap" by augmenting the internal capacity of linear-time models without reverting to quadratic complexity.*

### Seed 2.1: Sparse State Expansion (SSE) for Reasoning
*   **Mechanism**: Decoupling parameter count from state capacity via partitioned, row-sparse state updates, allowing the model to maintain "high-fidelity" memory without the quadratic cost of full attention.
*   **Evidence Support**: 
    *   `fb03ce4d6deed5eb2a147b90095cf0c6e3233f21` (2025) proposes SSE specifically to address the reasoning degradation in linear models.
*   **Closest-Prior/Future-Work Collision Risks**: 
    *   *Collision*: Direct overlap with existing SSE research.
    *   *Mitigation*: Investigate the interaction between SSE and **non-linear SSMs** (e.g., `e1e98a053a81b96d93c30a5c2b0f0f76b06f9571`) to see if non-linearity further mitigates the reasoning gap.
*   **Validation Path**: Targeted "Needle in a Haystack" retrieval tests and complex multi-step reasoning benchmarks.

---

## Family 3: Hardware-Architectural Co-Optimization
*This family explores whether the current dominance of Transformers is architectural or a byproduct of kernel-level optimization.*

### Seed 3.1: Throughput-Aware Kernel Synthesis
*   **Mechanism**: Designing architectures specifically to minimize pipeline stalls between heterogeneous modules (e.g., switching between a FlashAttention kernel and a Selective Scan kernel in a hybrid model).
*   **Evidence Support**: 
    *   Subagent 01 identifies a critical uncertainty: whether Transformer dominance is due to optimized GPU kernels (FlashAttention) vs. architectural superiority.
    *   Subagent 02 notes the lack of evidence regarding hybrid failure modes (e.g., pipeline stalls).
*   **Closest-Prior/Future-Work Collision Risks**: 
    *   *Collision*: Low architectural collision, but high technical difficulty in kernel implementation.
*   **Validation Path**: Empirical benchmarking of "Selective Scan" vs. "FlashAttention" throughput on diverse hardware (NVIDIA H100 vs. Edge/Mobile NPUs) to find the **empirical break-even point**.

---

## Summary of Missing Evidence (Required for Validation)
To move these proposals from seeds to active research, the following gaps must be closed:
1.  **Empirical Break-even Data**: Quantifying the exact sequence length $N$ where $O(N)$ efficiency compensates for $O(N^2)$ accuracy loss.
2.  **Hybrid Bottleneck Analysis**: Identifying where hybridity introduces memory overhead or latency spikes due to kernel switching.
3.  **Positional Robustness**: Determining if "Unified RoPE" is a sufficient solution for the integration friction in long-context SSM-hybrids.