# Proposal Seeds



## Proposal Seed: Domain-Specific Structural Stress-Testing Framework for Safety-Critical Transformers

- Status: promising
- Originating taste: Benchmark-Reproducibility Skeptic
- Seed-paper hook: "In Transformer We Trust?" (2026) highlights that structural vulnerabilities in Transformers pose risks in high-stakes domains like medicine and robotics.
- Evidence trigger: The review paper identifies a gap between general performance and domain-specific reliability/trustworthiness.
- Candidate novelty: Moves beyond generic adversarial robustness (e.g., FGSM) to create a diagnostic framework that specifically tests how architectural components (like self-attention mechanisms) respond to domain-specific, non-adversarial noise models (e.g., sensor jitter in robotics, physiological artifacts in EEG).
- Technical mechanism: A diagnostic metric measuring the 'Attention Stability Score'—the variance of attention weights under controlled domain-specific perturbations—correlated with task-specific error rates.
- Closest prior-work collision: Generic adversarial robustness studies for Transformers; standard ablation studies.
- Closest future-work collision: New 'safe-by-design' architectures that might bake in these robustness checks.
- Minimum validation: Apply the framework to the MultiScaleSleepNet (2025) architecture using the Sleep-EDF dataset, introducing synthetic EEG artifacts and measuring the decay of attention stability vs. classification accuracy.
- Falsification risk: If attention maps remain stable while performance drops, the vulnerability is likely located in the feed-forward networks or positional embeddings rather than the attention mechanism itself.
- Why this is not generic: It targets the specific interaction between architectural structure (attention) and domain-specific signal characteristics (e.g., temporal spectral features in EEG).
- Confidence: medium
- Required next search: "Transformer attention stability physiological noise", "robustness of Transformers in medical signal processing", "adversarial attacks on EEG transformers".
