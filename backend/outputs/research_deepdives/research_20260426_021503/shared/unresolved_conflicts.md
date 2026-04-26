# Unresolved Conflicts

This document identifies the contradictions, evidentiary gaps, and search failures that must be addressed before the proposed `S3A` and `CFMA` candidates can be promoted to high-confidence research directions.

## 1. Technical Contradictions & Tensions

### A. Efficiency vs. Complexity (S3A Conflict)
There is a direct tension between the **Synchronous Semantic-Spatial Alignment (S3A)** proposal and the contemporary research trend toward **"frugal" and "edge-ready" models** (as evidenced by ECViT 2025 and recent 2026 hybrid studies). 
- **The Conflict**: S3A proposes adding a Cross-Scale Contrastive Module to synchronize feature spaces. This increases computational overhead (FLOPs) and parameter count, potentially contradicting the industry push for high-efficiency, low-latency deployment in specialized domains (medical/remote sensing).

### B. Scaling vs. Structural Prior (Architecture Conflict)
A fundamental disagreement exists regarding how to achieve performance gains:
- **Scaling Path**: Tay et al. (2022) suggests that architecture choice interacts with scaling laws, implying that massive data/parameters might eventually compensate for lack of bias.
- **Structural Path**: Recent hybrid trends (ECViT 2025, CTLE 2025) suggest that structural inductive biases (CNN/LSTM integration) are necessary for efficiency and precision.
- **The Conflict**: It is unclear whether the "third way" (a unified architecture) is a superior long-term solution or if the field will bifurcate into "massive pure Transformers" and "small highly-biased hybrids."

### C. Continuous vs. Discrete Composition (CFMA Conflict)
The **Continuous Functional Manifold Augmentation (CFMA)** proposal assumes a continuous, differentiable state is the optimal way to handle composition.
- **The Conflict**: Strong recent work (Soulos et al. 2023; RetoMaton 2025) suggests that **discrete, structured operations** (Tree Machines, Weighted Finite Automata) are more effective for compositional generalization. It remains unresolved if a continuous manifold is a more general solution or if it is merely a less efficient approximation of discrete symbolic logic.

---

## 2. Weak Evidence & Speculative Claims

| Claim | Source | Weakness/Risk |
| :--- | :--- | :--- |
| **Transformer Compositional Ceiling** | Peng et al. (2024) | The proof relies on **unproven computational complexity conjectures**. The "impossibility" of composition might be a theoretical boundary that does not reflect empirical scaling reality. |
| **CoT Insufficiency** | Zubic et al. (2024) | The evidence is primarily framed within **State Space Models (SSMs)**. While linked to Transformers, the direct applicability of these complexity limits to large-scale Transformer-based LLMs is not fully formalized. |
| **Hybridization Dominance** | 2026 Literature | The high citation/relevance of 2026 hybrid papers may be a **recency/novelty bias** rather than proof that the "pure Transformer" era is functionally over. |
| **Bottleneck Attribution** | CFMA Hypothesis | There is no evidence yet that the compositionality bottleneck is the **state-passing mechanism** rather than the **token representational capacity** itself. |

---

## 3. Missing Literature Buckets

- **Universal Scaling Laws for Composition**: Lack of literature quantifying how scaling laws change specifically when the target task is defined by *compositional depth* rather than mere *sequence length*.
- **Continuous-Time Neuro-Symbolic Hybrids**: A gap exists between the "continuous" approach (Neural ODEs/CFMA) and the "symbolic/discrete" approach (Tree Machines/RetoMaton). No papers currently attempt to fuse continuous manifolds with discrete logical operations.
- **Complexity-Aware Alignment**: Lack of studies quantifying the "alignment tax"—the exact trade-off between semantic synchronization accuracy and inference latency in hybrid models.

---

## 4. Failed Searches

The following queries returned **0 results**, indicating either a highly specialized niche or a need for broader/alternative terminology:
- `formal comparison of inductive biases in convolutional neural networks and vision transformers`
- `"hybrid" AND ("CNN" OR "convolutional") AND "Transformer" AND ("interface" OR "fusion" OR "bottleneck")`
- `architectural solutions for function composition in Transformers`
- `differentiable scratchpad transformer external memory compositionality`
- `neural functional composition architectures differentiable state`

---

## 5. Required Follow-up Searches

To resolve the conflicts above, the following searches are mandatory before promoting candidates:

### For S3A (Alignment)
1. **Adversarial Phrase Search**: Exact-phrase search for `"semantic alignment module"` and `"cross-scale feature synchronization"` in CVPR/ICCV/NeurIPS (2024–2026).
2. **Complexity Audit**: Search for `"alignment overhead"` or `"computational cost of feature fusion"` in hybrid vision models to quantify the "alignment tax."

### For CFMA (Composition)
1. **Mechanism Collision Search**: Search for `"continuous state space transformers"` and `"differentiable functional manifold reasoning"` to ensure the idea is not a subset of emerging SSM-Transformer research.
2. **Cross-Paradigm Search**: Search for `"continuous-time neuro-symbolic"` or `"differentiable automata" AND "transformers"` to bridge the continuous vs. discrete gap.
3. **Bottleneck Verification**: Search for `"token capacity vs communication complexity in composition"` to determine if the state-passing or the embedding space is the true limiting factor.