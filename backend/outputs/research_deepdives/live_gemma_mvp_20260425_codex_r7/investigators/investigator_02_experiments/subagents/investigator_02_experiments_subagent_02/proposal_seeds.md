# Proposal Seeds



## Proposal Seed: Semantic Reservoir Transformer (SRT)

- Status: promising
- Originating taste: Novelty Auditor
- Seed-paper hook: Transformer's quadratic complexity (Vaswani et al., 2017).
- Evidence trigger: Echo State Transformer (Bendi-Ouis & Hinaut, 2025) demonstrates linear complexity via fixed-size reservoir memory but focuses on time-series tasks.
- Candidate novelty: Bridging the gap between Reservoir Computing (typically random/fixed dynamics) and NLP by designing a 'semantic reservoir'—a fixed-size latent state updated via learned projections that preserve linguistic/structural features rather than just temporal ones.
- Technical mechanism: Replace standard self-attention on the full sequence with an attention mechanism operating on a fixed-size, evolving latent reservoir. The reservoir state is updated per token using a gated mechanism (e.g., a lightweight GRU-style update) to manage information compression.
- Closest prior-work collision: Echo State Networks (ESN), standard Transformers, and linear-complexity models like Linformer or Performer.
- Closest future-work collision: Recent recurrent-attention hybrids like RWKV or RetNet.
- Minimum validation: Compare SRT performance against a standard Transformer on language modeling tasks (e.g., WikiText-103) across varying sequence lengths, focusing on the tradeoff between perplexity and computational cost.
- Falsification risk: The fixed-size bottleneck might prevent the model from capturing the high-entropy, nested hierarchical structures essential for complex natural language.
- Why this is not generic: It moves beyond simple 'linear attention' or 'recurrent models' by specifically proposing an attention mechanism that targets a structured, learned memory reservoir.
- Confidence: low
- Required next search: Search for 'reservoir computing for natural language processing' and 'attentional reservoir computing' to identify existing attempts at this hybrid.


## Proposal Seed: Attentional State-Updating Reservoir (ASUR)

- Status: promising
- Originating taste: Novelty Auditor
- Seed-paper hook: Transformer's quadratic complexity (Vaswani et al., 2017) and the linear efficiency of Reservoir Computing (Bendi-Ouis & Hinaut, 2025).
- Evidence trigger: Köster & Uchida (2025) demonstrate that 'attention-enhanced reservoirs' exist but are limited to the readout stage (adapting output weights).
- Candidate novelty: Moving attention from the readout stage to the *internal reservoir state update*. Instead of a passive reservoir, the architecture uses a learned, attentional gating mechanism to update the reservoir's hidden state, allowing the dynamics to be contextually modulated by the input sequence.
- Technical mechanism: A gated recurrent-style update where the reservoir state $h_t$ is updated via $h_t = 	ext{tanh}(W_{res}h_{t-1} + 	ext{Attention}(x_t, h_{t-1}))$. The attention mechanism operates on a fixed-size, low-dimensional representation, maintaining $O(L)$ complexity while providing the 'controlled' dynamics missing in traditional ESNs.
- Closest prior-work collision: Echo State Networks (passive dynamics), Köster & Uchida (readout-based attention), and RWKV (recurrent-based).
- Closest future-work collision: Structured State Space Models (Mamba) and Linear Transformers.
- Minimum validation: Evaluate ASUR on a standard language modeling benchmark (e.g., WikiText-103) against both a standard Transformer and the readout-only 'attention-enhanced reservoir' from Köster & Uchida (2025), measuring the trade-off between perplexity and inference latency/energy efficiency.
- Falsification risk: The overhead of the attentional gate might exceed the computational savings provided by the reservoir architecture.
- Why this is not generic: It specifically targets the *transition* from passive/random reservoir dynamics to actively managed/attentional dynamics, a clear technical distinction from existing RC-NLP research.
- Confidence: medium
- Required next search: Search for 'learned reservoir dynamics' and 'attentional recurrent state updates' to check for existing work on modulating reservoir-like states with attention.
