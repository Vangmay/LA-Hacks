# Proposal Seeds



## Proposal Seed: Hard-Thresholded Sparse Retrieval Experts (HT-SRE)

- Status: raw
- Originating taste: Obscure-Literature Dredger
- Seed-paper hook: Shazeer et al. (2017) Sparsely-Gated MoE expert gating instability.
- Evidence trigger: Gating collapse mentioned as a major limitation in early and modern MoE implementations.
- Candidate novelty: Replacing learned gating networks with deterministic retrieval mechanisms (e.g., locality-sensitive hashing or k-d tree routing) common in 90s Information Retrieval but neglected in current gradient-dense MoE.
- Technical mechanism: Use a fixed hashing-based router that maps input embeddings to a set of 'expert' weights without a secondary learned gating MLP, potentially using techniques from 90s 'associative memory' research.
- Closest prior-work collision: Jacobs et al. (1991) Adaptive Mixture of Local Experts; early associative memory networks (Kohonen).
- Closest future-work collision: Switch Transformer (Fedus 2021); Hash Layers (Roller et al. 2021).
- Minimum validation: Compare training stability and expert distribution for standard MoE vs Hashing-MoE on a language modeling task.
- Falsification risk: Static routing might fail to specialize experts as effectively as learned routing.
- Why this is not generic: It specifically proposes a shift from neural gating back to signal-processing/IR retrieval mechanisms to solve modern stability issues.
- Confidence: medium
- Required next search: Early 90s research on 'hashing in neural networks' and 'neural associative memory routing'.
