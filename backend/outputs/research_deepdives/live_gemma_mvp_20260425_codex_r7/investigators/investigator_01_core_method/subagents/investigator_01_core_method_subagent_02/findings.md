# Findings



## Finding: Attention-as-explanation skepticism

- Claim: Attention weights in Transformer architectures are not necessarily faithful explanations of model decisions.
- Confidence: high
- Evidence:
  - Paper ChQ_Pm3AqM4J (Attention is not explanation, 2019)
- Why it matters: This creates a fundamental tension in the Transformer paradigm: while the attention mechanism is explicitly modeled and 'visible', its weights may not represent the true causal drivers of the model's output, complicating mechanistic interpretability.
- Caveat: The faithfulness of attention may depend on specific architectural configurations or the presence of other explanatory mechanisms (e.g., residual connections).


## Finding: Causal mediation as a tool for mechanistic interpretability

- Claim: Causal mediation analysis is a viable and active methodology for identifying functional components (such as specific attention heads and MLP modules) within Transformer architectures.
- Confidence: high
- Evidence:
  - Paper 5dc15ac1c92ab7492f121471823fb13a95d273ba (Stolfo et al., 2023)
- Why it matters: This validates the use of causal intervention as a research direction, but also defines the 'novelty boundary': researchers have moved from component identification to needing more granular, weight-level faithfulness metrics.
- Caveat: Existing work is often highly task-specific (e.g., arithmetic reasoning) and may not generalize to a universal interpretability benchmark.
