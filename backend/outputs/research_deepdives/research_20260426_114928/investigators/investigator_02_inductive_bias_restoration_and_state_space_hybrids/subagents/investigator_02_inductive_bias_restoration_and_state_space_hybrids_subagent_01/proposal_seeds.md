# Proposal Seeds



## Proposal Seed: Differentiable Kalman-Mamba (DK-Mamba)

- Status: promising
- Originating taste: historical_synonym_mapper
- Seed-paper hook: Mamba / UnHiPPO (2025)
- Evidence trigger: UnHiPPO (9df724e66...) identifies that the HiPPO framework assumes noise-free data, which is violated in real-world sequences. They propose uncertainty-aware initialization but not a full online stochastic filter.
- Candidate novelty: Restoring the 'optimal estimator' property of classical Kalman Filters as a differentiable layer within the Mamba/SSM architecture to handle non-stationary noise and adversarial sequence perturbations.
- Technical mechanism: Replace the deterministic SSM recurrence with a differentiable Kalman update. Predict noise covariances Q (process noise) and R (measurement noise) using a small MLP or data-dependent selection mechanism (similar to Mamba's B and C matrices), allowing the model to dynamically adjust the Kalman Gain based on local sequence volatility.
- Closest prior-work collision: UnHiPPO (2025) which focuses on initialization; older 'Deep Kalman Filters' (e.g., Krishnan et al., 2015) which do not scale to the long-range scan efficiency of modern SSMs.
- Closest future-work collision: Stochastic SSMs in the SDE/ODE framework.
- Minimum validation: Performance on Long Range Arena (LRA) under varying noise-to-signal ratios compared to vanilla Mamba and S4.
- Falsification risk: The Kalman Gain calculation involves a matrix inversion or specialized linear solve that could break the hardware-aware prefix-sum (associative scan) optimization of Mamba.
- Why this is not generic: It bridges the gap between 'hardware-aware efficiency' and 'stochastic optimality' by re-deriving the Kalman update to be compatible with associative scans.
- Confidence: medium
- Required next search: Search for 'Associative Scan Kalman Filter' or 'Differentiable Kalman Filter hardware acceleration'.


## Proposal Seed: H-infinity Robust Mamba (HR-Mamba)

- Status: promising
- Originating taste: historical_synonym_mapper
- Seed-paper hook: Luis et al. (2024) / Mamba
- Evidence trigger: Luis et al. (2024) successfully mapped the Kalman Filter (L2-optimality) to an associative scan. However, Kalman Filters are sensitive to model mismatch and non-Gaussian outliers. In control theory, H-infinity filters (Minimax optimality) are the standard 'restoration' of robustness for worst-case perturbations.
- Candidate novelty: Integrating H-infinity 'Minimax' robust estimation into the Mamba associative scan to handle catastrophic sequence distractions and 'out-of-distribution' tokens.
- Technical mechanism: Derive an associative operator for the H-infinity filter update. Unlike the Kalman Filter which minimizes expected error (L2), the H-infinity filter minimizes the maximum error (L-infinity) relative to bounded noise. This involves a modified Riccati update with a performance bound parameter \gamma. I propose making \gamma a data-dependent learnable parameter, allowing Mamba to switch between 'trusting' (Kalman-like) and 'skeptical' (H-infinity-like) modes based on input saliency.
- Closest prior-work collision: Luis et al. (2024) for the Kalman associative scan; standard H-infinity control theory textbooks.
- Closest future-work collision: Robust Control-based Deep Learning papers (often too slow for LLMs).
- Minimum validation: Adversarial token prompt robustness in LLMs; performance on salt-and-pepper noise corrupted text benchmarks.
- Falsification risk: The H-infinity Riccati equation has stricter stability conditions (positivity of certain matrices) that might be difficult to satisfy during gradient descent.
- Why this is not generic: It moves beyond 'uncertainty as variance' (Kalman) to 'robustness as game-theoretic worst-case defense' (H-infinity), a classic control theory bridge currently absent from modern SSMs.
- Confidence: medium-high
- Required next search: Search for 'Associative Scan H-infinity Filter' and 'Differentiable H-infinity Filter'.
