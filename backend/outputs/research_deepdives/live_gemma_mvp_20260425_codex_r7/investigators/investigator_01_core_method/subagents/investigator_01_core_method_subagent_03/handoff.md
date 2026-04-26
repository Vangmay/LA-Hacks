# Hand-Off

## Research Summary
I have conducted a literature deep dive centered on the 'Attention is All You Need' architecture, specifically investigating the phenomenon of **exposure bias** and its modern mitigations. The research moved from understanding the ancestral RNN-based failures to evaluating the current state-of-the-art in Transformers, including Reinforcement Learning (RL), Direct Preference Optimization (DPO), and Contrastive Learning approaches.

## Buckets Filled
- `seed_metadata`: Completed.
- `foundational_references`: Identified key early work on exposure bias in seq2seq.
- `closest_prior_work`: Mapped technical collisions in scheduled sampling and early RL-based seq2seq.
- `recent_followups`: Extensive coverage of 2023-2024 works in DPO, Contrastive Preference Learning, and off-policy RL.
- `research_gaps`: Identified the 'over-correction' problem (the tension between error recovery and ground-truth fidelity).
- `spinoff_novelty_proposals`: Generated a refined proposal seed for constrained policy optimization.

## Top Papers & Why They Matter
- **Vaswani et al. (2017)**: The seed paper; establishes the Transformer architecture.
- **He et al. (2024) [Contrastive Preference Learning]**: A major collision; shows how contrastive learning can align models with sequence-level preferences.
- **Yang et al. (2023) [DPO for NMT]**: A major collision; demonstrates how DPO can emulate MBR decoding for NMT.
- **Yan et al. (2020) [Off-Policy Self-Critical Training]**: A technical collision; provides a solution to the sampling cost issue in Transformer-RL training.
- **He et al. (2024) [Recovery vs. Deviation]**: The key evidence for the identified gap; highlights how error recovery can lead to undesirable deviations from ground truth.

## Strongest Novelty/Gap Implications
The most promising research direction lies in the **tension between error recovery and semantic fidelity**. While current methods (RL, DPO, Contrastive Learning) attempt to solve exposure bias, they often encounter an 'over-correction' problem where the model becomes too aggressive in its recovery, leading to semantic drift. There is a clear opening for a **formal constrained optimization framework** (e.g., Lagrangian-constrained policy gradients) that explicitly treats fidelity to the ground-truth distribution as a constraint while maximizing sequence-level quality as the objective.

## Proposal Seeds
### Proposal Seed: Constrained Policy Optimization for Balanced Error Recovery in Transformers
- **Core Idea**: Use a Lagrangian-constrained optimization approach to maximize sequence-level rewards (like ROUGE/BLEU) subject to a constraint on the KL-divergence (or semantic similarity) relative to the ground-truth distribution.
- **Evidence Basis**: The 'over-correction' problem documented in 2024 NMT literature.
- **Mechanism**: Lagrangian-constrained policy gradient.
- **Confidence**: Medium.
- **Collision Risk**: DPO and Contrastive Preference Learning (must differentiate through the explicit constraint vs. implicit preference modeling).

## Contradictions & Uncertainties
- **RL vs. DPO**: It is unclear if the explicit modeling of a reward function (RL) provides better error-recovery control than the implicit preference modeling of DPO, specifically regarding the fidelity-recovery trade-off.
- **Implementation Complexity**: The computational cost of sampling for RL remains a barrier, even with off-policy mitigations.

## Recommended Next Steps
1. **Adversarial Mechanism Search**: Perform an exact phrase search for 'Lagrangian constrained policy optimization' and 'constrained reinforcement learning' in the context of 'language modeling' or 'sequence generation' to ensure this specific mathematical formulation hasn't been applied to this gap.
2. **Feasibility Study**: Develop a toy Transformer model to test if a simple KL-penalty (as a proxy for the constraint) effectively mitigates the 'over-recovery' observed in standard RL-tuned models.
