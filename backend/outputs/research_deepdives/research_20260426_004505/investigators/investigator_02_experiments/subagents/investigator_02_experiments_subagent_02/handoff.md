# Hand-Off

## Research Summary
I have investigated the architectural evolution from Transformers to State-Space Models (SSMs), specifically looking for novelty in the tension between quadratic complexity and bidirectional context modeling. 

Initially, I explored 'Bidirectional SSMs' as a way to address the unidirectionality of Mamba. However, collision searches (Dual-path Mamba, Vision Mamba, BabyMamba-HAR, etc.) revealed that bidirectional scanning is already an active area in domain-specific applications (vision, speech, genomics). Furthermore, non-causal research (VSSD, SF-Mamba) is heavily skewed towards vision tasks.

## Key Findings
- **Complexity Tension**: The core driver is the trade-off between the quadratic complexity of attention and the linear complexity/unidirectional scan of SSMs.
- **Collision Identified**: 'Bidirectional Mamba' is a known concept in domain-specific contexts (e.g., Vision Mamba, Dual-path Mamba), meaning simple dual-pass scanning is not a novel contribution.
- **The Research Gap**: There is a significant lack of research into **single-pass, non-causal SSM mechanisms** applied to **language modeling/LLMs**. While the 'prefix-LM' paradigm (encoder-decoder) is proving highly effective for LLMs (e.g., RedLLM), the underlying kernels are still predominantly causal/autoregressive.

## Top Papers & Why They Matter
- **Attention is All You Need (2017)**: The seed; established the Transformer baseline.
- **Vision Mamba (2024)**: Demonstrates that bidirectional SSMs can serve as generic vision backbones.
- **VSSD (2024)**: Provides a mathematical hint for non-causality via modifying the SSD (State Space Duality) kernel, though it is vision-centric.
- **RedLLM (2025)**: Validates the strength of prefix-language modeling (non-causal) for LLMs, providing the architectural motivation for a non-causal SSM replacement.
- **MTMixer (2025)**: Shows the current trend of hybridizing SSMs and Transformers to balance complexity and context.

## Proposal Seeds

### 1. Single-Pass Non-Causal SSMs for Efficient Prefix-Language Modeling
- **Core Idea**: Develop an SSM kernel that achieves non-causal/bidirectional context in a single scan, specifically optimized for the prefix-dependency patterns in LLM pre-training.
- **Evidence Basis**: The performance of prefix-LMs (RedLLM) vs. the efficiency of SSMs, and the current vision-centricity of non-causal SSM research (VSSD).
- **Collision Risk**: Medium (VSSD exists for vision; the novelty lies in the single-pass mechanism for 1D language sequences).
- **Confidence**: Medium
- **Next Search**: Mathematical feasibility of single-scan non-causal kernels and existence of 'prefix-Mamba' implementations.

## Recommended Next Steps
1. **Mathematical Formalization**: Explore if the VSSD approach (discarding magnitude in SSD) can be adapted for 1D language sequences without losing the semantic precision required for text.
2. **Benchmark Design**: Design a 'Prefix-SSM' benchmark that tests perplexity and throughput on prefix-completion tasks compared to standard causal Mamba and attention-based prefix-LMs.
3. **Collision Check**: Perform a targeted search for 'non-causal state space models for language' to ensure no recent LLM-centric non-causal SSM papers have been published.