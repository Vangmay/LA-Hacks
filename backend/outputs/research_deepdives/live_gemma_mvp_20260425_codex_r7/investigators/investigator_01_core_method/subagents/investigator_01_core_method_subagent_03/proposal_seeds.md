# Proposal Seeds



## Proposal Seed: Mitigating Transformer Exposure Bias via Reinforcement Learning

- Status: raw
- Originating taste: gap_synthesizer
- Seed-paper hook: Vaswani et al. (2017) Transformer architecture.
- Evidence trigger: 032274e57f7d8b456bd255fe76b909b2c1d7458e (A Deep Reinforced Model for Abstractive Summarization) identifying exposure bias in seq2seq.
- Candidate novelty: Applying RL-based optimization directly to the Transformer's autoregressive decoding to bridge the gap between teacher-forcing training and autonomous inference, specifically optimizing for sequence-level metrics (like ROUGE) rather than token-level cross-entropy.
- Technical mechanism: Policy gradient-based fine-tuning of the Transformer decoder where the reward is derived from sequence-level quality scores.
- Closest prior-work collision: Scheduled sampling (Bengio et al.) or standard RLHF (Reinforcement Learning from Human Feedback) in LLMs.
- Closest future-work collision: Direct preference optimization (DPO).
- Minimum validation: Train a small Transformer on a summarization task using both standard Teacher Forcing and the proposed RL-based method; compare performance on held-out data using sequence-level metrics.
- Falsification risk: The complexity and instability of RL might outweigh the gains in BLEU/ROUGE, or the Transformer might already be robust enough due to its capacity.
- Why this is not generic: It targets a specific, documented failure mode (exposure bias) in the lineage of seq2seq models that the Transformer's architecture (but not necessarily its training paradigm) inherits.
- Confidence: low
- Required next search: 'transformer exposure bias reinforcement learning', 'RL fine-tuning transformer decoding', 'scheduled sampling transformer'


## Proposal Seed: Constrained Policy Optimization for Balanced Error Recovery in Transformers

- Status: promising
- Originating taste: gap_synthesizer
- Seed-paper hook: Vaswani et al. (2017) Transformer architecture.
- Evidence trigger: The documented tension between error recovery and ground-truth fidelity (the 'over-correction' problem) identified in 2ef10559f59f3877ff7b3babfcc12972ceee842e.
- Candidate novelty: Unlike standard RLHF/DPO which focuses on preference alignment, this proposal specifically targets the exposure bias/recovery trade-off by using a constrained optimization framework (e.g., Lagrangian-constrained policy gradient). It aims to maximize sequence-level quality (reward) *subject to* a constraint that prevents the model from deviating too far from the ground-truth distribution (fidelity).
- Technical mechanism: A dual-objective optimization or a KL-regularized policy gradient where the regularization term is specifically tuned to penalize 'unnatural' error recovery paths that lead to semantic drift, effectively bridging the gap between MLE and sequence-level RL.
- Closest prior-work collision: Contrastive preference learning (2ef10559...) and DPO-based NMT (6c6d2a...).
- Closest future-work collision: Advanced RLHF methods that incorporate explicit semantic constraints.
- Minimum validation: Compare a vanilla RL-tuned Transformer against the 'Constrained RL' version on NMT and Summarization tasks. Measure both reward (e.g., ROUGE/BLEU) and a 'Fidelity Score' (e.g., semantic similarity to ground truth via BERTScore) to demonstrate that the constraint prevents over-correction without sacrificing recovery.
- Falsification risk: The constraint might be too restrictive, preventing the model from learning effective recovery, or the added complexity of the Lagrangian formulation might not yield measurable gains over simple KL-regularized DPO.
- Why this is not generic: It moves beyond 'improving performance with RL' to 'solving the specific failure mode of over-correction in exposure bias mitigation' using a formal optimization constraint.
- Confidence: medium
- Required next search: 'Lagrangian constrained reinforcement learning sequence generation', 'constrained policy optimization for language models', 'balancing error recovery and fidelity in NMT'
