# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: This is the seed paper.
- Why it matters: Introduces the Transformer architecture, replacing recurrence and convolution with self-attention mechanisms.
- Caveat: N/A


## Paper: Attention is not explanation

- Paper ID: ChQ_Pm3AqM4J (SerpApi)
- Year: 2019
- Source bucket: serpapi
- Found by: google_scholar_search
- Relation to seed: Critique of the interpretability/explanatory power of the attention mechanism introduced in the seed paper.
- Why it matters: Challenges the assumption that attention weights can be used as a faithful explanation of model decisions.
- Caveat: The critique may be limited to specific attention variants or architectures.


## Paper: A Mechanistic Interpretation of Arithmetic Reasoning in Language Models using Causal Mediation Analysis

- Paper ID: 5dc15ac1c92ab7492f121471823fb13a95d273ba
- Year: 2023
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Closest prior-work. It uses causal mediation analysis to interpret Transformer components (MLPs and attention) in the context of arithmetic reasoning.
- Why it matters: Confirms that causal mediation is a viable and active method for mechanistic interpretability in Transformers. My proposal must distinguish itself by focusing on a *standardized faithfulness metric* rather than just using the technique for task-specific interpretation.
- Caveat: The paper focuses on identifying responsible components rather than providing a general-purpose faithfulness benchmark for attention weights.
