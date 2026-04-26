# Memory

## Stable Facts

## Search Threads

## Candidate Papers

## Open Questions

## Contradictions

## Hand-Off Summary



## Step 1: resolve_arxiv_paper

Resolving seed paper Attention is All You Need (arXiv:1706.03762) to start investigation.


## Step 2: append_workspace_markdown

Repaired papers.md by adding the seed paper record.


## Step 3: paper_relevance_search

Starting technical search for transformer attention complexity and architecture limitations to identify potential novelty triggers.


## Step 4: append_workspace_markdown

Recorded Echo State Transformer (EST) paper; it represents a major architectural departure from the seed by using fixed-size reservoir memory to achieve linear complexity.


## Step 5: append_workspace_markdown

Repaired findings.md by adding a finding regarding linear complexity via reservoir-based attention.


## Step 6: append_workspace_markdown

Populated proposal_seeds.md with a promising seed: the Semantic Reservoir Transformer (SRT), addressing the scaling gap identified in the EST paper.


## Step 7: paper_relevance_search

Executing the required next search for the SRT proposal seed: investigating existing work on reservoir computing and attention in the context of NLP.


## Step 8: append_workspace_markdown

Recorded 'Reservoir Computing as a Language Model' (2025). This paper directly addresses the attention-reservoir hybrid idea, serving as a collision check for the SRT seed.


## Step 9: append_workspace_markdown

Recorded 'Reservoir Computing as a Language Model' (2025). This paper uses attention for the readout, which allows for a pivot in the SRT proposal: moving attention from the readout to the reservoir's internal state updates.


## Step 10: append_workspace_markdown

Added a finding regarding the distinction between readout-based and state-based reservoir attention, identifying a specific technical gap for the SRT proposal.


## Step 11: append_workspace_markdown

Added a refined proposal seed (ASUR) that pivots from the previous SRT seed, moving the novelty from 'semantic reservoir' to 'attentional state-update mechanism' based on the finding that existing RC-NLP work only uses attention for the readout.


## Step 12: paper_relevance_search

Executing the required next search for the ASUR proposal seed: checking for existing work on learned reservoir dynamics or attentional recurrent state updates to ensure novelty.


## Step 13: append_workspace_markdown

Recorded Maslennikov (2026), which provides a strong theoretical reason to move from passive to 'sculpted' (attentional) reservoir dynamics, reinforcing the ASUR proposal.


## Step 14: append_workspace_markdown

Added a finding distinguishing between external context modulation (RL-based) and the proposed internal attentional sculpting (ASUR), providing a clearer theoretical boundary for the novelty of the ASUR seed.


## Step 15: append_workspace_markdown

Recorded Tomihari & Karakida (2025); its focus on the dynamical systems analysis of attention provides a potential theoretical toolset for validating the stability of the ASUR mechanism.


## Step 16: paper_relevance_search

Executing a targeted search for 'gated reservoir computing' to check if the proposed attentional state-updating mechanism (ASUR) has already been implemented in existing literature.


## Step 17: append_workspace_markdown

Recorded 'leaky reservoir computing' (2025). This highlights that while 'gating' exists in the form of leaky integrators, it is typically a fixed/structural property, further supporting the novelty of the ASUR proposal's 'learned attentional sculpting'.


## Step 18: paper_relevance_search

Performing a comparison search between State Space Models (Mamba) and Reservoir Computing to delineate the specific technical niche for the ASUR proposal.


## Step 19: paper_relevance_search

The search for 'Mamba vs Reservoir Computing' returned irrelevant geological results. I will pivot to searching for 'State Space Models' (SSM) specifically in relation to 'reservoir computing' and 'linear attention' to find a better comparison baseline.


## Step 20: paper_bulk_search

Pivoted search to 'State Space Models AND reservoir computing' to find a meaningful comparison between modern linear-complexity architectures (like Mamba) and Reservoir Computing, which will help refine the ASUR proposal's position.


## Step 21: append_workspace_markdown

Recorded Liu & Parhi (2023); their work on 'dynamic reservoirs' through physical cascading provides a precedent for moving beyond static reservoirs, but reinforces the gap: their dynamics are structural, whereas the ASUR proposal targets sequence-dependent, attentional dynamics.


## Step 22: get_paper_metadata

Investigating HA-ESNet (2025) to determine if its attention mechanism is applied to the reservoir state or the readout, which is crucial for the ASUR novelty test.


## Step 23: paper_relevance_search

Performing a final precision check for 'linear attention reservoir computing' to ensure the ASUR proposal's technical mechanism hasn't already been unified under this specific term.
