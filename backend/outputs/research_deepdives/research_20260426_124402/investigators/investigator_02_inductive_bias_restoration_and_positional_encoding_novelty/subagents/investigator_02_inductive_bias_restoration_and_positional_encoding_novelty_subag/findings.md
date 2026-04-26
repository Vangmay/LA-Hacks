# Findings



## Finding: Search Gap for RoPE Limitations

- Claim: Direct bulk search for 'limitations of RoPE long context' yielded zero results in Semantic Scholar's high-citation index, suggesting a potential gap in how 'limitations' are catalogued or a need for more nuanced query terms like 'length extrapolation' or 'out-of-distribution sequence length'.
- Confidence: low
- Evidence:
  - paper_bulk_search query: "limitations of RoPE 'Rotary Positional Embedding' long context" [2022-]
- Why it matters: Identifying why specific failure-mode keywords fail to return results helps refine the 'Void Cartographer' approach. It may suggest that critiques are embedded within 'extension' papers (e.g., LongLoRA, YaRN) rather than being titled as 'limitations'.
- Caveat: The search term was highly specific with double-quoted phrases which may have overly constrained the results; need to relax lexical constraints.


## Finding: Intentional Removal of Local Inductive Biases

- **Claim**: The original Transformer architecture explicitly replaces structural inductive biases (recurrence for sequentiality and convolution for translation equivariance) with a global self-attention mechanism, necessitating the use of absolute positional encodings.
- **Confidence**: High
- **Evidence**: Vaswani et al. (2017), 'Attention is All you Need'. The paper states it dispenses with recurrence and convolutions entirely.
- **Why it matters**: From a signal processing perspective, this is a radical departure. Absolute positional encodings (APE) used in the seed paper are not naturally translation-invariant. This created a 'gap' in the model's ability to handle shifted sequences efficiently, which motivated several years of follow-up work on Relative Positional Encodings (RPE) to restore the translation-invariant properties typical of classical filters.
- **Caveat**: While the lack of APE invariance is mathematically clear, the impact on practical performance is often mitigated by the model 'learning' these symmetries when data is abundant.


## Finding: Explicit PE as an Extrapolation Barrier

- Claim: Recent work (Zhang et al., 2025; LEDiT) makes the strong claim that explicit positional encodings (like RoPE) are fundamentally at odds with length/resolution extrapolation because they force the model to handle previously unseen coordinate values.
- Confidence: medium
- Evidence:
  - LEDiT (2025): 'The primary obstacle is that the explicit positional encodings (PE), such as RoPE, need extrapolating to unseen positions which degrades performance.'
- Why it matters: This identifies a major research gap in the 'inductive bias restoration' theme. If causal attention already provides implicit global position, the explicit addition of RoPE may actually be injecting 'noise' or 'overfitting signal' that prevents scaling.
- Caveat: The implicit position hypothesis for causal attention may depend on specific architectural choices (e.g., softmax behavior or specific normalization) and may not generalize trivially from DiT to LLMs.


## Finding: Convergence of Transformers and SSMs via Positional Inductive Bias

- **Claim**: Recent work on 2-D State Space Models (SSMs) and Vision Transformers (ViTs) shows that 'pos-encoding-free' performance is achievable by introducing layers that satisfy translation and permutation invariance explicitly.
- **Confidence**: Medium-High
- **Evidence**: Baron et al. (2023), '2-D SSM: A General Spatial Layer for Visual Transformers'. The paper demonstrates that vision transformers can function effectively without positional encoding if they use a layer with strong 2-D inductive bias (dynamic spatial locality and translation invariance).
- **Why it matters**: This validates the 'lexical archeologist' hypothesis: the removal of inductive bias in the original Transformer (2017) is being systematically reversed. By moving toward SSM-based layers, researchers are essentially re-implementing the properties of classical shift-invariant filters in a differentiable, dynamic framework.
- **Caveat**: Most of these 'restoration' methods involve adding specialized layers (like convolutions or SSMs) rather than modifying the self-attention mechanism itself to be naturally equivariant.


## Finding: Convergence of Implicit Position Evidence

- Claim: There is a multi-modal convergence (2022 NLP, 2024 Meteorology, 2025 Vision) suggesting that causal attention acts as an 'emergent' positional encoding by allowing tokens to infer their index based on the number of predecessors.
- Confidence: high
- Evidence:
  - Haviv et al. (2022): Showed GPT-style models without PEs are competitive and learn absolute positions via causal masking.
  - LEDiT (2025): Showed Diffusion Transformers extrapolate better *without* explicit PEs like RoPE because explicit PEs create 'unseen coordinate' out-of-distribution (OOD) failures.
  - DTCA (2024): Leveraged causal attention in meteorology for spatiotemporal queries.
- Why it matters: This contradicts the 'necessity' assumption of Vaswani et al. (2017) and suggests that the modern industry standard (RoPE) may be over-determined, providing redundant global info but essential local bias.
- Caveat: The implicit signal is likely 'coarse' (low frequency). This explains why RoPE helps in practice—it provides the high-frequency 'sharpness' that counting predecessors lacks.
