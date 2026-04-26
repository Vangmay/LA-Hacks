# Papers



## Paper: Attention is All you Need

- Paper ID: `204e3073870fae3d05bcbc2f6a8e263d9b72e776` 
- Year: 2017 
- Source bucket: `seed_metadata` 
- Found by: `resolve_arxiv_paper` 
- Relation to seed: Seed paper 
- Why it matters: Establishes the Transformer architecture, replacing recurrence with self-attention. It is the central target for my investigation into how dynamic and sparse computation (like sparse attention or conditional computation) has been proposed to optimize its quadratic complexity.
- Caveat: This paper itself does not focus on 'sparse' mechanisms in the modern sense but relies on dense global attention; the overheads of this dense mechanism are what later works attempt to solve.


## Paper: Do Efficient Transformers Really Save Computation?

- Paper ID: `50503f1de00c567dec1ca8b2fa9d81e822bbed5f` 
- Year: 2024 
- Source bucket: `critiques_limitations` 
- Found by: `paper_relevance_search` 
- Relation to seed: Direct theoretical critique of the 'efficiency' claims made by successors of the seed paper.
- Why it matters: It challenges the assumption that sparse/linear transformers are suitable replacements for the standard Transformer. It finds that for complex reasoning (DP problems), these models require model size to scale with problem size, potentially negating efficiency gains. This is a primary evidence source for my taste in overhead/utility contradictions.
- Caveat: It identifies specific classes of problems where they *can* be efficient, but frames the general 'saving' as theoretically unproven.


## Paper: CODA: Difficulty-Aware Compute Allocation for Adaptive Reasoning

- Paper ID: `bcc5304b13840cc407025d72d1bd45b0abe99ebc` 
- Year: 2026 
- Source bucket: `recent_followups` 
- Found by: `paper_relevance_search` 
- Relation to seed: Extends the concept of adaptive reasoning compute (related to inference scaling) to solve the 'overthinking simple problems' issue.
- Why it matters: It directly addresses the tradeoff between reasoning depth and compute cost using a policy-internal difficulty signal. This provides a clear benchmark/baseline for any proposal involving dynamic sparse attention, as it demonstrates that difficulty-aware allocation can save >60% tokens on easy tasks.
- Caveat: Focuses on token count/reasoning depth rather than sparse attention mechanisms specifically, though the principles of difficulty-aware gating are highly transferable.


## Paper: Sparse Growing Transformer: Training-Time Sparse Depth Allocation via Progressive Attention Looping

- Paper ID: `2kWW9eZhNPMJ` (SerpApi ID)
- Year: 2026
- Source bucket: `recent_followups`
- Found by: `google_scholar_search`
- Relation to seed: Proposes a strategy for sparse depth/attention allocation during training, evolving from the static Transformer seed.
- Why it matters: Critical validation for my proposal: it explicitly establishes 'attention entropy' as a proxy for 'where added depth is valuable.' This justifies the core mechanism of my SDG proposal, which uses entropy to gate sparsity. It suggests that researchers are already pivoting from fixed sparsity to entropy-guided dynamic allocation.
- Caveat: Focuses on training-time progressive growth rather than inference-time dynamic density switching based on task complexity.
