# Findings



## Finding: Exposure Bias in RNN-based Seq2Seq

- Claim: RNN-based encoder-decoder models often suffer from 'exposure bias' during training, where they assume ground truth is provided at each step, leading to incoherent sequences when generating autonomously.
- Confidence: high
- Evidence:
  - 032274e57f7d8b456bd255fe76b909b2c1d7458e (A Deep Reinforced Model for Abstractive Summarization, 2017)
- Why it matters: This highlights a critical failure mode in the architectures that the Transformer sought to replace/improve, specifically regarding how models handle sequence generation and training-inference discrepancy.
- Caveat: The paper suggests RL as a mitigation, but the Transformer's architectural shift also fundamentally changed how dependencies are modeled.


## Finding: Contrastive Learning as an Alternative to RL for Exposure Bias

- Claim: Token-level contrastive learning can coordinate MLE, error recovery, and ground-truth preservation objectives, offering an alternative to reinforcement learning (RL) for mitigating exposure bias in NMT.
- Confidence: high
- Evidence:
  - 2ef10559f59f3877ff7b3babfcc12972ceee842e (Recovery Should Never Deviate from Ground Truth, 2024)
- Why it matters: This provides a direct technical collision for the proposed RL-based seed. While the seed proposes RL to optimize for sequence-level metrics, this paper suggests a contrastive learning approach to manage the trade-off between error recovery and ground-truth deviation at the token level.
- Caveat: The contrastive approach might still suffer from the same sampling efficiency issues as RL, or it might not capture the same long-range sequence-level dependencies that RL-based optimization (on ROUGE/BLEU) targets.


## Finding: The 'Over-Correction' Problem in Exposure Bias Mitigation

- Claim: Current methods for mitigating exposure bias (like scheduled sampling or certain RL objectives) can cause models to 'over-correct' or deviate too far from the ground truth, potentially sacrificing semantic fidelity for the sake of error recovery.
- Confidence: medium
- Evidence:
  - 2ef10559f59f3877ff7b3babfcc12972ceee842e (Recovery Should Never Deviate from Ground Truth, 2024) notes that token-level solutions like scheduled sampling can lead to a sequence with errors having a larger probability than the ground truth.
- Why it matters: This identifies a fundamental tension in exposure bias research: the trade-off between the model's ability to recover from errors (robustness) and its ability to stay faithful to the target sequence (accuracy). This tension is a primary candidate for a novelty-driven research direction (e.g., a constrained RL objective).
- Caveat: The exact mechanism of 'over-correction' varies across architectures (e.g., NMT vs. Diffusion), and the severity is task-dependent.


## Finding: L1 Policy Regularization for Exposure Bias

- Claim: L1 policy regularization can be used as a specific mechanism to mitigate exposure bias in sequence generation.
- Confidence: medium
- Evidence:
  - b44467340afca73b9adabf601398769518802d54 (RegRL-KG, 2023)
- Why it matters: This provides a specific, existing regularization-based alternative to the proposed Lagrangian-constrained approach. While L1 regularization targets the policy directly, the proposed Lagrangian approach targets a constraint on the fidelity (divergence from ground truth), potentially offering more fine-grained control over the 'over-correction' problem.
- Caveat: The 2023 paper focuses on keyphrase generation, so its effectiveness in high-entropy tasks like NMT or summarization is unproven.
