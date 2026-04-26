# Proposal Seeds



## Proposal Seed: Formal Equivalence Analysis of Linear Attention and Gated RNNs

- Status: raw
- Originating taste: historical_equivalence_prosecutor
- Seed-paper hook: Vaswani et al. (2017) claim to 'dispense with recurrence entirely' to achieve O(1) path lengths between distant positions.
- Evidence trigger: The trade-off between O(N^2) attention (O(1) path) and O(N) recursion (O(N) path) is a fundamental bottleneck mentioned in the seed (Section 2).
- Candidate novelty: Formalizing the 're-discovery' arc wherein sub-quadratic scaling (Linear Attention/SSMs) implicitly reintroduces the recursive bottlenecks the original Transformer was designed to evade, specifically mapping kernel-based attention to classical Fast Weight Programmers or SRNs.
- Technical mechanism: Establishing a bijection between the update rules of modern Linear Attention (e.g., Katharopoulos) and 1990s-era recursive neural networks using non-linear kernels.
- Closest prior-work collision: Schmidhuber (1992) 'Learning to control fast-changing weights' or Hopfield Networks.
- Closest future-work collision: Katharopoulos et al. (2020) 'Transformers are RNNs'.
- Minimum validation: A analytical comparison of the Jacobian of the state update in a Linear Transformer vs. a modern LSTM/GRN derivative.
- Falsification risk: If Linear Attention mechanisms demonstrate a retrieval capability that is provably impossible for a fixed-size latent state RNN.
- Why this is not generic: It specifically targets the Transformer's founding claim of being 'non-recurrent' and tests if sub-quadratic scaling is a regression to the very architecture it replaced.
- Confidence: medium
- Required next search: Search for 'mathematical equivalence of linear attention and gated recurrence' and 'Schmidhuber fast weights transformer connection'.


## Proposal Seed: Selective Fragment Retrieval for Bottleneck-Constrained Transformers

- Status: raw
- Originating taste: Research-Gap Miner (Targeting context scaling walls)
- Seed-paper hook: Vaswani et al. (2017) acknowledges that the sequence length N is a fundamental bottleneck due to $O(N^2)$ complexity in the self-attention mechanism.
- Evidence trigger: The 'dot-product attention' mechanism requires comparing every token against every other token, which is inefficient for sparse or long-range dependencies where only a subset of historical features are statistically significant.
- Candidate novelty: Introduce a learnable 'retrieval-gate' that operates on compressed sequence fragments before the attention layer, effectively bypassing the quadratic computation for non-relevant segments.
- Technical mechanism: A two-stage process: (1) low-fidelity fragment scoring via a lightweight linear projection, (2) high-fidelity softmax attention only over the top-k retrieved fragments and local sliding window.
- Closest prior-work collision: Longformer (sliding window) and BigBird (random/global tokens), but those use static or probabilistic patterns rather than dynamic content-based retrieval at every layer.
- Closest future-work collision: RAG (Retrieval-Augmented Generation) usually retrieves from a static external database; this proposal proposes retrieval from the *internal* activations of the current long sequence.
- Minimum validation: Test on the 'Long Range Arena' benchmark specifically to observe if fragment retrieval out-performs local-only or sparse-global patterns on hierarchical tasks.
- Falsification risk: The overhead of the retrieval gating mechanism might exceed the savings from skipped attention computation for sequences under 8k tokens.
- Why this is not generic: It specifically targets the internal KV-cache management bottleneck within a single forward pass, rather than just appending document results.
- Confidence: low
- Required next search: Search for 'internal KV-cache retrieval' and 'dynamic sparse attention' to see if this gating mechanism has been formalized in the last 2-3 years.


## Proposal Seed: Hardware-Aware Kernel Refactor of 1990s Fast Weights

