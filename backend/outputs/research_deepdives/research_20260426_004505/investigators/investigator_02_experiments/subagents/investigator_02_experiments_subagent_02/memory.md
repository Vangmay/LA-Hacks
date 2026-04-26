# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Attempting to resolve the seed paper (Attention is All You Need) to establish a baseline for novelty research.


## Step 2: append_workspace_markdown

Repaired papers.md by adding the seed paper record.


## Step 3: paper_relevance_search

Starting precision search for Transformer architecture limitations, weaknesses, and bottlenecks to identify research gaps.


## Step 4: append_workspace_markdown

Added MTMixer paper to papers.md. It highlights the quadratic complexity vs linear complexity trade-off and Mamba's unidirectional scan limitation.


## Step 5: append_workspace_markdown

Repaired findings.md by adding the first finding regarding the complexity trade-off between Transformers and SSMs.


## Step 7: append_workspace_markdown

Repaired proposal_seeds.md by adding a seed focused on solving the unidirectional scan limitation of SSMs identified in MTMixer.


## Step 8: paper_relevance_search

Performing collision search for 'Bidirectional Selective SSMs' to check if the proposed mechanism (addressing Mamba's unidirectional scan) is already implemented or published.


## Step 9: append_workspace_markdown

Added Dual-path Mamba (2024) to papers.md. This is a direct collision with the 'Bidirectional SSM' idea, showing it's already used for speech separation.


## Step 10: append_workspace_markdown

Added BabyMamba-HAR (2026) to papers.md. It uses weight-tied bidirectional scanning, further confirming the bidirectional SSM trend.


## Step 11: append_workspace_markdown

Added finding regarding the emergence of bidirectional SSMs in specific domains, which provides context for refining the previous proposal seed.


## Step 12: paper_relevance_search

Pivoting from 'can we do bidirectional SSMs' (which is solved in domains) to 'can we do them efficiently/in a single pass' for general-purpose architectures.


## Step 13: append_workspace_markdown

Added Motion Mamba to papers.md. It uses a Bidirectional Spatial Mamba (BSM) block, confirming the trend of bidirectional SSMs in domain-specific tasks.


## Step 14: append_workspace_markdown

Added HSIDMamba to papers.md. It uses forward and backward scans for hyperspectral denoising, reinforcing the trend of multi-scan bidirectional SSMs in specialized domains.


## Step 15: append_workspace_markdown

Added HLX (2025) to papers.md. This highlights a second research direction: hardware-aware optimization for hybrid Transformer-Mamba models, focusing on memory traffic and compute utilization.


## Step 16: paper_relevance_search

Pivoting research toward 'asymmetric' or 'single-pass' bidirectional SSMs. The goal is to find a mechanism that provides bidirectional context without the $2\times$ computational overhead of standard bidirectional scanning, which is a clear gap in existing domain-specific implementations.


## Step 17: append_workspace_markdown

Added Vision Mamba (2024) to papers.md. This is a major collision as it presents a generic bidirectional Mamba backbone (Vim), proving that bidirectional SSMs are a viable path for general-purpose vision models, not just domain-specific ones.


## Step 18: paper_relevance_search

Searching for 'non-causal' state space models. 'Non-causal' is a technical term for bidirectional or globally-aware SSMs. This will help determine if the 'bidirectional' concept is being discussed under a different name and if true single-pass non-causal mechanisms exist.


## Step 19: append_workspace_markdown

Added VSSD (2024) to papers.md. It presents a very high-relevance collision: a non-causal SSD mechanism that modifies token-state interaction magnitudes. This suggests the 'bidirectional' problem is being attacked via structural mathematical changes to the SSD/Mamba-2 kernel, not just multiple scans.


## Step 20: append_workspace_markdown

Added finding regarding the vision-centricity of non-causal SSM research, which establishes a new direction: non-causal SSMs for language/LLMs.


## Step 22: paper_bulk_search

Semantic Scholar relevance search failed with a 500 error. Retrying with paper_bulk_search to continue the search for non-causal SSM applications in NLP.


## Step 23: paper_bulk_search

The previous specific bulk search returned no results. I will now attempt a broader query ('Mamba bidirectional language') to see if any non-causal/bidirectional work is being applied to language modeling.


## Step 24: append_workspace_markdown

Added PTM-Mamba to papers.md. It confirms that bidirectional Mamba is being applied to specialized language models (protein sequences), providing a non-vision example of the technology.


## Step 25: append_workspace_markdown

Added DiffuMamba (2025) to papers.md. This is a significant collision for the 'language modeling + bidirectional' direction, showing that bidirectional Mamba is already being used as a backbone for diffusion-based language models.


## Step 26: paper_relevance_search

Attempting to find if the 'auxiliary patch swapping' mechanism from SF-Mamba (vision) has been transferred to language modeling (token swapping/permutation) to achieve single-pass bidirectional context in SSMs.


## Step 27: paper_bulk_search

The specific search for 'token swapping' failed. I will now attempt a broader search for 'Mamba bidirectional text' to see if any non-causal or bidirectional text-based Mamba models are emerging, which would help refine the novelty of my language-focused proposal.


## Step 28: append_workspace_markdown

Added InfiniMotion (2024) to papers.md. This is a high-value collision: it uses 'Bidirectional Mamba Memory' for long-sequence motion generation, proving that bidirectional SSMs are moving into sequence modeling domains (beyond vision) to address long-context limitations in Transformers.


## Step 29: paper_relevance_search

Refining the research direction. I have seen bidirectional Mamba in vision, protein, and motion, but I'm searching specifically for 'prefix-LM' or 'non-autoregressive' Mamba applications in natural language to see if the general LLM gap is truly unaddressed.


## Step 30: append_workspace_markdown

Added Text-to-Talk (2025) to papers.md. This is a key collision: it uses bidirectional modeling for non-autoregressive audio spans within a multimodal framework. It confirms that the need for bidirectional context in NAR tasks is being addressed, but currently through modality-specific mechanisms (e.g., bidirectional audio, causal text) rather than a single, unified non-causal SSM backbone for all tokens.


## Step 31: paper_relevance_search

Searching for 'prefix-LM' or 'prefix language model' applications with Mamba. Prefix-LMs are a standard way to allow bidirectional context in LLMs (e.g., during pre-training or for specific tasks), so seeing if Mamba has been adapted for this will help determine if a 'non-causal' SSM gap actually exists for the LLM paradigm.


## Step 32: append_workspace_markdown

Added RedLLM (2025) to papers.md. This provides critical context: the encoder-decoder architecture (using prefix-LM/bidirectional processing) is still a highly competitive paradigm for LLMs. This strengthens the argument that there is a clear architectural slot for efficient, non-causal (bidirectional) modeling in the LLM space, which SSMs are perfectly positioned to fill.


## Step 33: append_workspace_markdown

Added finding regarding collision analysis. I've identified that the 'bidirectional SSM' idea has high collision risk in specialized domains, directing the novelty focus toward efficiency (single-pass) and general-purpose LLM applicability.


## Step 34: append_workspace_markdown

Added a new, refined proposal seed to proposal_seeds.md. This seed pivots from a general 'bidirectional SSM' idea (which has high collision risk in vision) to a 'single-pass non-causal SSM' specifically designed for the prefix-LM paradigm in LLMs, targeting the efficiency/performance gap identified in my collision analysis.
