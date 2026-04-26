# Proposal Seeds



## Proposal Seed: Inductive Bias Injection via Gated Convolutional Attention

- Status: raw
- Originating taste: Ancestry Cartographer (tracing the lineage of parallelization)
- Seed-paper hook: The Transformer replaces recurrence/convolution with pure attention to achieve parallelization (Vaswani et al., 2017).
- Evidence trigger: The tension between the highly parallel but local CNN architectures (e.g., Convolutional Seq2Seq, 2017) and the global but quadratic complexity of the Transformer.
- Candidate novelty: Instead of choosing between the local inductive bias of CNNs and the global receptive field of attention, use a gated/sparse mechanism (inspired by MoE, 2017) to dynamically select convolutional-like local windows for attention, reducing complexity while maintaining structural priors.
- Technical mechanism: Implement a 'Gated Local-Global Attention' where a lightweight convolutional layer predicts a sparsity mask for the attention matrix, effectively routing attention to a local neighborhood while allowing a small number of 'global experts' (MoE) to handle long-range dependencies.
- Closest prior-work collision: Sparse Transformers (Child et al.), which use fixed patterns; hybrid CNN-Transformer architectures.
- Closest future-work collision: Efficient Transformers (Performer, Reformer).
- Minimum validation: Measure training throughput and perplexity on Long Range Arena (LRA) benchmarks compared to standard Transformer and Sparse Transformer.
- Falsification risk: If the gated mask overhead exceeds the complexity savings, or if the loss of unstructured global attention significantly harms performance on tasks requiring dense connectivity.
- Why this is not generic: It specifically targets the trade-off between the structured local priors of the pre-transformer era (CNNs) and the capacity/parallelism of the post-transformer era (MoE/Attention).
- Confidence: medium
- Required next search: Search for 'gated convolutional attention' and 'hybrid CNN-Transformer sparsity patterns' to identify existing implementations.
