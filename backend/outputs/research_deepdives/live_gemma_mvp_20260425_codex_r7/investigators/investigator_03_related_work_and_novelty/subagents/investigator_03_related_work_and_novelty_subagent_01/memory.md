# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Resolved seed paper URL to canonical ID.


## Step 2: append_workspace_markdown

Initialized papers.md with the seed paper metadata.


## Step 3: get_references

Fetching references of the seed paper to map technical ancestry (RNNs, CNNs, and prior attention mechanisms).


## Step 4: append_workspace_markdown

Added CNN-based Seq2Seq paper to papers.md to track architectural competitors.


## Step 5: append_workspace_markdown

Recorded the architectural motivation (parallelization) in findings.md.


## Step 6: append_workspace_markdown

Generated a raw proposal seed targeting the tension between Transformer scalability and structural modeling capabilities.


## Step 7: paper_relevance_search

Executing collision search for the 'Structural Inductive Bias' proposal to check for existing work like Graphormer or learned mask mechanisms.


## Step 8: append_workspace_markdown

Added DAFormer paper to papers.md; it confirms interest in topology-aware transformers but suggests the novelty must lie in *learning* the topology from scratch.


## Step 9: paper_relevance_search

Refining collision search: moving from 'applying masks' to 'learning masks/topology end-to-end' to better differentiate the proposal seed.


## Step 10: append_workspace_markdown

Added Sparsifiner to papers.md; it represents a strong collision for learned sparse attention patterns.


## Step 11: append_workspace_markdown

Added the 'Routing Absorption' paper to papers.md. This is a critical finding that challenges the end-to-end training approach suggested in the initial proposal seed.


## Step 12: append_workspace_markdown

Recorded the 'Routing Absorption' finding. This invalidates the first version of the 'Structural Inductive Bias' proposal seed and necessitates a pivot towards decoupled or non-per-query mechanisms.


## Step 13: paper_relevance_search

Searching for methods that decouple representation learning from sparsification to bypass the 'Routing Absorption' barrier identified in the previous step.


## Step 14: append_workspace_markdown

Added VSA paper to papers.md. Its coarse-to-fine approach provides a potential architectural path to bypass the 'Routing Absorption' barrier seen in per-query gating.


## Step 15: paper_relevance_search

Searching for 'learned hierarchical sparse attention' to see if the coarse-to-fine approach (like VSA) has been applied to general Transformers to overcome routing absorption.


## Step 16: append_workspace_markdown

Added HSA-Transformer to papers.md. This paper is a direct implementation of the hierarchical sparse idea, providing a benchmark for what 'learned gating' currently looks like in the literature.


## Step 17: paper_relevance_search

Searching for 'differentiable topology generation' to see if there are methods for creating structural masks that aren't simple per-token gates, specifically looking for ways to avoid 'routing absorption'.


## Step 18: append_workspace_markdown

Added TAM-GT to papers.md. It reinforces the idea that 'topology-aware' attention is highly effective when the structure is known, but highlights that the challenge for my proposal is *learning* that structure from unstructured data without falling into the 'routing absorption' trap.


## Step 19: paper_relevance_search

Exploring two-stage or decoupled training strategies for sparse attention to see if they provide a viable way to circumvent the 'Routing Absorption' barrier identified earlier.


## Step 20: append_workspace_markdown

Added RocketKV to papers.md; its coarse-to-fine two-stage approach provides structural evidence for hierarchical sparsification, though it focuses on inference-time KV cache compression.


## Step 21: append_workspace_markdown

Recorded the finding that coarse-to-fine/two-stage architectures are a potential way to avoid 'Routing Absorption'. This shifts the research focus from 'per-query gating' to 'hierarchical/coarse-to-fine topology learning'.


## Step 22: paper_relevance_search

Searching for 'stable' (layer-wise or block-wise) learned sparse attention to see if this is an established strategy for avoiding per-query 'routing absorption'.


## Step 23: paper_bulk_search

The previous specific search for 'stable layer-wise learned sparse attention' failed. Switching to a broader search for 'layer-wise sparsity' and 'block-wise sparsity' in Transformers to identify existing patterns and gaps.


## Step 24: append_workspace_markdown

Added SVOO to papers.md. This paper establishes that layer-wise sparsity is an intrinsic and useful property, but since it is training-free, it leaves an open question: can we learn these stable, layer-wise patterns end-to-end?


## Step 25: paper_relevance_search

Executing a highly targeted collision search for 'end-to-end learned block-wise sparse attention' to see if anyone has successfully bridged the gap between 'learned sparsity' and 'stable (non-per-query) patterns' to bypass routing absorption.


## Step 26: append_workspace_markdown

Added RainFusion2.0 to papers.md. It confirms the trend toward block-wise prediction, but the 'online adaptive' nature suggests it might still face the absorption issue if the mask is too fine-grained or per-query.


## Step 27: append_workspace_markdown

Pivoted the primary proposal seed from 'per-query learned masks' to 'decoupled, stable layer-wise topology learning' to specifically address the 'Routing Absorption' blocker.
