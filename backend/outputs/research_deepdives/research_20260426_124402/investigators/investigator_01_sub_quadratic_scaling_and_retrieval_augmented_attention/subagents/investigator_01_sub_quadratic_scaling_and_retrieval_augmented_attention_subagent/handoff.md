# Subagent Hand-Off: Sub-Quadratic Scaling and Retrieval-Augmented Attention

## Overview
This investigation explored the transition from the $O(N^2)$ bottleneck of the 2017 Transformer (Vaswani et al.) to modern sub-quadratic and retrieval-augmented architectures. The research focused on identifying why high-efficiency models often fail to match the retrieval precision of standard Transformers in long-context scenarios.

## Search Summary
- **Targeted**: Foundational scaling bottlenecks, hierarchical pruning mechanisms (HiP), State Space Model (SSM) retrieval failures, and benchmarks like Needle-in-a-Haystack (NIAH).
- **Buckets Filled**: `seed_metadata`, `closest_prior_work`, `recent_followups`, `critiques_limitations`, `research_gaps`, `spinoff_novelty_proposals`.

## Top Papers
1.  **Attention is All you Need (2017)**: The quadratic baseline that defines the $O(N^2)$ scaling wall.
2.  **Hierarchically Pruned Attention (HiP) (2024)**: Demonstrates $O(T \log T)$ scaling via an 'attention locality' hypothesis, which assumes adjacent tokens have similar importance.
3.  **How Well Can a Long Sequence Model Model Long Sequences? (Huang, 2024)**: Proves that theoretically infinite-context models (SSMs/RNNs) empirically fail at precise non-local retrieval (NIAH) and 'lost-in-the-middle'.

## Strongest Research Gaps
- **The Locality Trap**: Sub-quadratic models often rely on token-index locality. In tasks where relevant information is randomly scattered (e.g., code-base navigation), these pruning/locality assumptions create a performance floor.
- **Addressability Decay**: SSMs and linear recurrent models compress history into a hidden state but lose the 'query-to-pointer' addressability of active KV-caches, leading to retrieval failures at scale.

## Proposal Seeds

### 1. Addressable State-Space Retrieval (ASSR)
- **Core Idea**: Fix the addressability failure in SSMs by quantizing and storing latent state snapshots (checkpoints) in an addressable vector-memory to restore NIAH performance.
- **Evidence Basis**: Huang (2024) identifying SSM failure on NIAH despite theoretical scaling.
- **Collision Risk**: Jamba/Hybrid models (already use full attention); novelty rests on retrieving *latent states* rather than raw embeddings.
- **Confidence**: Medium.

### 2. Selective Fragment Retrieval Attention
- **Core Idea**: Using learnable 'retrieval-gates' to choose which compressed sequence fragments to load into the attention window at each layer, bypassing quadratic compute dynamically.
- **Evidence Basis**: Lee et al. (2024) using static trees; this proposes dynamic, learnable gating.
- **Confidence**: Low (speculative).

## Uncertainties & Next Steps
- **Uncertainty**: It is unclear if 'attention locality' is a property of the data or an artifact of common positional encoding (RoPE). 
- **Next Search**: Investigate the effect of Relative vs. Absolute positional embeddings on the success of sub-quadratic pruning mechanisms.