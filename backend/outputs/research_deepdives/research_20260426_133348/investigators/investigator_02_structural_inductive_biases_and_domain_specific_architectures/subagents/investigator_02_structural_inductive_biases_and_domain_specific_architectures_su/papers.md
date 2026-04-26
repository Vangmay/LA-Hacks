# Papers



## Paper: Attention is All you Need

- Paper ID: `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (ARXIV:1706.03762)
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed paper itself.
- Why it matters: Establishes the Transformer architecture, replacing recurrence and convolutions with a pure attention mechanism. It introduces the fundamental inductive bias of 'permutation equivariance' (mitigated by positional encodings) and global dependency modeling.
- Mechanism: Multi-head scaled dot-product attention, residual connections, and layer normalization in an encoder-decoder structure.
- Caveat: The paper's claim of 'all you need' focuses on standard NLP sequence tasks; structural constraints for non-sequence domains (e.g., graphs, 3D manifolds) were left for later work.


## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed paper
- Why it matters: Establishes the Transformer architecture, replacing recurrence and convolution with self-attention. It serves as the primary structural baseline for investigating inductive biases like position encoding, multi-head attention, and residual connections.
- Caveat: Massive citation count (173k+) makes finding specific structural critiques difficult without targeted queries.


## Paper: The Inductive Bias Gap (Gong et al., 2026)

- **Paper ID**: c16ab403e6ad7c01870a60f3e11f817c198a9e65
- **Year**: 2026
- **Source bucket**: relevance_search
- **Found by**: query: 'transformer inductive bias limitations failure modes'
- **Relation to seed**: Directly critiques the 'no-inductive-bias' philosophy of 'Attention is All You Need' for fine-grained computer vision.
- **Why it matters**: Introduces the 'Local Focus Ratio' metric, providing a concrete way to measure where attention mechanisms fail to localize critical features compared to CNNs.
- **Caveat**: Analysis is focused on FER; needs verification on broader datasets like COCO or medical imaging.


## Paper: Equivariant Spherical Transformer for Efficient Molecular Modeling

- Paper ID: `e624095a92845f8bab49c00090f52d129d0f583b` (ARXIV:2505.23086)
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Extends the Transformer's attention mechanism to the Fourier spatial domain of group representations (specifically SE(3) symmetries for molecules).
- Why it matters: It addresses a key limitation of standard Transformers: they lack inherent SO(3)/SE(3) equivariance, which is vital for physical systems. The paper uses 'Spherical Transformer' (EST) to avoid the high cost of Clebsch-Gordan tensor products by performing attention in the Fourier domain.
- Mechanism: Uniform sampling of spherical Fourier transforms combined with Transformer-like blocks specifically for group representations.
- Caveat: Performance gains are primarily shown on molecular datasets (OC20, QM9); generalization to other manifold-type data remains an open question.


## Paper: Are Sixteen Heads Really Better than One?

- Paper ID: b03c7ff961822183bab66b2e594415e585d3fd09
- Year: 2019
- Source bucket: foundational_references
- Found by: paper_bulk_search
- Relation to seed: Direct structural audit of the Transformer architecture.
- Why it matters: Demonstrates that a large percentage of attention heads are redundant at inference time. This supports my 'Efficiency Auditor' worldview by showing that the 'prestige complexity' of many heads may not be load-bearing for the task.
- Caveat: Pruning is done at test time; training might still require multiple heads for optimization stability.


## Paper: Pruning LLMs to Intra-module Low-rank Architecture (TransAct)

- Paper ID: c2d2dbb6b2d82308a7a354468574623a378c4cc0
- Year: 2024
- Source bucket: recent_followups
- Found by: paper_bulk_search
- Relation to seed: Modern sequel to the pruning/redundancy conversation started by the 2019 Michel et al. paper.
- Why it matters: Proposes 'TransAct', which specifically targets redundancy in MHA and MLP modules by pruning them into low-rank architectures. This validates that the 2017 Transformer's structural blocks are still significantly over-parameterized in 2024 models (like LLaMA).
- Caveat: Focuses on activation-guided pruning rather than removing full heads, suggesting that partial head redundancy is a more granular audit target.
