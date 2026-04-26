# Papers



## Paper: Attention is All you Need

- Paper ID: `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (ARXIV:1706.03762)
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Root seed paper
- Why it matters: This is the foundational Transformer paper which replaced recurrent and convolutional layers with global attention. While it claims "Attention is All You Need," the quadratic complexity of standard attention (O(n^2)) is the primary bottleneck that motivates subsequent work in sparsity and dynamic computation. My research will focus on how this bottleneck was addressed by looking for older mechanisms (e.g., from the 90s) and modern sparse variations.
- Caveat: Its performance is highly dependent on large-scale training and specific initialization (Warmup, LayerNorm), which are often overlooked compared to the attention mechanism itself.


## Paper: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer

- Paper ID: `510e26733aaff585d65701b9f1be7ca9d5afc586` (ARXIV:1701.06538)
- Year: 2017
- Source bucket: foundational_references
- Found by: get_references (from seed paper)
- Relation to seed: Co-authored by Vaswani and Shazeer; foundational for conditional computation.
- Why it matters: This paper introduced the modern Sparsely-Gated MoE, which allows scaling model capacity by orders of magnitude without a proportional increase in computation. It is the primary mechanism for 'dynamic computation' in large-scale Transformers today. My 'dredger' taste notes that while this is a 2017 paper, it cites the 'Mixture of Experts' concept from the 90s, which I need to investigate for earlier sparse precedents.
- Caveat: Relies on a sophisticated gating function to maintain expert balance, which can be unstable or lead to expert collapse.


## Paper: Convergence Results for the Em Approach to Mixtures of Experts Architectures

- Paper ID: `fb4bb554ebc6a8a29a663f3a9100723c06f3e242` 
- Year: 1993
- Source bucket: foundational_references
- Found by: paper_bulk_search
- Relation to seed: Historical predecessor of the MoE used in modern Transformers.
- Why it matters: This work (Jordan & Xu) formalized the statistical foundation of Hierarchical Mixtures of Experts (HME). Unlike modern deep-learning MoE which often uses gradient-based routing, this early era relied on Expectation-Maximization (EM). My research curiosity is triggered by the fact that EM-based gating is inherently 'discrete' and sparse, whereas modern softmax gating is a continuous approximation. This suggests a potential gap: could modern models benefit from returning to EM-style discrete optimization for expert selection?
- Caveat: EM algorithms were famously difficult to scale and parallelize compared to modern backpropagation, which is likely why they were superseded.


## Paper: Fmmformer: Efficient and flexible transformer via decomposed near-field and far-field attention

- Paper ID: `Trugkv771IQJ` (NeurIPS 2021)
- Year: 2021
- Source bucket: recent_followups
- Found by: google_scholar_search
- Relation to seed: Direct efficiency-oriented followup addressing the $O(n^2)$ bottleneck.
- Why it matters: This paper explicitly bridges the gap between the Fast Multipole Method (FMM) from 1980s/90s physics (Rokhlin/Greengard) and modern Transformer attention. It decomposes attention into near-field (high precision, local) and far-field (low precision, global/sparse) components, reducing complexity to $O(n)$. It confirms that 'novel' sparse patterns are actually realizations of classic N-body interaction mathematics.
- Caveat: Implementation complexity of FMM is significantly higher than standard attention, which may hinder adoption in standard libraries like PyTorch or JAX compared to simple sparse masks.


## Paper: Conditional computation in neural networks for faster models

- Paper ID: `ARXIV:1511.06297` (Bengio et al., 2015)
- Year: 2015
- Source bucket: foundational_references
- Found by: google_scholar_search
- Relation to seed: Direct predecessor to the Sparse MoE used in modern Transformers.
- Why it matters: Emmanuel Bengio and colleagues formulated conditional computation as a Reinforcement Learning problem (using policies to decide which parts of a network to activate). This paper is a critical bridge because it attempts to solve the 'discrete' activation problem using policy gradients (REINFORCE) before the field largely settled on the continuous relaxations used in Shazeer's MoE (2017). It represents a 'lost' path of using RL for dynamic computation.
- Caveat: Training with REINFORCE is high-variance and often less stable than gradient-based methods, which led to the popularization of easier-to-train relaxations.
