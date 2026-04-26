# Findings



## Finding: High Attention Head Redundancy

- Claim: Individual attention head ablation in large models (like GPT-2) often produces minimal or negligible changes in perplexity.
- Confidence: medium
- Evidence:
  - `f849c3fff907b8bc8dbeedb5cae178916853d5ff` (2025): "Why large language models cannot possess consciousness..."
- Why it matters: This suggests that the massive parameter counts in current Transformer architectures may be significantly over-parameterized, and many components might be redundant rather than essential for linguistic competence. This opens up paths for aggressive architectural pruning or more efficient, sparse designs.
- Caveat: The effect might depend heavily on the specific task, the scale of the model, or the method of ablation (e.g., zeroing vs. removing).
