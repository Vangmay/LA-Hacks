# Findings



## Finding: Fundamental Limitation in Function Composition

- Claim: Transformers are theoretically incapable of composing functions when the domains are sufficiently large.
- Confidence: medium
- Evidence:
  - bbe0e4cc9b052e960362fdc18b6805043b81ca6b (On Limitations of the Transformer Architecture, 2024)
- Why it matters: This provides a theoretical explanation for why LLMs struggle with complex reasoning and compositional tasks, suggesting that current architectures may hit a ceiling that simply scaling parameters cannot solve.
- Caveat: The proof uses Communication Complexity and relies on certain unproven computational complexity conjectures.


## Finding: CoT Prompting Insufficiency for Compositional Scaling

- Claim: Chain-of-Thought (CoT) prompting does not allow SSMs to efficiently perform function composition over large domains, as the required number of steps scales unfavorably with complexity.
- Confidence: medium
- Evidence:
  - e640c1ba69f268a7a1eaa19552dbbc78cdc4cc9f (Limits of Deep Learning: Sequence Modeling through the Lens of Complexity Theory, 2024)
- Why it matters: This suggests that 'prompt engineering' or 'reasoning steps' are not enough to overcome fundamental architectural scaling limits. It reinforces the need for structural/architectural changes rather than just algorithmic/prompting ones.
- Caveat: The finding is specifically framed within the context of SSMs, though the paper links this to broader sequence modeling constraints.
