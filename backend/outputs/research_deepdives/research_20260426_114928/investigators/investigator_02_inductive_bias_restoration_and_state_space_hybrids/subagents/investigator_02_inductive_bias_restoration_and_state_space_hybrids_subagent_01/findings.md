# Findings



## Finding: HiPPO as Orthogonal Basis Projection

## Finding: HiPPO as Orthogonal Basis Projection

- Claim: The HiPPO framework (and by extension S4) functions by projecting input sequences onto a subspace of orthogonal polynomials, specifically exponentially-warped Legendre polynomials.
- Confidence: high
- Evidence:
  - a30ac45ac5b7bd2148d3fb80ee7f3c29724e3170 (How to Train Your HiPPO, 2022)
  - 9df724e66fe2878c32269e4dbd2e5ca43b8548f3 (UnHiPPO, 2025)
- Why it matters: This bridge to classical orthogonal polynomial theory explains the 'memory' of SSMs and provides a deterministic mechanism for long-range dependency modeling that Transformers lack. It also identifies a gap: HiPPO assumes noise-free data.
- Caveat: Theoretical interpretations sometimes lag behind the empirical performance of simplified diagonal variants (DSS) that may discard the strict orthogonal structure.


## Finding: H-infinity Filters for Worst-Case Divergence

## Finding: H-infinity Filters for Worst-Case Divergence

- Claim: H-infinity filters provide minimax optimality, minimizing the maximum error relative to bounded but unknown noise, making them more robust than Kalman Filters for non-Gaussian/adversarial perturbations.
- Confidence: high
- Evidence:
  - 3397214bb4847acd5f82635a5261fe6feba5c898 (Kiriakidis & O\'Brien, 2004)
  - d5ce06b0a4e0bd1f4dfa75f744665d46f233f75d (Rigatos et al., 2019)
- Why it matters: In the context of deep SSMs like Mamba, the standard recurrence assumes a specific error model. H-infinity formulations allow for formal 'robustness guarantees' against distribution shift and distracting tokens, but they have not yet been integrated into the 'associative scan' hardware acceleration framework used by modern SOTA models.
- Caveat: The stability of the Riccati-like update in H-infinity estimation depends on a performance bound parameter \gamma; if \gamma is too small, the estimator may diverge, complicating end-to-end training.
