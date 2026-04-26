# Proposal Seeds



## Proposal Seed: Quantifying Attention Faithfulness via Causal Intervention

- Status: promising
- Originating taste: friction_detector
- Seed-paper hook: The tension between the Transformer's explicit attention mechanism (Vaswani et al., 2017) and the claim that attention weights are not faithful explanations (Jain & Wallace, 2019).
- Evidence trigger: The contradiction between the visibility of attention weights and their potential lack of causal connection to model outputs.
- Candidate novelty: Proposes a formal metric/benchmark to quantify the 'faithfulness gap' by measuring the divergence between attention weight magnitudes and the causal effect of intervening on those weights.
- Technical mechanism: Use causal mediation analysis to intervene on specific attention heads/weights and measure the change in logit output. Define a 'Faithfulness Score' as the alignment (e.g., Spearman correlation) between attention weight magnitude and the resulting causal effect.
- Closest prior-work collision: Existing mechanistic interpretability work (e.g., Elhage et al., 2021) that studies head functions, but lacks a standardized 'faithfulness' metric.
- Closest future-work collision: Research into 'interpretable-by-design' attention mechanisms.
- Minimum validation: Implement the scoring framework on a small-scale Transformer (e.g., GPT-2 small) using a controlled task (e.g., sentiment classification) and evaluate correlation across different layers and heads.
- Falsification risk: If standard attention heads already show high correlation with causal effects, the novelty of the metric is diminished.
- Why this is not generic: It moves beyond the qualitative claim of 'attention is not explanation' to a quantitative, measurable benchmark for evaluating the reliability of attention as an interpretability tool.
- Confidence: medium
- Required next search: Search for recent papers quantifying 'attention faithfulness' or 'causal mediation analysis in Transformers' to ensure the metric isn't already established.
