# Proposal Seeds

## Proposal Seed: Selective Learning Rate Schedules for Inductive Bias Restoration
- Status: raw
- Seed-paper hook: The discovery that learning rate (LR) choice is critical for Associative Recall (AR) performance in modern SSMs, unlike Transformers (Okpekpe & Orvieto, 2025).
- Evidence trigger: Okpekpe & Orvieto (2025) demonstrate that SSMs have a fragile optimization landscape where standard global LR fails to activate the 'induction-head-like' behavior needed for AR.
- Candidate novelty: Rather than adding physical attention layers, restore inductive bias via an optimization hybrid: a parameter-group-specific LR schedule that scales the selective parameters (B, C, and Delta) differently based on training-time gradient variance.
- Technical mechanism: Implement a 'SelecLR' (Selective Learning Rate) callback that monitors the SNR (Signal-to-Noise Ratio) of the selectivity matrices. If SNR is low (indicating a failure to latch onto associative patterns), the LR for those specific SSM parameters is boosted relative to the mixer layers.
- Closest prior-work collision: Standard Mamba/S4 models use a single global LR or simple linear warm-up. No major work explicitly modulates LR specifically to solve the AR bottleneck discovered in 2024/2025.
- Minimum validation: Synthetic AR benchmark (string length 128-512) comparing baseline Mamba-2 with a 'SelecLR' version under varying LR conditions.
- Falsification risk: If the AR failure is due to state-size capacity (memory) rather than optimization, then LR modulation will show no improvement.
- Why this is not generic: It moves away from the 'Universal Optimizer' assumption and targets the specific mechanistic failure of SSM selectivity identified in the 2025 'Shattering' and 'Optimization Friction' literature.
- Confidence: medium
- Required next search: 'Mamba optimization landscape', 'adaptive layer-wise learning rates for state-space models'.


## Proposal Seed: Gated Gradient-Informed Local Attention Restoration

- Status: raw
- Seed-paper hook: The empirical necessity of re-introducing local attention to linear recurrences to achieve extrapolation (De et al., 2024; Griffin).
- Evidence trigger: Finding #1 (Optimization Friction) and Finding #2 (Attention as a Bandage). Griffin shows local attention is a 'patch' for recurrence failures, while Okpekpe shows these failures might be optimization-linked.
- Candidate novelty: A 'Soft-Hybrid' that does not use static local attention blocks, but instead uses a 'Gradient-Informed Local Attention' layer that only activates when the underlying SSM recurrence is failing to minimize local cross-entropy loss.
- Technical mechanism: A gating mechanism based on a 'Surprise Meter' (local prediction error). If the error exceeds a threshold at specific token positions, a small-window (local) attention module is gated-in to 'resolve' the local context, while the SSM handles long-range state. This reduces the FLOP count of static hybrids like Griffin by only applying attention where the 'recurrence bottleneck' is mathematically present.
- Closest prior-work collision: Griffin (static hybrid), Jamba (global hybrid). These models use fixed attention/SSM ratios regardless of sequence complexity.
- Minimum validation: Test on the 'SharedContextBench' or synthetic AR tasks. Compare a static Griffin model against a 'Dynamic Gated Griffin' where the attention heads are sparsely activated based on the SSM prediction confidence.
- Falsification risk: If the bottleneck is not local (e.g., global recall failure), then local attention gating won't help.
- Why this is not generic: It proposes a dynamic, error-driven hybrid rather than a fixed architectural sandwich, directly addressing the 'bandage' nature of current hybrids.
- Confidence: medium
- Required next search: 'Dynamic attention gating in hybrid models', 'uncertainty-aware activation in state-space models'.
