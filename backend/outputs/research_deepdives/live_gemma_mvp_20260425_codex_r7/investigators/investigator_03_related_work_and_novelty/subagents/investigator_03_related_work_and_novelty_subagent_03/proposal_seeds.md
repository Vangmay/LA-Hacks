# Proposal Seeds



## Proposal Seed: Bridging the Computability-Learnability Gap in Transformer-based Symbolic Reasoning

- Status: promising
- Originating taste: Research-Gap Miner
- Seed-paper hook: Smolensky et al. (2024) demonstrates that Transformers can be compiled to execute symbolic programs (PSL), proving computability, but leaves the learnability of these programs via standard training/ICL underexplored.
- Evidence trigger: The identified gap between architectural capacity (computability) and optimization success (learnability) in symbolic tasks.
- Candidate novelty: Shifting focus from 'is it possible?' to 'what makes it learnable?' by quantifying the difficulty of learning different classes of symbolic programs.
- Technical mechanism: A systematic benchmark of symbolic programs (using PSL) categorized by complexity metrics (e.g., recursion depth, branching factor, variable dependency) to analyze the relationship between program structure and the Transformer's gradient signal or ICL success rate.
- Closest prior-work collision: Existing work on the 'learning algorithm' of ICL.
- Closest future-work collision: Future research into specialized symbolic-neural architectures.
- Minimum validation: Correlate program complexity metrics with the number of in-context examples required for successful execution.
- Falsification risk: If the learning difficulty is decoupled from program complexity, the proposed complexity-based categorization may fail.
- Why this is not generic: It directly addresses the specific 'computability vs. learnability' distinction raised by recent literature.
- Confidence: medium
- Required next search: 'Transformer learning dynamics symbolic reasoning' or 'difficulty of learning symbolic programs with neural networks'


## Proposal Seed: Mitigating Post-Hoc Rationalization via Multi-Stage Consistency Rewards

- Status: promising
- Originating taste: Research-Gap Miner
- Seed-paper hook: Wang et al. (2026) demonstrates that unfaithfulness is an emergent property of autoregressive training; Xu et al. (2025) and Sun et al. (2025) show that fine-grained/multi-dimensional rewards (VERITAS, ReFIne) can mitigate this in specialized settings (RAG, trustworthiness).
- Evidence trigger: The contradiction between optimizing for outcome-based rewards (which can incentivize post-hoc rationalization) and the need for process-based faithfulness.
- Candidate novelty: Shifting from task-specific faithfulness (e.g., RAG-based or structured-trace based) to a generalized training objective that specifically targets the 'unfaithfulness gap' during the transient training phases identified by Pengmei et al. (2025).
- Technical mechanism: A reinforcement learning framework (e.g., using GRPO) where the reward function $R$ is a composite of $R_{outcome}$ (verifiable correctness) and $R_{consistency}$ (an 'internal-external' alignment score). $R_{consistency}$ would be calculated by measuring the causal dependency of the final answer on specific intermediate CoT steps (using intervention-based methods like Lanham et al., 2023) or by checking the logical entailment between steps (using a symbolic verifier).
- Closest prior-work collision: VERITAS (Xu et al., 2025) for RAG; ReFIne (Sun et al., 2025) for general trustworthiness.
- Closest future-work collision: Future work on 'process-supervised reward models' (PRMs).
- Minimum validation: Training a small transformer on modular arithmetic tasks (as in Wang et al., 2026) and demonstrating that a multi-stage consistency reward reduces the 'transient unfaithfulness phase' observed in standard training.
- Falsification risk: If the consistency reward is too sparse or if it creates a conflict with the outcome reward that prevents the model from reaching high accuracy.
- Why this is not generic: It specifically targets the *emergence* of unfaithfulness during the training process, rather than just evaluating it post-hoc.
- Confidence: medium
- Required next search: 'causal intervention for reward modeling' or 'training transformers with process-based consistency rewards'
