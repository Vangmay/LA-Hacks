# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Resolving the seed paper 'Attention is All You Need' to get its canonical Semantic Scholar ID and metadata.


## Step 2: append_workspace_markdown

Recorded the seed paper 'Attention is All You Need' into papers.md to establish the baseline quadratic complexity bottleneck.


## Step 1: resolve_arxiv_paper

Initializing research for 'Scaling Beyond Quadratic Complexity'. Starting by resolving the seed paper 'Attention is All You Need' (1706.03762) to establish the canonical baseline and transition into the 'Pedigree and Limitation Auditor' search thread, focusing on the historical context of sub-quadratic alternatives.


## Step 3: write_workspace_markdown

Repaired papers.md to include the full structured record for the seed paper, satisfying the audit requirements for Paper ID, Year, Source bucket, Found by, Relation to seed, Why it matters, and Caveat.


## Step 2: append_workspace_markdown

Verified seed paper metadata and initialized papers.md to satisfy the artifact contract. Preparing to investigate the pedigree of linear scaling methods by searching for early 'linear attention' and 'sub-quadratic' critiques.


## Step 3: append_workspace_markdown

Initialized findings.md with the baseline complexity claim. Proceeding to search for ancestral linear-attention papers (e.g., Fast autoregressive transformers, Linear Transformers) and comparative critiques.


## Step 4: paper_relevance_search

Searching for recent (2024-2025) sub-quadratic sequence models and State Space Model (SSM) variations that specifically address the VRAM bottlenecks identified in the seed paper. Looking for frontier alternatives to standard self-attention.


## Step 5: append_workspace_markdown

Created the first proposal seed based on the Hydra paper (Hwang et al. 2024) and the Image/Video Diffusion SSM paper (Hong et al. 2025), focusing on VRAM-efficient bidirectional scaling.


## Step 4: append_workspace_markdown

Initialized proposal_seeds.md with a speculative idea regarding dynamic kernels to address the expressivity gap in linear scaling models. This satisfies the artifact documentation requirement.


## Step 6: append_workspace_markdown

Added the Hydra paper to papers.md. This paper is the primary technical basis for the proposed bidirectional SSM research direction.


## Step 5: paper_relevance_search

Executing a precision-oriented search for critiques and limitations of sub-quadratic 'efficient' Transformers. This query is designed to find papers that stress-test the claims of 'linear attention' and identify where these methods fail to match the expressivity of the original O(N^2) mechanism.


## Step 6: append_workspace_markdown

Added SCOUT (2025) to papers.md. This paper identifies the failure of purely linear models like Mamba to retain detailed information from distant tokens, motivating the transition toward hybrid 'Segment Compression' architectures.


## Step 7: google_scholar_search

Searching for 2024-2025 comparative analyses of VRAM usage between State Space Models (SSMs) and Transformers. I want to identify specific sequence lengths where SSMs actually provide a practical win on standard GPU hardware, vs where hardware-specific overheads (like FFT or scan) might negate the theoretical O(N) complexity.


## Step 7: append_workspace_markdown

Recorded finding regarding information decay in linear models based on recent 2025 evidence (SCOUT, LAWCAT). This reinforces the 'Pedigree and Limitation Auditor' view that sub-quadratic efficiency often comes with hidden expressivity costs.


## Step 8: append_workspace_markdown

Integrated SCBench findings into findings.md. SCBench provides high-confidence evidence that KV cache is the killer bottleneck for Transformers, further justifying the search for SSM-based alternatives in the novelty ideation thread.


## Step 9: append_workspace_markdown

Appended SCBench into papers.md to record the evidence for the KV cache bottleneck, which is the cornerstone for the 'VRAM-efficient bidirectional mixing' proposal seed.


## Step 8: paper_relevance_search

Searching for the 'linear attention' ancestry (Katharopoulos et al., 2020) to audit the pedigree of current sub-quadratic ideas like GLA and Mamba. I want to see if the limitations identified in 2020 are still the same ones appearing in 2025 preprints.


## Step 9: append_workspace_markdown

Added the 2020 Katharopoulos paper to papers.md. This establishes the baseline for 'linear attention' ancestry. I will now perform a citation search to see how modern sub-quadratic papers (like GLA or Mamba) justify their departure from this specific 2020 lineage.


## Step 10: append_workspace_markdown

Synthesized a second, more specific proposal seed targeting video diffusion by combining 'Gamba bottleneck' and 'Hydra' concepts to solve the VRAM-bound video scaling problem.


## Step 11: paper_relevance_search

The get_citations call for Katharopoulos (2020) failed with a 400 error (potentially due to the tldr field or paper ID format in the citations endpoint). I am switching to a relevance search for papers that specifically critique linear attention kernels or compare them to Gated Linear Attention (GLA) and Mamba to find the modern technical pivot point.


## Step 12: append_workspace_markdown

Recorded Preconditioned DeltaNet (2026). This paper provides a theoretical link between linear attention and online least squares, specifically identifying 'curvature neglect' as a limitation of previous sub-quadratic methods. This aligns with the 'Auditor' taste for finding missing mathematical assumptions.


## Step 13: append_workspace_markdown

Distilled the Test-Time Regression (TTR) framework into findings. This provides a theoretical 'pedigree' for why linear attention underperformed and how modern preconditioning (2026) aims to fix it.


## Step 14: paper_relevance_search

Investigating the hidden VRAM costs and initialization overhead of preconditioned linear attention compared to FlashAttention. I want to see if the 'curvature-aware' improvements (2026) introduce a new memory bottleneck that makes the sub-quadratic complexity claim less practically useful for real-world scaling.


## Step 15: paper_relevance_search

The previous search for preconditioned linear attention VRAM yielded zero results, likely due to the extreme recency of the terminology (2026). I am broadening to an empirical comparison of Mamba-2 (the state-of-the-art sub-quadratic baseline) against FlashAttention to uncover the 'hidden cost' of recurrent states versus the optimized quadratic baseline, satisfying the Auditor taste for detecting real-world trade-offs.
