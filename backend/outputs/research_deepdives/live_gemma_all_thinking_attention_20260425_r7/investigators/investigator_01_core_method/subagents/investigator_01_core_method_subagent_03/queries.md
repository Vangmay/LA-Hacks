# Queries

## Resolution
- **Query**: `resolve_arxiv_paper(arxiv_url='https://arxiv.org/abs/1706.03762')`
- **Result**: Successfully resolved to `204e3073870fae3d05bcbc2f6a8e263d9b72e776` (Attention is All You Need).

## Reference Search

- **Query**: `get_references(paper_id='204e3073870fae3d05bcbc2f6a8e263d9b72e776', limit=50, fields='...')`
- **Result**: Retrieved 50 references. Identified key mechanistic competitors: RNN-based attention (summarization), CNN-based seq2seq, and structured self-attention for embeddings.


## Relevance Search: Efficient Attention

- **Query**: `paper_relevance_search(query='efficient attention linear attention sub-quadratic transformer', limit=20)`
- **Result**: Found papers on hybrid attention (Attention Surgery), window attention (SWAT), and distillation-based linearization. Identified a tension between the expressivity of softmax attention and the efficiency of linear approximations.
