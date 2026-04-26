# Proposal Seeds



## Proposal Seed: Recurrence-Augmented Attention Sharpening

- Status: speculative
- Originating taste: optimizer_convergence_rate
- Seed-paper hook: Vaswani et al. (2017) explicitly avoids recurrence to facilitate parallelism.
- Evidence trigger: The trade-off between the O(N^2) global receptive field of Transformers and the O(N) efficient memory of RNNs.
- Candidate novelty: Bridging the gap by treating linear recurrences not just as a replacement for attention, but as a spectral filter that adaptively 'sharpens' the attention matrix before normalization, potentially improving the convergence rate of fixed-point iterations in recurrent Transformers.
- Technical mechanism: Implementing a linear recurrence step that acts as a low-rank approximation of the attention scores, using a state-space approach to propagate context with O(N) cost, then using that state to sparsify the dense attention map.
- Closest prior-work collision: Linear Transformers (Katharopoulos et al.), Mamba (Gu & Dao).
- Closest future-work collision: Hybrid architectures combining SSMs and Attention (e.g., Jamba).
- Minimum validation: Measure the perplexity vs. sequence length on the Long Range Arena for a toy 'Recurrent-Attention' hybrid.
- Falsification risk: Simple weight-averaging or soft-masking might achieve the same effect without the complexity of a recurrence kernel.
- Why this is not generic: It specifically targets the interaction between spectral properties of the recurrence and the attention coefficients to improve training stability.
- Confidence: low
- Required next search: Search for 'spectral properties of linear recurrence in transformers' or 'attention sharpening via SSMs'.


## Proposal Seed: Identifying Discrete Recurrence Limits in Large Scale SSMs

- Status: raw
- Originating taste: Sentinel Complexity Limits
- Seed-paper hook: Transition from O(N^2) attention to O(N) recurrence in linear models (from Vaswani 2017 to SSM/Linear Attention successors).
- Evidence trigger: The fundamental tradeoff between the infinite memory of O(N^2) attention and the finite state compression of O(N) recurrences.
- Candidate novelty: Formalization of 'state collapse' thresholds where linear recurrences fail to preserve long-range dependencies compared to quadratic models.
- Technical mechanism: Applying communication complexity lower bounds to the hidden state $h_t$ of a linear recurrence to determine the maximum entropy $S$ as a function of sequence length $N$.
- Closest prior-work collision: 'Transformers are RNNs' (Katharopoulos et al., 2020) and selective state space models (Mamba).
- Closest future-work collision: Recent scaling laws for SSMs.
- Minimum validation: Measure the capacity to recover specific bits from early in a sequence of length $N$ as $N$ surpasses the state dimension $D$.
- Falsification risk: Discovery that precision increases can arbitrarily delay state collapse without hitting a hard complexity limit.
- Why this is not generic: It focuses specifically on the *impossibility* of maintaining full-rank information in a sub-quadratic state, rather than just proposing a more efficient model.
- Confidence: low
- Required next search: Search for 'information capacity of linear recurrence hidden state' and 'lower bounds on selective state space models'.


## Proposal Seed: Lyapunov-Stable Linear Recurrence for Sub-Quadratic Attention Approximation

- Status: raw
- Originating taste: Proof-Technique Transplanter
- Seed-paper hook: Vaswani et al. (2017) established the O(n^2) complexity wall. Linear Transformers (Cathcart et al., 2020/2021) and SSMs (Gu et al., 2021) try to evade this using linear recurrences but hit stability/convergence bottlenecks on very long sequences.
- Evidence trigger: Finding: Quadratic Bottleneck as the Baseline Complexity. The failure of simple linear recurrences to capture long-range dependencies without exploding/vanishing gradients is the key gap.
- Candidate novelty: Transplanting the Discrete-Time Lyapunov Stability theorem from control theory into the initialization and projection layers of a linear recurrence transformer to guarantee stable convergence of the recurrence state even as $N \to \infty$.
- Technical mechanism: Formulate the recurrence state $h_t = A h_{t-1} + B x_t$. Instead of a free-form A, we constrain A such that the spectral radius $\rho(A) < 1$ using a parameterization derived from the Bilinear Transform or the Schur-Cohn algorithm to ensure the sequence of states $h_t$ converges to a bounded manifold.
- Closest prior-work collision: S4 (Structured State Spaces) uses HiPPO matrices for stability; Linear Transformers use cumulative sums (identity recurrence). This idea specifically targets stability through the lens of Lyapunov functions.
- Closest future-work collision: Mamba (Gu & Dao, 2023) uses selection mechanisms but does not explicitly use control-theoretic Lyapunov projection for global stability.
- Minimum validation: Test on the 'Long Range Arena' (LRA) benchmark, specifically the PathFinder-256 task where stability is crucial for performance.
- Falsification risk: The Lyapunov constraint might be too restrictive, preventing the model from learning fast-changing dynamics required for complex language tasks.
- Why this is not generic: It defines a specific mathematical constraint (Lyapunov projection) rather than a vague 'make it more stable' claim.
- Confidence: low
- Required next search: Search for 'Lyapunov stability in linear transformers' and 'discrete control theory lemmas for neural recurrence'.


