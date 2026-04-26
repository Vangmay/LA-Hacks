# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 2: resolve_arxiv_paper

Resolving seed paper 'Attention is All You Need' (arXiv:1706.03762) to canonical ID.


## Step 3: append_workspace_markdown

Recorded seed paper 'Attention is All you Need' in papers.md.


## Step 4: get_references

Fetching references for the seed paper to trace technical ancestry.


## Step 5: append_workspace_markdown

Populated papers.md with key foundational references from the seed paper's citation list (Seq2Seq, Attention in NMT, LSTM).


## Step 6: append_workspace_markdown

Populated findings.md with key findings regarding the technical lineage of Transformers and the parallelization bottleneck of RNNs.


## Step 7: append_workspace_markdown

Created a speculative proposal seed in proposal_seeds.md addressing the quadratic complexity bottleneck of the Transformer architecture.


## Step 8: paper_relevance_search

Searching for specific Transformer limitations (inductive bias, interpretability) to find new evidence triggers for novelty seeds.


## Step 9: append_workspace_markdown

Added recent (2023-2025) papers addressing Transformer inductive bias and efficiency to papers.md.


## Step 10: paper_relevance_search

Searching for methods to inject inductive bias into Transformers while avoiding traditional convolutions, targeting a potential new novelty dimension.


## Step 11: append_workspace_markdown

Added papers addressing inductive bias injection (hybrid/distillation approaches) and the theoretical quantification of inductive bias to papers.md.


## Step 12: paper_relevance_search

Investigating the 'localization' claim (that attention is often sparse/local) to see if it generalizes from diffusion models to LLMs/Transformers, which could lead to a new novelty direction.


## Step 13: paper_bulk_search

Previous search for 'sparsity and localization in LLMs' was unsuccessful. Pivoting to a broader bulk search for 'attention sparsity transformer patterns' to identify empirical evidence of sparse/local attention behaviors.


## Step 14: append_workspace_markdown

Added paper 'Algorithm to Compilation Co-design' to papers.md; it provides evidence that optimal attention sparsity might not be square-blocked.


## Step 15: paper_relevance_search

Pivoting search to 'attention sinks' to investigate a specific known phenomenon of attention localization/specialization in LLMs, which might validate the 'localization' hypothesis for Transformer architectures.


## Step 16: append_workspace_markdown

Added several key papers on the 'attention sink' phenomenon to papers.md, covering security implications, multimodal manifestations, geometric interpretations, and architectural mitigations.


## Step 17: append_workspace_markdown

Consolidated findings on the geometric nature of attention sinks and their dual roles as computational waste and security vulnerabilities.


## Step 18: paper_relevance_search

Checking for the existence of 'Vision Transformers Need Registers' to avoid redundancy and refine the 'Explicit Coordinate Registers' novelty seed.


## Step 19: append_workspace_markdown

Added papers on 'Vision Transformer Registers' to papers.md, covering identification (Darcet et al.), training-free mitigation (Jiang et al.), and alternative mechanistic explanations (Shi et al.). This helps refine the 'Explicit Coordinate Registers' idea by showing what has already been done (adding tokens vs. training-free shifting vs. semantic integration).


## Step 20: append_workspace_markdown

Added a finding regarding the contradiction/uncertainty in the root cause of attention sinks (Geometric necessity vs. Semantic shortcut vs. Computational artifact).


## Step 21: append_workspace_markdown

Created a promising proposal seed: 'Latent Coordinate Anchors (LCA)', which aims to proactively provide geometric reference frames to Transformers, rather than reactively absorbing attention sinks using registers.


## Step 22: paper_relevance_search

Performing an adversarial collision search for the 'Latent Coordinate Anchors (LCA)' proposal to ensure novelty regarding explicit reference frames in Transformers.


## Step 23: paper_relevance_search

The previous search for explicit coordinate systems yielded no results. This supports the novelty of the LCA proposal. Running a final precision search for 'geometric inductive bias' and 'reference frame' in attention to confirm no close semantic matches exist.
