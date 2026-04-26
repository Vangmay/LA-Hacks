# Memory - Dynamic and Sparse Computation Mechanisms

## Stable Facts
- The Transformer (Vaswani et al., 2017) introduced self-attention as a replacement for recurrence/convolution, which has a quadratic computation cost relative to sequence length.
- Modern sparsity often targets the $O(n^2)$ self-attention bottleneck or the parameter density in Feed-Forward Networks (FFNs).

## Search Threads
- **Ancestry Search**: Tracing 'conditional computation' and 'MoE' back to the early 90s (e.g., Jacobs, Jordan, Hinton, Nowlan).
- **Mathematical Precedents**: Investigating signal processing and matrix compression techniques (Fast Multipole Method, Wavelets) as potential analogues for sparse attention.
- **Obsolete Sparse Implementations**: Searching for early 90s hardware-specific sparsity tricks that didn't survive the dense-matrix GPU era.

## Candidate Papers
- Vaswani et al. (2017): Root seed.

## Open Questions
- Did the 90s connectionist community explore 'sparse attention-like' indexing before memory became as cheap as it is today?
- Were 'Mixture of Experts' initially proposed as a way to handle multi-modal data or as a pure efficiency mechanism?

## Step 3: write_workspace_markdown

Initialized memory.md with foundational facts and search threads focusing on 90s precursors to modern sparsity.


## Step 4: get_references

Fetching references for the seed paper 'Attention is All you Need' to identify the intellectual ancestry of the dynamic mechanisms it mentions (e.g., conditional computation/sourcing).


## Step 5: append_workspace_markdown

Recorded Shazeer's MoE paper as a key foundational reference for dynamic and sparse computation. This serves as the bridge between 90s theoretical sparsity and modern SOTA.


## Step 6: append_workspace_markdown

Recorded the first finding regarding MoE as the dominant dynamic computation mechanism. This fills the findings.md requirement before I proceed with deeper historical search.


## Step 7: append_workspace_markdown

Created the first proposal seed targeting the instability of MoE gating by looking back at 90s retrieval-based mechanisms.


## Step 8: paper_bulk_search

Searching for the foundational 90s Mixture of Experts papers to trace the origins of modern dynamic computation. Looking specifically for the Jacobs/Jordan/Hinton lineage to see if early sparsity mechanisms were lost in the transition to modern deep learning.


## Step 9: append_workspace_markdown

Recorded the 1993 Jordan & Xu paper to establish the EM-based roots of Mixtures of Experts. This highlights a shift from discrete statistical optimization to continuous gradient-based approximation in modern sparsity.


## Step 10: append_workspace_markdown

Recorded the finding that modern MoE relies on continuous relaxations of what were originally discrete selection problems, which contributes to current expert-balancing issues.


## Step 11: paper_bulk_search

Investigating whether modern sparse attention mechanisms have rediscovered the Fast Multipole Method (FMM) or similar N-body simulation speedups from classical physics/calculus. This query seeks to bridge the gap between 80s/90s numerical methods and modern 'efficient' Transformers.


## Step 12: google_scholar_search

The Semantic Scholar bulk search for 'Fast Multipole Method' returned zero papers, which is surprising given the mathematical similarity between N-body interactions and self-attention. I am switching to Google Scholar to see if this connection exists under different terminology or in less mainstream venues (e.g., physics-informed ML or numerical analysis workshops).


## Step 13: append_workspace_markdown

Recorded Fmmformer as a successful 'rediscovery' of the 80s Fast Multipole Method in the context of Transformer efficiency. This validates my search thread on mathematical precedents.


## Step 14: append_workspace_markdown

Recorded the finding that complex sparse attention converges on the 1980s Fast Multipole Method. This successfully closes the 'Mathematical Precedents' search thread.


## Step 15: paper_bulk_search

Searching for early 80s and 90s implementations of conditional computation and dynamic branching to see if modern dynamic mechanisms (like MoE or Early Exit) have forgotten hardware-centric precedents from the pre-GPU era.


## Step 16: google_scholar_search

Semantic Scholar bulk search for 'conditional computation' in the 1985-1998 period failed to return results, likely due to indexing gaps for older papers. Switching to Google Scholar to find precursors to modern dynamic mechanisms like MoE and conditional branching, specifically looking for Bengio's or Hinton's early work in this area.


## Step 17: append_workspace_markdown

Recorded the Bengio 2015 paper on RL-based conditional computation. This paper provides the link between early 90s gating and modern MoE architectures, highlighting a transition from RL-based discrete decisions to continuous approximations.
