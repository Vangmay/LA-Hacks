# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Resolving seed paper 1706.03762 to begin research loop.


## Step 2: append_workspace_markdown

Recorded seed paper metadata in papers.md.


## Step 3: paper_relevance_search

Searching for papers discussing transformer limitations to identify research gaps.


## Step 4: append_workspace_markdown

Recorded Peng et al. (2024) in papers.md. This paper is highly relevant as it identifies a fundamental theoretical limitation regarding function composition.


## Step 5: append_workspace_markdown

Recorded the finding regarding function composition limitations in findings.md. This is a high-value gap for novelty ideation.


## Step 6: append_workspace_markdown

Generated the first proposal seed in proposal_seeds.md, targeting the function composition gap identified in Peng et al. (2024).


## Step 7: paper_relevance_search

Searching for architectural solutions to function composition to evaluate the novelty of the proposed state-augmentation seed.


## Step 8: append_workspace_markdown

Recorded Zubic et al. (2024) in papers.md. This paper reinforces the compositionality gap and adds that CoT prompting might not be a sufficient architectural fix for the scaling problem.


## Step 10: append_workspace_markdown

Recorded the finding that CoT prompting fails to solve the compositional scaling problem in SSMs/Transformers (Zubic et al. 2024). This strengthens the case for the proposed 'External State' seed.


## Step 11: paper_relevance_search

Performing a precision search for 'differentiable scratchpads' and 'external memory' to test the collision risk of the proposed 'Compositional Transformer Augmentation' seed.


## Step 12: append_workspace_markdown

Recorded Tang & Xie (2026) in papers.md. This is a critical collision/formalization paper that reframes Transformers as stateless DNCs, providing a theoretical basis for why they struggle with dynamic compositionality.


## Step 13: append_workspace_markdown

Recorded Soulos et al. (2023) in papers.md. This is a strong collision/alternative that shows structured, symbolic-like tree operations with external memory can solve compositionality far better than standard Transformers.


## Step 14: paper_relevance_search

Searching for hybrid Transformer-SSM architectures that might address the compositionality gap, specifically looking for models that combine the strengths of both to solve the 'stateless' vs 'compositional' trade-off.


## Step 15: append_workspace_markdown

Recorded TransXSSM in papers.md. Noted that while it is a hybrid model, its primary contribution is positional encoding compatibility, not compositional reasoning.


## Step 16: paper_relevance_search

Searching for neuro-symbolic hybrid architectures that use external memory to solve compositionality and reasoning tasks. This will help refine the 'Compositional Transformer Augmentation' seed and determine if 'structured state' is a sufficiently novel angle compared to existing neuro-symbolic approaches.


## Step 17: append_workspace_markdown

Recorded RetoMaton (2025) in papers.md. This is a strong collision that uses WFAs for structured memory. It validates the direction (structured memory > implicit CoT) but suggests my seed might need to be broader than just automata to be novel (e.g., general functional composition vs. specific automata transitions).


## Step 18: paper_relevance_search

Searching for 'neural functional composition' to find architectures that use differentiable/continuous states for composition, aiming to differentiate my seed from the discrete/symbolic 'Tree Operations' (Soulos et al. 2023) and 'Automata' (RetoMaton) approaches.


## Step 19: append_workspace_markdown

Recorded Fang & Jin (2025) in papers.md. This paper's use of a 'Differentiable Hidden State' in a continuous-time framework (Neural ODE) provides a potential technical precedent for the 'continuous functional state' I am proposing for compositionality.


## Step 20: append_workspace_markdown

Recorded Wang et al. (2024) in papers.md. This paper provides theoretical grounding for the use of 'reusable neural modules' (functional blocks) to achieve universal approximation, supporting the technical feasibility of a modular compositional architecture.
