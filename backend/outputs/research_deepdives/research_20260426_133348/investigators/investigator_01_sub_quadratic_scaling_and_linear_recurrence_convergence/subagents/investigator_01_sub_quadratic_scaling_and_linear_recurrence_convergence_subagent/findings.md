# Findings



## Finding: Quadratic Bottleneck as the Baseline Complexity

- Claim: The standard Transformer self-attention mechanism, as established in the seed paper (Vaswani et al., 2017), scales quadratically O(N^2) with respect to sequence length N, making it computationally prohibitive for long-context applications.
- Confidence: High
- Evidence:
  - 204e3073870fae3d05bcbc2f6a8e263d9b72e776 | Attention is All you Need | 2017 | seed_metadata
- Why it matters: This quadratic scaling defines the 'complexity wall' that all follow-up works (Recurrent Transformers, Linear Transformers, SSMs) attempt to circumvent. My taste for 'Sentinel Complexity Limits' requires established lower bounds for this specific mechanism before evaluating sub-quadratic claims.
- Caveat: The paper argues that O(N^2) is offset by parallelizability compared to recurrent models, but this assumption breaks down as N significantly exceeds the hidden dimension d.


## Finding: Quadratic Scaling Bottleneck of Vanilla Attention

- Claim: The standard self-attention mechanism in the 2017 Transformer scales quadratically $O(N^2)$ with sequence length, creating a major efficiency barrier for long-context tasks.
- Confidence: high
- Evidence:
  - `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (Vaswani et al., 2017): The paper notes that while self-attention reduces the path length between tokens to $O(1)$, the computational complexity per layer is $O(n^2 \cdot d)$.
- Why it matters: This bottleneck is the primary motivator for the development of "Linear Transformers," State Space Models (SSMs), and other recurrence-based sub-quadratic models that attempt to regain the $O(N)$ scaling typical of RNNs while maintaining Transformer-like performance.
- Caveat: Quadracity is often manageable for short sequences (e.g., 512 tokens), but becomes the dominant cost in long-document processing or high-resolution image tasks.


## Finding: Convergence and State Tracking in SSM-based Linear Recurrences

- Claim: Recent linear-complexity models (e.g., Mamba-3) have transitioned to complex-valued state updates and MIMO formulations to solve the 'state tracking' failure mode of earlier linear recurrences.
- Confidence: high
- Evidence:
  - `02cbf7c87d721ca17b3416d2360350092a21c2c8` (Lahoti et al., 2026): Identifies that while linear models provide algorithmic efficiency, they traditionally fail on tasks requiring precise state-tracking. Mamba-3 uses complex-valued updates and more expressive recurrence derived from SSM discretization to achieve 1.8 point gains at 1.5B scale.
- Why it matters: This highlights that sub-quadratic scaling is no longer just about 'making attention linear' via kernels, but about the mathematical expressivity of the recurrence itself (spectral properties of the transition matrix).
- Caveat: Complex-valued states double the memory requirements for the latent state, partially offsetting the 'constant memory' benefit of recurrence during training if not carefully implemented.


## Finding: Formal Lyapunov Synthesis for Neural Stability

- Claim: It is possible to automatically synthesize Lyapunov functions for neural network dynamical systems to ensure asymptotic stability using machine learning and SMT solvers.
- Confidence: medium
- Evidence:
  - `b25eb299067a5447e3afd550909e6127a07a34f5` | Formal Synthesis of Lyapunov Neural Networks | 2020 | relevance_search
- Why it matters: This providing a formal path to ensure that the internal states of a linear recurrence do not explode or collapse, a frequent failure mode in long-context models that attempt to reach O(N) scaling. It validates the 'Technical Mechanism' in my proposal seed by showing that stability criteria can be baked into the network design rather than just observed post-hoc.
- Caveat: The existing papers focus on autonomous systems; adapting this to input-driven (non-autonomous) sequence models is the primary research frontier.


## Finding: SETH-Conditional Efficiency Transitions

- Claim: Sub-quadratic variants of modern sequence models (modern Hopfield/Attention) only exist below a specific pattern-norm criterion, under the Strong Exponential Time Hypothesis (SETH).
- Confidence: High
- Evidence:
  - 22910f92c164971ff6ae886ece9c586c703c7153 | On Computational Limits of Modern Hopfield Models | 2024 | relevance_search
- Why it matters: This identifies a rigorous 'Sentinel' boundary for research ideation. It implies that sub-quadratic efficiency isn't just a matter of better architecture, but is fundamentally prohibited if pattern norms (information energy) exceed a specific threshold. This provides the 'impossible regime' needed for a solid novelty proposal.
- Caveat: The bound is conditional on SETH, though SETH is widely accepted in fine-grained complexity Theory.


## Finding: Emerging Spectral Analysis in Sub-Quadratic LLMs

- Claim: The research landscape is shifting from purely 'making attention linear' to analyzing the spectral properties of the transfer operators and state matrices in recurrent models.
- Confidence: medium
- Evidence:
  - `Wyss (2025)` (Wyss, CM): Analyzes 'semantic collapse' by studying the spectral properties of transfer operators in LLMs.
  - `D. Shah (Survey)`: Catalogs 'Spectral SSMs' as a distinct subclass of State Space Models that leverage filter properties and relaxations of linear systems.
- Why it matters: It suggests that the 'Rate Tightener' taste is technically viable—optimizing the eigenvalue distribution of recurrent kernels can mitigate expressive failures (like semantic collapse or state-tracking loss).
- Caveat: Many 'spectral' analyses remain theoretical; the 'Mamba-3' complex-valued approach is the closest empirical implementation of these principles in a large-scale setting.


## Finding: Stability Gap in Input-Dependent Sub-Quadratic Models

- Claim: Modern input-dependent recurrent models (e.g., Mamba, Liquid-S4) lack formal gradient-stability guarantees, leading to potential training instability and memory collapse.
- Confidence: High
- Evidence:
  - `e1e98a053a81b96d93c30a5c2b0f0f76b06f9571` | LrcSSM | 2025 | relevance_search
  - `8fe9ba5ec118c32b3410b0b817b79666ff0951d4` | SpectralGuard | 2026 | relevance_search
- Why it matters: This gap confirms that the O(N) scaling achieved by late-stage SSMs has come at the cost of the theoretical stability inherent in vanilla Transformers. The discovery of papers like SpectralGuard (2026) suggests that 'memory collapse' is an active vulnerability in these architectures, making formal stability mechanisms (such as the Lyapunov proposal) a high-value research direction.
- Caveat: LrcSSM proposes a diagonal Jacobian solution, but this may restrict the model's expressively compared to fully-coupled recurrent states.
