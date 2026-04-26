# Papers

## Paper: Attention is All you Need
- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Self
- Why it matters: Establishes the O(n^2) self-attention baseline. This is the global standard for sequence modeling but acts as the primary bottleneck for long-context scaling due to quadratic VRAM and compute costs.
- Caveat: The paper asserts 'Attention is All You Need' but largely demonstrates it on translation tasks (WMT14); subsequent scaling issues for long-form generation were not yet central in 2017.

## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed paper
- Why it matters: This is the fundamental architecture that established the O(N^2) complexity bottleneck. It serves as the primary benchmark against which all sub-quadratic and linear scaling methods ('Transformer-killers') are measured. Its success in dispensing with recurrence and convolution directly motivates the current search for mechanisms that regain recurrence-like efficiency without losing Transformer-like performance.
- Caveat: Popularity may mask subtle performance trade-offs in low-resource or extremely long-context regimes often claimed by competitors.


## Paper: Hydra: Bidirectional State Space Models Through Generalized Matrix Mixers

- **Paper ID**: ea507df05bb5fe32cd8af80602708713c9bd2ba2
- **Year**: 2024
- **Source bucket**: recent_followups
- **Found by**: paper_relevance_search
- **Relation to seed**: Provides a sub-quadratic (linear-scaling) replacement for the self-attention matrix mixer.
- **Why it matters**: Introduces the 'quasiseparable matrix mixer' framework. It allows for bidirectional sequence modeling (useful for non-causal tasks like image generation or classification) while maintaining the efficiency of Mamba-style SSMs. Reports outperforming BERT and ViT.
- **Caveat**: Most benchmarks are on standard GLUE/ImageNet; the 'ultra-long' context scaling benefit in VRAM-constrained production environments is hinted at but needs specific stress-testing.


## Paper: SCOUT: Toward Sub-Quadratic Attention via Segment Compression

- Paper ID: 475b1e6491fe4c23f47abfcaa5bbf92d22aaf034
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Direct successor addressing the O(N^2) bottleneck.
- Why it matters: It proposes a hybrid approach using local mixers (Mamba or SWA) and attention over compressed 'checkpoint' tokens. This indicates a trend moving away from pure linear attention toward 'compressed quadratic' or 'segment-wise sub-quadratic' methods, suggesting that pure linear mechanisms may still struggle with detail retention in long contexts.
- Caveat: Increased throughput claims for sequences > 8K need verification against modern FlashAttention-3 implementations.


## Paper: SCBench: A KV Cache-Centric Analysis of Long-Context Methods

- Paper ID: Li et al. 2024 (ARXIV:2412.10319)
- Year: 2024
- Source bucket: recent_followups
- Found by: google_scholar_search
- Relation to seed: Direct empirical evaluation of scaling bottlenecks in Transformers vs SSM descendants.
- Why it matters: Identifies that KV cache-centric VRAM bottlenecks are the limit for Transformers at scale. It validates hybrids and SSMs as the only viable path for keeping VRAM footprints below model weight sizes for ultra-long contexts.
- Caveat: The benchmark focuses heavily on retrieval/effective context length; raw generation quality in non-causal visual tasks remains an open comparison area for these specific architectures.


## Paper: Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention

- Paper ID: 6f68e1bb253925d8431588555d3010419f322e04
- Year: 2020
- Source bucket: foundational_references
- Found by: paper_relevance_search
- Relation to seed: Formalized the O(N) linear attention mechanism using kernel associativity.
- Why it matters: This is the 'intellectual ancestor' of modern sub-quadratic methods like RetNet and GLA. It demonstrated that attention could be reformulated as a recurrency, revealing the fundamental trade-off: to achieve linear scaling, one must replace the explicit softmax with a feature map (kernel). Its high citation count (2600+) marks the peak of optimism for pure linear attention before modern hybrid (SSM/Quadratic) methods emerged to fix its precision issues.
- Caveat: Claimed 'similar performance' to vanilla transformers, but later studies (and 2025 follow-ups like SCOUT) highlight that this is only true for certain sequence modeling tasks, not for high-resolution retrieval or complex reasoning.


## Paper: Preconditioned DeltaNet: Curvature-aware Sequence Modeling

- Paper ID: d3944893325ad2906c09870ceef1d2bdb3935229
- Year: 2026
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Successor in sub-quadratic scaling that replaces softmax attention with preconditioned linear recurrences.
- Why it matters: It formalizes the 'Test-Time Regression' (TTR) framework, interpreting linear attention as online least squares. Crucially, it identifies that previous 'delta-rule' models (like DeltaNet) ignored the 'curvature' of the loss, which explains their lagging performance behind quadratic attention. By introducing preconditioning, it attempts to close the expressivity gap mathematically rather than heuristically.
- Caveat: Performance gains are verified at 340M/1B scales; scaling behavior at 70B+ or with high-sparsity MoE remains an open question.
