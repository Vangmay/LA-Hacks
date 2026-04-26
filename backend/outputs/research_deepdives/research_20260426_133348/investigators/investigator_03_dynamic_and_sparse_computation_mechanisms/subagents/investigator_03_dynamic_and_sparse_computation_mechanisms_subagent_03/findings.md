# Findings



## Finding: MoE as the Primary Dynamic Mechanism in Transformers

- Claim: The most prominent dynamic computation mechanism in the Transformer lineage is the Sparsely-Gated Mixture-of-Experts (MoE) layer.
- Confidence: high
- Evidence:
  - Shazeer et al. (2017): 'Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer'
  - Vaswani et al. (2017): Citations to conditional computation in Section 2 (Background).
- Why it matters: It demonstrates that 'sparsity' in Transformers is often achieved by selecting a subset of parameters (experts) rather than using sparse attention matrices, which was the main path for scaling before recent linear-attention innovations.
- Caveat: MoE primarily addresses the FFN (Feed-Forward Network) bottleneck, not the O(n^2) self-attention bottleneck directly, though later work combines them.


## Finding: Discrete Optimization Gaps in Modern Sparsity

- Claim: Modern dynamic computation has shifted from discrete/statistical selection (EM-based) to continuous gradient approximations, leaving 'hard' expert routing underexplored for current scales.
- Confidence: medium
- Evidence:
  - Jordan & Xu (1993): 'Convergence Results for the Em Approach to Mixtures of Experts Architectures' demonstrates formal EM for discrete expert assignment.
  - Shazeer et al. (2017): Uses softmax-based 'noisy top-k' gating, which is a continuous relaxation to allow backpropagation.
- Why it matters: Continuous relaxations often lead to 'expert collapse' (all tokens going to one expert) and require complex load-balancing loss terms. The original EM-style discrete selection offered a more principled assignment that might be more robust if adapted to modern auto-differentiation (e.g., via Straight-Through Estimators or Reinforcement Learning).
- Caveat: Hard discrete selection can break the differentiability of the network, requiring specialized optimization techniques like REINFORCE or Gumbel-Softmax which have their own variance issues.


## Finding: Rediscovery of N-Body Numerical Methods for Sparse Attention

- Claim: The most technically sophisticated sparse attention mechanisms are formal rediscovery or adaptations of the Fast Multipole Method (FMM) from 1980s numerical analysis.
- Confidence: high
- Evidence:
  - Nguyen et al. (2021): 'Fmmformer: Efficient and flexible transformer via decomposed near-field and far-field attention' explicitly maps FMM near/far-field decomposition to attention matrices.
  - Mitchell & Kersting (2025): 'Multipole Semantic Attention' further refines this connection for pretraining.
- Why it matters: It suggests that the 'search for sparsity' in ML is converging on the same mathematical solutions used for gravitational and electrostatic simulations (O(n) complexity). This implies that future 'novel' attention patterns can likely be found by mining the last 40 years of N-body simulation literature, especially regarding adaptive mesh refinement and tree-codes.
- Caveat: The high constant factor in FMM often makes it slower than O(n log n) or even O(n^2) methods for moderate sequence lengths on modern SIMD hardware like GPUs.
