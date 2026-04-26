# Papers

## Paper: Griffin: Mixing Gated Linear Recurrences with Local Attention for Efficient Language Models
- Paper ID: d53fe76bd2795a19ddf52d012917782f6f6f2c1e
- Year: 2024
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: descendant_hybrid
- Why it matters: Demonstrates the necessity of re-introducing local attention to linear recurrences (Hawk) to match Transformer performance on downstream tasks and extrapolate effectively on long sequences.
- Caveat: Suggests attention is a mandatory 'bandage' for current recurrence-based SOTA models.

## Paper: Revisiting associative recall in modern recurrent models
- Paper ID: 91fd141738858eff0f31ae5db208f269e4d3f982
- Year: 2025
- Source bucket: recent_critiques_and_scaling_barriers
- Found by: paper_relevance_search
- Relation to seed: descendant_optimization_study
- Why it matters: Found that Mamba's failure on Associative Recall is largely an optimization problem (learning rate sensitivity) rather than an architectural inability.
- Caveat: The model remains more fragile than Transformers regarding hyperparameter tuning.

## Paper: Tiny Recursive Reasoning with Mamba-2 Attention Hybrid
- Paper ID: 45ecf6033663a38e661c2ceb9c1225413a6aba71
- Year: 2026
- Source bucket: same_task_competitors
- Found by: paper_relevance_search
- Relation to seed: descendant_hybrid_reasoning
- Why it matters: Documents a 'coverage-vs-selection' gap where SSM hybrids can generate correct reasoning candidates but fail to rank them as top-1 correctly compared to Transformers.
- Caveat: Only tested on tiny 7M parameter models; scaling laws for this gap are not yet fully understood.

## Paper: Attention is All you Need
- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: self
- Why it matters: The fundamental transformer baseline that established the global-attention standard which SSMs and hybrids are designed to replace for efficiency reasons.
- Caveat: SOTA at publication but quadratic complexity is the primary limitation being researched today.
