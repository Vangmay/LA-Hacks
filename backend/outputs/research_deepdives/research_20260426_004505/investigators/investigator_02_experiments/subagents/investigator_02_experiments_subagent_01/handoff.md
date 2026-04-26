# Hand-Off

## Research Summary
I have investigated the technical ancestry and contemporary research landscape of the Transformer architecture to identify novel spinoff directions. The research focused on the tension between the parallelization achieved by pre-Transformer architectures (CNNs, MoE) and the global modeling of the Transformer.

## Searched Queries
- `resolve_arxiv_paper` for seed (arXiv:1706.03762)
- `get_references` to map technical ancestry.
- `paper_relevance_search` for 'gated convolutional attention'.
- `paper_relevance_search` for 'convolutional sparsity mask transformer'.
- `paper_relevance_search` for 'transformer "dynamic attention" sparsity mask learned'.

## Key Papers
- **Attention is All you Need (2017)**: Seed paper; introduced pure attention.
- **Convolutional Seq2Seq (2017)**: Ancestor/Competitor; demonstrated parallelization via CNNs.
- **Sparsely-Gated MoE (2017)**: Ancestor/Competitor; demonstrated capacity via conditional computation.
- **GCAT (2025)**: Collision risk; uses gated convolutional attention for efficiency in CV, but for feature enhancement rather than sparsity routing.
- **Dynamic Sparse Mask Transformer (2025)**: Collision risk; uses percentile-based thresholding for sparsity, which is score-based rather than structural.

## Strongest Novelty/Gap Implications
The research revealed a significant distinction between **score-based sparsity** (selectively keeping high attention scores via thresholds) and **structural sparsity** (using an auxiliary network to predict the topology of the attention matrix). While recent work (e.g., Asadi et al., 2025) focuses on thresholding, there is a clear opening for a mechanism that uses the local inductive bias of convolutions to predict a structured, sparse topology for global attention.

## Proposal Seeds

### Proposal Seed: Gated Local-Global Attention
- **Core Idea**: Use a lightweight convolutional layer to predict a sparsity mask for the attention matrix, effectively routing attention to local neighborhoods while allowing a small number of 'global experts' to handle long-range dependencies.
- **Evidence Basis**: Collision with score-based methods (Asadi et al., 2025) suggests that thresholding is common, but there is little evidence of convolution-driven topology prediction.
- **Technical Mechanism**: A convolutional-driven sparsity mask generator that guides a sparse attention mechanism.
- **Confidence**: Medium (requires collision check against 'learned structured sparsity').
- **Required Next Search**: Adversarial search for 'learned structured sparsity' and 'dynamic routing via convolutional masks'.

## Recommended Next Steps for Investigator
1. **Adversarial Collision Check**: Specifically search for 'learned structured sparsity' or 'dynamic routing' to ensure the 'topological mask' idea hasn't been claimed by recent work in sparse Transformers.
2. **Mechanism Refinement**: Determine if the mask should be applied to the attention *scores* (masking) or the attention *indices* (routing) to optimize for hardware/throughput.
3. **Promotion**: If no collision is found, promote the seed to a 'Proposal Candidate' and define a formal validation protocol on the Long Range Arena (LRA) benchmark.