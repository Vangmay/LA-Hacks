# Hand-Off: Inductive Bias Restoration and State-Space Hybrids

## Research Summary
This deep dive investigated the technical frictions and documented failures that occur when replacing pure attention with State-Space Models (SSMs) or modern linear recurrences like Mamba. The research indicates that while SSMs have the *capacity* to match Transformers, they suffer from significant **optimization friction** (sensitivity to LR and scaling) and a **coverage-vs-selection gap** (adept at generating candidate reasoning paths but weak at final top-1 selection).

## Key Findings
- **Optimization Friction is the Primary Bottleneck**: 2024-2025 research (Okpekpe & Orvieto) suggests Associative Recall (AR) failures are often optimization artifacts. SSMs require specific LR regimes and depth/width ratios to activate 'induction-head-like' behaviors that Transformers exhibit robustly.
- **The 'Attention Bandage' Current State-of-the-Art**: High-profile hybrids like Griffin and Jamba re-introduce local/global attention as a 'bandage' for recurrence-specific extrapolation and precision failures (De et al., 2024).
- **Representation Shattering**: Both architectures suffer from 'representation shattering' during knowledge editing, but SSMs show distinct sensitivity to structured knowledge perturbations (Nishi et al., 2024).
- **Coverage vs. Selection Disconnect**: Mamba-2 hybrids improve candidate coverage (pass@k) but struggle with top-1 selection (pass@1), indicating a missing 'ranking' inductive bias in linear state representations.

## Top Papers
- **[Okpekpe & Orvieto, 2025]** *Revisiting associative recall in modern recurrent models*: Proves LR and scaling are critical for SSM inductive bias activation.
- **[De et al., 2024]** *Griffin*: Establishes the empirical necessity of local attention for extrapolation.
- **[Wang & Reid, 2026]** *Tiny Recursive Reasoning with Mamba-2*: Documents the coverage-vs-selection gap in hybrid reasoning operators.

## Proposal Seeds
- **Selective Learning Rate Schedules (SelecLR)**: Restore inductive bias via parameter-group-specific LR schedules that scale selectivity matrices (B, C, Delta) based on training-time gradient SNR.
- **Gated Gradient-Informed Local Attention**: A 'Soft-Hybrid' where local attention blocks only activate when the underlying SSM unit triggers a high 'prediction surprise' signal or local entropy spike.

## Recommended Next Steps
1. Search Boundary: Deep dive into the 'Signal-to-Noise Ratio (SNR) of Mamba Gradients' during the first 1k steps of training on AR tasks.
2. Adversarial Challenge: Investigate if the 'coverage' advantage of Mamba-2 holds at 1B+ parameter scales or if it collapses under standard training regimes.