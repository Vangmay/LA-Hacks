# Findings



## Finding: Computability vs. Learnability Gap in Symbol Processing

- Claim: There is a potential disconnect between the symbolic computability of transformer architectures and their ability to learn such symbolic programs.
- Confidence: medium
- Evidence:
  - 0e703833cf10099e0d825b3490a6956c88e00d73 (Mechanisms of Symbol Processing for In-Context Learning in Transformer Networks, 2024)
- Why it matters: Understanding whether the bottleneck in symbolic reasoning is the architecture's capacity to represent rules (computability) or the training process's ability to recover them (learnability) is critical for the next generation of reasoning models.
- Caveat: The source paper explicitly notes that its investigation focuses on computability rather than learnability.


## Finding: Algorithmic Complexity as a Barrier to CoT Generalization

- Claim: Chain-of-Thought (CoT) supervision accelerates the learning and generalization of symbolic reasoning in Transformers, but it does not enable the model to overcome tasks that exceed a certain threshold of algorithmic complexity.
- Confidence: high
- Evidence:
  - 58549bbb5bffab9c286694963639586c5388313f (The Kinetics of Reasoning: How Chain-of-Thought Shapes Learning in Transformers?, 2025)
- Why it matters: This identifies a hard boundary for current reasoning enhancement techniques. If CoT cannot solve high-complexity tasks, we need a different mechanism (perhaps architecture-based or hybrid) rather than just better supervision.
- Caveat: The study uses specific symbolic reasoning tasks and 'grokking' as a lens, which may not generalize to all reasoning domains.


## Finding: Emergence of Unfaithfulness from Autoregressive Training

- Claim: Unfaithful reasoning patterns (where intermediate steps are logically inconsistent with the final answer) can emerge naturally during the autoregressive training process.
- Confidence: high
- Evidence:
  - 60bf56ed72d032600f01161fd40769273bef84a8 (How Does Unfaithful Reasoning Emerge from Autoregressive Training? A Study of Synthetic Experiments, 2026)
- Why it matters: This suggests unfaithfulness is not just a prompting issue but a fundamental side-effect of how transformers are trained to optimize for next-token prediction on noisy or complex data. It points toward a need for training-time objectives that explicitly penalize unfaithfulness.
- Caveat: The evidence is currently based on small-scale synthetic experiments involving modular arithmetic.