## Proposal Seed: Complex-Spectral Recurrence Sharpening for Fixed-Point Convergence

- Status: promising
- Originating taste: optimizer_convergence_rate
- Seed-paper hook: Mamba-3 (Lahoti et al., 2026) uses complex-valued states to improve state-tracking.
- Evidence trigger: The contradiction between the need for 'expressive' complex states and the increased memory/compute overhead they introduce during the quadratic-to-linear distillation process shown in mmMamba (Liao et al., 2025).
- Candidate novelty: Instead of uniform complex updates, use the spectral properties of the recurrence to adaptively switch between real and complex kernels based on the 'sharpening' needs of the attention-approximation, effectively treating the recurrence as a complex-valued spectral optimizer.
- Technical mechanism: Implement a spectral gating mechanism that computes the eigenvalues of the linear recurrence matrix in O(1) time per step (for low-rank kernels) and uses imaginary components only when the recurrent state update enters a regime of low convergence (detected via moving average of state norm changes).
- Closest prior-work collision: Gated DeltaNet, Mamba-2/3.
- Closest future-work collision: Learned complex discretization in hybrid SSM-Transformers.
- Minimum validation: Test on the Associative Recall task from the Mamba paper, comparing 'spectral gating' vs full complex Mamba-3 in terms of FLOPs-per-token at equal accuracy.
- Falsification risk: Simple real-valued gating (like in Gated Linear Attention) might be sufficient if the complex components don't provide a unique topological advantage for the specific data manifold.
- Why this is not generic: It leverages the 'Rate Tightener' worldview that constants (like the cost of complex arithmetic) can be improved by targeting local spectral convergence conditions.
- Confidence: medium
- Required next search: Search for 'eigenvalue-based gating in linear recurrences' or 'complex vs real state space model performance trade-offs'.


## Proposal Seed: SpectralGuard Layer for Adaptive Lyapunov Re-normalization

- Status: promising
- Originating taste: Proof-Technique Transplanter
- Seed-paper hook: Gu & Dao (2023) Mamba. LrcSSM (2025) and SpectralGuard (2026) have identified that input-dependent linear recurrences lack formal stability and are vulnerable to 'memory collapse'.
- Evidence trigger: Finding: Stability Gap in Input-Dependent Sub-Quadratic Models. Evidence from 2026 (SpectralGuard) proves an 'Evasion Existence Theorem' where adaptive attacks can drive the spectral radius of the transition matrix toward zero, erasing memory.
- Candidate novelty: Integrating a differentiable Lyapunov-check layer into the Selective State Space (SSM) block that performs real-time re-normalization of the transition operator whenever the spectral radius deviates from a target convergence manifold.
- Technical mechanism: Traditional SSMs initialize A with stable eigenvalues (e.g., HiPPO), but Mamba's input-dependent delta parameter can scale A in ways that violate stability. I propose an 'Adaptive Lyapunov Projection' where the model learns a state-dependent Lyapunov function $V(x)$ and applies a projection derived from the Small-Gain Theorem to the discretization step, ensuring the state-to-state mapping remains a contraction (spectral radius < 1) regardless of input perturbation.
- Closest prior-work collision: LrcSSM (2025) uses a diagonal Jacobian for global stability; this proposal is more general, allowing non-diagonal interactions as long as the Lyapunov constraint is met.
- Closest future-work collision: SpectralGuard (2026) detects but does not necessarily remediate the collapse through a differentiable learning signal; it is a monitor, not a training-time regularizer.
- Minimum validation: Robustness benchmark against the 'Spectral Poisoning' attack described in Bonetto (2026) compared to vanilla Mamba and LrcSSM.
- Falsification risk: The computational overhead of computing even a partial spectral radius or Lyapunov update per token might negate the O(N) scaling speed advantage.
- Why this is not generic: It bridges the gap between passive detection (SpectralGuard) and restrictive architecture (LrcSSM) by proposing an adaptive, differentiable control-theory regularizer.
- Confidence: medium
- Required next search: Search for 'differentiable spectral radius approximation' and 'projected gradient descent on Lyapunov manifolds'.
