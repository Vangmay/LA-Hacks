# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed Paper
- Why it matters: Foundational architecture for modern large language models; introduces the Transformer and the self-attention mechanism, dispensing with recurrence and convolutions.
- Caveat: Extremely well-studied; novelty must come from identifying tensions, contradictions, or failures in its core architectural assumptions (e.g., quadratic complexity, lack of inductive bias).


## Paper: VL-Mamba: Exploring State Space Models for Multimodal Learning

- Paper ID: 6d49ed0ea24b9c218f5ec6731cd261ce618df2ac
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Competitor/Alternative
- Why it matters: Explores using SSMs (Mamba) as a backbone for Multimodal LLMs to solve the quadratic complexity of Transformers in long-sequence multimodal inputs.
- Caveat: Primarily focuses on multimodal efficiency; doesn't address the fundamental 'retrieval' vs 'compression' tension.


## Paper: DELTA: Dynamic Layer-Aware Token Attention for Efficient Long-Context Reasoning

- Paper ID: c411e89ff7bedcbcc5a2abf959349ff0e5a7d344
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Potential Collision (Mechanism Differentiation required)
- Why it matters: Uses a three-tier layer partitioning (full attention $ightarrow$ selection $ightarrow$ sparse attention) to reduce computation. It focuses on *sparsifying* the attention mechanism rather than replacing it with an alternative kernel like SSMs.
- Caveat: It targets the *sparsity* of attention, not the *architectural paradigm* of SSMs.


## Paper: MambaVSR: Content-Aware Scanning State Space Model for Video Super-Resolution

- Paper ID: a4e0a277bbde734911e8173836037330de597986
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Partial Collision (Scan mechanism)
- Why it matters: Introduces a content-aware scanning mechanism (CAS) for SSMs in video tasks to replace rigid 1D sequential processing.
- Caveat: Focuses on the *scanning pattern* within the SSM rather than the *routing* between Attention and SSM kernels.


## Paper: MamTrans: magnetic resonance imaging segmentation algorithm for high-grade gliomas and brain meningiomas integrating attention mechanisms and state-space models

- Paper ID: 9c553eda5579ae95b8c46073df9ab16ff10ade48
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Partial Collision (Hybrid paradigm)
- Why it matters: Integrates SSMs and attention for medical image segmentation, claiming improved efficiency and accuracy.
- Caveat: Like MetaMamba-Aesthetic, this is a domain-specific hybrid (medical imaging) and appears to follow a static or fixed combination rather than the proposed dynamic, content-dependent kernel routing.