- Status: promising
- Originating taste: historical_equivalence_prosecutor
- Seed-paper hook: Schlag et al. (2021) showed linear attention is a Fast Weight Programmer (FWP) from the 90s, but modern sub-quadratic scaling (FlashAttention, Mamba) relies on hardware-aware tiling/fusing.
- Evidence trigger: The equivalence finding (Schlag, 2021) identifies a memory limit in purely additive updates (the 'delta rule' gap).
- Candidate novelty: Translating the 'delta rule' and 'associative memory' enhancements of 1990s FWPs into Triton kernels to see if they outperform Mamba/RWKV in the context of retrieval-augmented attention.
- Technical mechanism: Implementing the 1992 Fast Weight update as a hardware-fused scan operator (similar to Mamba's selective scan) to bypass the O(N) bottleneck of the original sequential FWP implementation.
- Closest prior-work collision: Schmidhuber (1992) 'Learning to control fast-changing weights'.
- Closest future-work collision: Gu et al. (2024) 'Mamba' (SSM-based scaling).
- Minimum validation: Comparing the perplexity/latency of an 'FWP-Triton' model against RWKV-v6 and Mamba on the LongBench or ProofPile datasets.
- Falsification risk: If the high-dimensional hidden state updates required by the delta rule cannot be parallelized as effectively as simple additive updates, the hardware gains might vanish.
- Why this is not generic: It bridges the gap between historical theoretical superiority (90s) and modern implementation efficiency (2020s).
- Confidence: medium
- Required next search: Search for 'Triton implementations of fast weight programmers' and 'hardware-aware linear attention kernels'.


## Proposal Seed: Differentiable HNSW Layer for Dynamic Sub-Quadratic Attention

- Status: promising
- Originating taste: historical_equivalence_prosecutor
- Seed-paper hook: Lee et al. (2024) Hierarchically Pruned Attention (HiP) uses tree-search ($O(T \log T)$) to estimate top-k keys.
- Evidence trigger: The findings on the convergence of attention pruning and vector retrieval suggest that fixed search structures (k-NN) are being retrofitted onto dynamically changing Transformer activations.
- Candidate novelty: Replacing 'learned' sparse attention patterns with a truly differentiable Hierarchical Navigable Small World (HNSW) graph layer. While k-NN is classical, making the graph construction and traversal differentiable through the query-key path would allow the model to 'learn' a search index structure concurrently with its representations.
- Technical mechanism: Formulating the HNSW graph construction as a differentiable process (e.g., using Gumbel-Softmax on edge selection or straight-through estimators) to replace the standard $O(N^2)$ attention matrix with a graph-traversal layer that retains sub-quadratic $O(N \log N)$ complexity during both training and inference.
- Closest prior-work collision: Malkov & Yashunin (2018) 'Efficient and robust approximate nearest neighbor search using HNSW' (non-differentiable).
- Closest future-work collision: Zhang et al. (2023) 'H2O: Heavy-Hitter Oracle' (heuristic pruning, not differentiable).
- Minimum validation: Compare an HNSW-Attention layer against FlashAttention-2 in terms of gradient quality and retrieval accuracy on the 'Needle In A Haystack' benchmark.
- Falsification risk: If the overhead of maintaining a differentiable graph structure surpasses the $O(N^2)$ costs for sequence lengths under 32k tokens, the utility vanishes.
- Why this is not generic: It moves beyond 'heuristic pruning' of attention (which is a known technique) toward 'differentiable indexing,' a specific gap identified between the DB community and the DL community.
- Confidence: medium-high
- Required next search: Search for 'differentiable graph indexing neural networks' and 'HNSW in transformer layers'.


## Proposal Seed: Addressable State-Space Retrieval (ASSR)

- Status: promising
- Originating taste: Research-Gap Miner (Addressing retrieval gaps in SOTA models)
- Seed-paper hook: Huang (2024) and Lu et al. (2025) identify that Mamba/SSM sub-quadratic scaling fails on NIAH (Needle-in-a-Haystack) tasks because compressed states lose 'addressability'.
- Evidence trigger: The 'lost-in-the-middle' and retrieval failures in fa2f8963df88d8684b38c33aa59cc3ae0927561b highlight that purely recurrent state compression is insufficient for high-precision, non-local retrieval.
- Candidate novelty: Introduce a 'Hybrid-Addressable' memory layer that stores a subset of high-entropy SSM state snapshots in a quantized vector store, allowing the sub-quadratic model to 'recall' specific historical states via a retrieval-augmented query before continuing the recurrence.
- Technical mechanism: 1. Deploy a standard SSM (e.g., Mamba) for O(N) throughput. 2. At fixed intervals or high-uncertainty tokens, push the current latent state to an external mini-KV-cache. 3. Use an 'Attention-over-Recurrence' gate to query these snapshots when the temporal decay in the main state exceeds a threshold.
- Closest prior-work collision: Hybrid Mamba-Transformer models (e.g., Jamba) utilize full attention layers. This proposal is different because it retrieves *intermediate latent states* (SSM states) rather than raw token embeddings.
- Closest future-work collision: Retrieval-Augmented Generation (RAG) focuses on external text; this focuses on architectural 'internal retrieval' of the hidden state history.
- Minimum validation: Evaluate on the NIAH (Needle-in-a-Haystack) benchmark using Mamba-2.8B with and without the ASSR layer to see if it restores the 100% accuracy typically seen only in quadratic Transformers.
- Falsification risk: If the bottleneck in Mamba is the *projection* into the state rather than the state's storage capacity, then external retrieval won't help.
- Why this is not generic: It specifically addresses the addressability decay in linear recurrence identified of current SOTA sub-quadratic models.
- Confidence: medium
- Required next search: Search for 'latent state retrieval' or 'Mamba state checkpointing' to ensure this hybrid approach hasn't been implemented for internal architectures.
