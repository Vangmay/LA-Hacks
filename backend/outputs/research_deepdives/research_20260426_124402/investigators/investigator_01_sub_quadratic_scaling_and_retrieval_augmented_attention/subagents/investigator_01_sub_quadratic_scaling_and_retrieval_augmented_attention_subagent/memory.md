# Memory

## Stable Facts
- Seed Paper: "Attention is All You Need" (Vaswani et al., 2017).
- Objective: Novelty ideation in sub-quadratic scaling and retrieval-augmented attention.
- Taste: Prior-Art Prosecutor (searching for historical mathematical equivalence).

## Search Threads
- Initializing seed paper metadata and tracing references.
- Investigating historical predecessors (associative memories, kernels, RNNs) to the Transformer.

## Open Questions
- Which modern sub-quadratic architectures are structurally equivalent to pre-Transformer models?
- Are retrieval-augmented methods truly novel or just re-parameterized k-Nearest Neighbors or classical memory stores?

## Contradictions
- None yet.

## Step 1: write_workspace_markdown

Initialized memory.md with objective and initial search threads.


## Step 2: append_workspace_markdown

Initialized papers.md with the seed paper metadata. I will now look for sub-quadratic or retrieval-augmented follow-ups that address sequence length scaling.


## Step 2: resolve_arxiv_paper

Resolving the seed paper (Vaswani et al., 2017) to obtain a canonical Semantic Scholar ID for further lineage tracing of sub-quadratic scaling and historical antecedents.


## Step 3: append_workspace_markdown

Recorded the seed paper in papers.md with prosecution-focused relevance notes.


## Step 4: append_workspace_markdown

Recorded the initial baseline finding regarding the Transformer's stance on recurrence vs. attention.


## Step 3: append_workspace_markdown

Repairing papers.md to include the baseline Transformer paper with all required fields in the correct format.


## Step 5: append_workspace_markdown

Added a raw proposal seed focused on the historical equivalence of sub-quadratic attention to recurrence, satisfying the artifact contract for proposal_seeds.md before proceeding with literature retrieval.


## Step 6: get_references

Tracing references of the seed paper to locate foundational work in sub-quadratic sequence modeling (e.g., convolutional pathways, early attention/alignment mechanisms) that the Transformer aimed to supersede.


## Step 4: append_workspace_markdown

Populated proposal_seeds.md with a speculative seed addressing the architectural bottleneck of the 2017 Transformer. I will now search for modern sub-quadratic and retrieval-augmented papers to ground this more firmly.


## Step 7: append_workspace_markdown

Recorded Gehring et al. (2017) in papers.md as a key sub-quadratic reference that the Transformer cited for parallelizability.


## Step 5: paper_relevance_search

Searching for modern papers (post-2017) that introduce sub-quadratic mechanisms or integrate retrieval into the self-attention layer to evaluate for novel gaps.


## Step 6: append_workspace_markdown

Recorded the HiP (2024) paper which demonstrates sub-quadratic complexity via hierarchical pruning. This matches my 'Research-Gap miner' taste by providing a specific mechanism (attention locality) that I can now scrutinize for limitations.


## Step 8: paper_relevance_search

Searching for papers that explicitly link modern Linear Attention or sub-quadratic mechanisms to historical RNNs or Fast Weight methods, testing the Prosecutor taste's hypothesis of mathematical equivalence.


## Step 7: append_workspace_markdown

Synthesized a finding regarding the 'attention locality' assumption in sub-quadratic models. This identifies a major gap: how do these models perform when relevant info is strictly non-local?


## Step 9: append_workspace_markdown

Verified the mathematical equivalence between linear attention and 1990s fast weight programmers, supporting the historical equivalence thesis.


## Step 8: paper_relevance_search

Searching for papers that critique sub-quadratic or sparse attention models specifically on non-local tasks, seeking to validate the gap where 'attention locality' assumptions fail.


## Step 10: append_workspace_markdown

Recorded the high-confidence finding regarding the mathematical equivalence of linear transformers and 1990s RNN architectures.


## Step 11: append_workspace_markdown

Promoted the equivalence finding into a concrete proposal seed that bridges 90s theory with 2024 hardware-aware kernel techniques.


## Step 9: paper_bulk_search

Searching for recent critiques of sub-quadratic models specifically regarding retrieval bottlenecks or failures to capture non-local dependencies to deepen the 'Research-Gap miner' evidence base.


## Step 10: paper_relevance_search

Bulk search was too restrictive. Switching to a relevance search for 'Needle In A Haystack' (NIAH) failures in sub-quadratic models. This is the gold-standard test for whether the 'attention locality' assumption I found earlier breaks when retrieval is non-local/random.


## Step 12: paper_relevance_search

Shifting focus to retrieval-augmented attention to determine if modern RAG/retrieval mechanisms are technically novel or re-parameterized k-Nearest Neighbors/memory systems, following the Prosecutor taste's audit of sub-quadratic scaling lineage.


## Step 11: paper_relevance_search

Broadening search to include specific architecture families like 'Linear Attention' and 'State Space Models' (Mamba/RWKV) to find documented failures on the Needle In A Haystack (NIAH) benchmark, which specifically stresses non-local retrieval.


## Step 13: append_workspace_markdown

Recorded HiP (2024) as a recent example of O(T log T) scaling that uses k-NN structures, further blurring the line between attention and retrieval.


## Step 14: append_workspace_markdown

Documented the technical convergence of attention pruning and k-NN retrieval, reinforcing the Prosecutor hypothesis that modern scaling is often a re-application of classical search algorithms.


## Step 12: google_scholar_search

Switching to Google Scholar to find specific benchmark comparisons between sub-quadratic models (like Mamba) and Transformers on non-local retrieval tasks (Needle In A Haystack), as Semantic Scholar relevance search for 'failure' was too narrow.


## Step 15: append_workspace_markdown

Proposed a differentiable HNSW layer to bridge the gap between classical vector retrieval and dynamic neural attention.


## Step 13: paper_relevance_search

Found evidence in Google Scholar snippets that Mamba/SSMs exhibit 'lost-in-the-middle' phenomena and fail at Needle-in-A-Haystack (NIAH). Resolving this paper to confirm the exact retrieval failure modes and quantify the gap relative to Transformers.


## Step 14: append_workspace_markdown

Recorded the Huang (2024) paper which identifies the critical empirical failure of sub-quadratic models on NIAH. This perfectly grounds my next proposal on why sub-quadratic scaling often breaks retrieval.


## Step 15: append_workspace_markdown

Recording the high-confidence finding that sub-quadratic models fail in practical retrieval despite theoretical scaling. This sets the stage for a proposal seed on addressable sub-quadratic memory.


## Step 16: append_workspace_markdown

Added a new proposal seed for Addressable State-Space Retrieval (ASSR), targeting the specific addressability failure in SSMs found in the Huang (2024) evidence.


## Step 17: paper_relevance_search

Running a final adversarial search to check for collisions with the 'Addressable State-Space Retrieval' proposal. I want to ensure that papers like 'H-MHESA' or 'Mamba-Memory' haven't already implemented internal hidden-state retrieval.
