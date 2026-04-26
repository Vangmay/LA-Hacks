# Hand-Off

## Summary
I have completed a deep dive into the 'Attention is All You Need' literature through the lens of the 'Friction Detector' taste. I focused on the contradiction between the Transformer's reliance on the highly visible attention mechanism and the academic critique that these weights are not faithful explanations of model behavior.

## Search Activity
- **Critique Search**: Used Google Scholar to find limitations of the Transformer/Attention mechanism. Found 'Attention is not explanation' (Jain & Wallace, 2019).
- **Collision Search**: Used Semantic Scholar relevance search to check if 'causal mediation analysis' for attention faithfulness was already a settled topic. Found Stolfo et al. (2023) which uses the technique for component identification but not for faithfulness benchmarking.

## Key Papers
- **Vaswani et al. (2017)**: The seed architecture.
- **Jain & Wallace (2019)**: The core critique regarding interpretability.
- **Stolfo et al. (2023)**: Established causal mediation as a tool for mechanistic interpretability in Transformers, serving as the closest prior-work collision.

## Findings
- **Attention-as-explanation skepticism**: High confidence that attention weights are not inherently faithful to model decision-making.
- **Causal mediation utility**: High confidence that causal intervention is a valid way to probe Transformer internals, though currently applied at the component level rather than the weight level.

## Proposal Seeds

### Proposal Seed: Quantifying Attention Faithfulness via Causal Intervention
- **Core Idea**: Create a standardized metric (Faithfulness Score) that measures the correlation between attention weight magnitudes and the causal effect of intervening on those specific weights.
- **Evidence Basis**: The conflict between the visibility of attention and the 'Attention is not explanation' critique.
- **Novelty**: Moves from qualitative skepticism to quantitative benchmarking, and from component identification to weight-level faithfulness.
- **Confidence**: Medium (requires specific validation of weight-patching vs. activation-patching efficacy).

## Recommendations for Investigator
1. **Collision Check**: Verify if any recent (2024-2025) work has introduced a 'faithfulness benchmark' for attention weights specifically.
2. **Technical Feasibility**: Test if intervening on individual attention weights (via weight patching) is stable enough to produce a measurable signal compared to the much stronger signal of activation patching.
3. **Expansion**: Consider how this faithfulness metric could be applied to other visible mechanisms, like MLP-based 'memory' tokens or sparse autoencoder features.