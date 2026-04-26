# Papers



## ## Seed Paper

- **Title**: Attention is All you Need
- **ID**: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- **Year**: 2017
- **Source**: Seed
- **Note**: The seminal Transformer paper. Focus on its core components: Multi-Head Attention (MHA), Positional Encoding, and Layer Normalization.


## ## Attention Head Ablation (CLIP)

- **Title**: Not All Attention Heads Are What You Need: Refining CLIP's Image Representation with Attention Ablation
- **ID**: fe75d7c67788f39803ae39842d3b45bc5c34ff30
- **Year**: 2025
- **Source**: relevance_search
- **Note**: Investigates detrimental attention heads in CLIP. Suggests that some heads are harmful to representations. This is a key empirical clue for head-specific functionality.


## ## LayerNorm Redundancy (GPT-2)

- **Title**: Transformers Don't Need LayerNorm at Inference Time: Scaling LayerNorm Removal to GPT-2 XL and the Implications for Mechanistic Interpretability
- **ID**: 52be61c3edaa54b568805db55a748ba6d8159587
- **Year**: 2025
- **Source**: relevance_search
- **Note**: Demonstrates that LN layers can be removed from GPT-2 models with minimal loss. Suggests LN's role is likely training-related rather than fundamental to the inference-time information transduction logic.


## ## Information-Theoretic Transformer Analysis

- **Title**: Information-Theoretical Analysis of a Transformer-Based Generative AI Model
- **ID**: f1022d780a8c31e10094ae882c0e1feb79759b7b
- **Year**: 2025
- **Source**: relevance_search
- **Note: Uses Information Theory and Information Geometry to quantify information transmission and word relationships in Transformer layers. Potentially useful for building a formal model of why components like LayerNorm or Attention are required for specific information properties.
