# Global Evidence Map

This map synthesizes the evidence gathered across three major research investigations into the Transformer architecture, focusing on three fundamental tensions: **Computational Complexity ($O(L^2)$)**, **Mechanistic Interpretability (Faithfulness)**, and **Training-Inference Discrepancy (Exposure Bias)**.

## 1. Core Research Dimensions & Synthesis

| Dimension | Primary Tension | Key Research Gap | Synthesis Status |
| :--- | :--- | :--- | :--- |
| **Efficiency** | $O(L^2)$ Complexity vs. High-Precision Reasoning | The "Soft-Switch" Gap: Absence of continuous, differentiable blending between Attention and SSMs. | **High** (Evidence of saturation in kernel/linear attention; presence of discrete hybrid routing). |
| **Interpretability** | Visible Attention Weights vs. Causal Faithfulness | The "Granularity Gap": Causal mediation currently targets heads/MLPs, not granular weight-level faithfulness. | **Medium** (Strong critique exists; techniques for component identification are established). |
| **Optimization** | Error Recovery vs. Semantic Fidelity | The "Over-Correction" Problem: RL/DPO methods for exposure bias often sacrifice fidelity for recovery. | **High** (Documented divergence in NMT; opportunity for constrained optimization). |

---

## 2. Evidence & Paper Mapping

### A. Architectural Foundations & Lineage
*Foundational works establishing the baseline and its immediate evolutionary pressures.*

| Paper ID | Title / Topic | Year | Role | Subagent(s) |
| :--- | :--- | :--- | :--- | :--- |
| `204e3073870fae3d05bcbc2f6a8e263d9b72e776` | **Attention is All You Need** | 2017 | **Seed Paper**: Established the Transformer paradigm. | All |
| `43428880d75b3a14257c3ee9bda054e61eb869c0` | Convolutional Seq2Seq | 2017 | **Ancestor**: Pre-Transformer parallelizable alternative. | `inv_01_sub_01` |
| `fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5` | Bahdanau Attention | 2014 | **Ancestor**: Precursor to self-attention. | `inv_02_sub_01` |

### B. Efficiency, Linearization, & Hybridization
*Mapping the transition from quadratic attention to linear/SSM-based scaling.*

| Paper ID | Title / Topic | Year | Key Finding / Role | Subagent(s) |
| :--- | :--- | :--- | :--- | :--- |
| `cbaf689fd9ea9bc939510019d90535d6249b3367` | **Jamba** | 2024 | **Collision**: Successful interleaved Transformer-Mamba model. | `inv_02_sub_01`, `inv_03_sub_02` |
| `8a3ee6b06695a444b63e79d9ff542d1c7c7b947a` | **MambaFormer** | 2026 | **Collision**: Implements discrete (hard) token-level routing. | `inv_02_sub_01`, `inv_02_sub_02` |
| `e62198fd44c62b890c99e738e02ec5064cd6ec93` | **LaplacianFormer** | 2026 | **Collision**: Recent kernel-based linearization (Vision-focused). | `inv_01_sub_01`, `inv_02_sub_01` |
| `ae77842be0aebc13b208726a2b5f3565dcd2e66a` | **Echo State Transformer** | 2025 | **Precedent**: Attention over fixed-size reservoir memory. | `inv_02_sub_02` |
| `327d3bb056e1456bb96ff711a2ec54317ca61feb` | **KV Admission** | 2025 | **Precedent**: Proactive, learned admission control for KV caches. | `inv_01_sub_01` |
| `0502ad3507b437af48afb3cd8bb4c2d1875bcbff` | **Information Density** | 2023 | **Theory**: Provides framework for surprisal/entropy gating. | `inv_01_sub_01` |

### C. Interpretability & Faithfulness
*Evidence regarding the reliability of attention as an explanatory mechanism.*

| Paper ID | Title / Topic | Year | Key Finding / Role | Subagent(s) |
| :--- | :--- | :--- | :--- | :--- |
| `ChQ_Pm3AqM4J` | **Attention is not explanation** | 2019 | **Critique**: Foundation of the faithfulness skepticism. | `inv_01_sub_02` |
| `5dc15ac1c92ab7492f121471823fb13a95d273ba` | **Causal Mediation** | 2023 | **Precedent**: Uses causal intervention for component identification. | `inv_01_sub_02` |
| `60bf56ed72d032600f01161fd40769273bef84a8` | **Emergent Unfaithfulness** | 2026 | **Evidence**: Proves unfaithfulness is an emergent training property. | `inv_03_sub_03` |
| `6968f45aabe7b328bb322bc35c808a6d5e5ea006` | **FaithCoT-Bench** | 2025 | **Benchmark**: Instance-level faithfulness detection. | `inv_03_sub_03` |

### D. Alignment, Exposure Bias, & Training Dynamics
*Evidence on the trade-offs in training and optimizing Transformers.*

| Paper ID | Title / Topic | Year | Key Finding / Role | Subagent(s) |
| :--- | :--- | :--- | :--- | :--- |
| `2ef10559f59f3877ff7b3babfcc12972ceee842e` | **Recovery vs. Deviation** | 2024 | **Gap Trigger**: Mitigating exposure bias can cause "over-correction" and semantic drift. | `inv_01_sub_03`, `inv_01_sub_03` |
| `6c6d2ac4f7c94b30ceef79ba3e72840d0f4ba1d0` | **DPO for NMT** | 2023 | **Collision**: Preference optimization for sequence-level objectives. | `inv_01_sub_03` |
| `db0ef40e1985037eebde306bd91a1bc71836b3e1` | **Contrastive Preference** | 2024 | **Collision**: List-wise preference modeling for alignment. | `inv_01_sub_03` |
| `01021187b2ac3b2341b674c2063b1566b87ec6ef` | **VERITAS** | 2025 | **Precedent**: Fine-grained faithfulness rewards in RL (RAG-focused). | `inv_03_sub_03` |

---

## 3. Identified Research Gaps & Novelty Drivers

| Gap Category | Evidence-Based Trigger | Novelty Driver |
| :--- | :--- | :--- |
| **Hybrid Granularity** | MambaFormer (2026) uses discrete routing; no evidence for "soft" or continuous blending of Attention/SSM kernels. | **Continuous/Soft Hybridization** |
| **Structural Stability** | "Routing Absorption" (09346bf8ba00e9ecf6b4ce2b3f03d9c69d0d7d8a) proves per-query gating is unstable; no end-to-end learned layer-wise/block-wise topology. | **Decoupled Topology Learning** |
| **Reward Consistency** | Emergent unfaithfulness (60bf56ed72d032600f01161fd40769273bef84a8) and "over-correction" (2ef10559f59f3877ff7b3babfcc12972ceee842e) suggest a need for explicit constraints. | **Constrained Policy Optimization** |
| **Internal Dynamics** | RC-NLP (ea78c1c0c4b19d13b405c3c2b8151df9d68f2838) only applies attention to readouts; no attention-driven "sculpting" of internal reservoir states. | **Attentional State-Updating Reservoir (ASUR)** |