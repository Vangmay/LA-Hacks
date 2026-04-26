# Papers



## Paper: Attention is All you Need
- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: seed_paper
- Why it matters: Foundational architecture introducing the Transformer, dispensing with recurrence and convolution in favor of self-attention mechanisms.
- Caveat: N/A


## Paper: Sequence to Sequence Learning with Neural Networks
- Paper ID: cea967b59209c6be22829699f05b8b1ac4dc092d
- Year: 2014
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: foundational ancestor
- Why it matters: Established the encoder-decoder framework for sequence-to-sequence tasks, which the Transformer later optimized by removing recurrence.
- Caveat: Relies on RNNs, which are harder to parallelize.

## Paper: Neural Machine Translation by Jointly Learning to Align and Translate
- Paper ID: fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5
- Year: 2014
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: foundational ancestor
- Why it matters: Introduced the attention mechanism in NMT, a key component that the Transformer later used as its primary structural driver.
- Caveat: Still uses recurrent architectures.

## Paper: Long Short-Term Memory
- Paper ID: 2e9d221c206e9503ceb452302d68d10e293f2a10
- Year: 1997
- Source bucket: foundational_references
- Found by: get_references
- Relation to seed: technical ancestor
- Why it matters: Seminal work on handling long-term dependencies in sequences, which was the central problem Transformers sought to solve more efficiently.
- Caveat: Sequential nature limits parallelization.


## Paper: EEViT: Efficient Enhanced Vision Transformer Architectures with Information Propagation and Improved Inductive Bias
- Paper ID: 090f74402c3b960b8d31b212609a4c84ff99d6f3
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up/competitor
- Why it matters: Explicitly targets the two main weaknesses identified: lack of inductive bias (compared to CNNs) and quadratic computational complexity. Proposes EEViT-PAR and EEViT-IP architectures.
- Caveat: Recent (2025) work; validation on broad datasets needed.

## Paper: Multi-Scale Transformer Architecture for Accurate Medical Image Classification
- Paper ID: c6fd6846e0c94f93717529724e4f2b052221add3
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up
- Why it matters: Uses multi-scale feature fusion to address local/global feature extraction and improve interpretability in medical imaging.
- Caveat: Domain-specific (medical).


## Paper: Can We Achieve Efficient Diffusion without Self-Attention? Distilling Self-Attention into Convolutions
- Paper ID: ef8ec849bbe77b96fc7b700430cb679fa26977ed
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (on diffusion)
- Why it matters: Finds that self-attention in pre-trained diffusion models often exhibits localized patterns resembling convolutions. Proposes \(\Delta\)ConvFusion to replace self-attention with Pyramid Convolution Blocks, achieving massive efficiency gains (6929x) without compromising fidelity.
- Caveat: Specific to diffusion models.

## Paper: ConvDeiT-Tiny: Adding Local Inductive Bias to DeiT-Ti for Enhanced Maize Leaf Disease Classification
- Paper ID: d56ba1f607998273da3e61aa1eb10f33e1682dc5
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (hybrid approach)
- Why it matters: Addresses the weak inductive bias of ViTs by placing depthwise convolutions in parallel with multi-head self-attention in early blocks, fusing them via MLP.
- Caveat: Hybrid approach (not purely attention-based).

## Paper: Towards Exact Computation of Inductive Bias
- Paper ID: a16cec5fc1f9209c275b347fb56a2ea28f722540
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: theoretical background
- Why it matters: Proposes an information-theoretic method to quantify the amount of inductive bias required for generalization on a task, providing a metric to compare architectures.
- Caveat: Highly theoretical.


## Paper: Algorithm to Compilation Co-design: An Integrated View of Neural Network Sparsity
- Paper ID: 009db3b83a2bbb97cc4024d3820fc5c562e7da69
- Year: 2021
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: technical ancestor/efficiency study
- Why it matters: Investigates the relationship between model sparsity (pruning) and hardware execution. Crucially finds that for BERT attention weights, the end-to-end optimal block sparsity shape in a CPU context is a linear $32 \times 1$ block rather than a standard square block.
- Caveat: Focused on CPU inference/TVM compiler context.


## Paper: Forgetting to Forget: Attention Sink as A Gateway for Backdooring LLM Unlearning
- Paper ID: 33eb524517cd5fc1a0eba5afcf9ed9f037650986
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (security/unlearning)
- Why it matters: Uncovers a link between backdoor efficacy and the attention sink phenomenon. It shows that placing triggers at sink positions (shallow tokens) enhances backdoor persistence during unlearning.
- Caveat: Security-focused context.

## Paper: See What You Are Told: Visual Attention Sink in Large Multimodal Models
- Paper ID: 5c308e16788bb80d9a6292c05448d319928f0be5
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (multimodal)
- Why it matters: Identifies a 'visual attention sink' in LMMs where irrelevant visual tokens receive disproportionately high attention. Proposes Visual Attention Redistribution (VAR) to recycle this surplus attention budget.
- Caveat: Multimodal/Vision-Language specific.

## Paper: What are you sinking? A geometric approach on attention sink
- Paper ID: 5958e8a8010d39947104efe599b676b9e1d0e040
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: theoretical background
- Why it matters: Provides a geometric interpretation of attention sinks as the establishment of 'reference frames' (centralized, distributed, or bidirectional) to anchor representational spaces. Suggests AS is a fundamental principle, not just an artifact.
- Caveat: Theoretical/Geometric.

## Paper: EDIT: enhancing vision transformers by mitigating attention sink through an encoder-decoder architecture
- Paper ID: 9736b0e9696d6515c05feb6f5213ba570c4427cf7
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (mitigation/architecture)
- Why it matters: Addresses the [CLS] token attention sink in ViTs by proposing a layer-aligned encoder-decoder architecture (EDIT) to improve visual feature extraction.
- Caveat: Architecture-specific mitigation.


## Paper: Vision Transformers Need Registers
- Paper ID: 10bd38673951f5d7729568284093cbd80482ab16
- Year: 2023
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (mitigation/artifact identification)
- Why it matters: Identifies high-norm tokens (artifacts) in ViT feature maps that are repurposed for internal computations. Proposes adding 'register' tokens to the input sequence to absorb these artifacts, leading to smoother feature/attention maps.
- Caveat: Requires retraining with additional tokens.

## Paper: Vision Transformers Don't Need Trained Registers
- Paper ID: 5312d8bf0cd7e8dcb75b459e02537049bb763ec4
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (training-free mitigation)
- Why it matters: Proposes a training-free approach to mitigate register artifacts by shifting high-norm activations from discovered 'register neurons' into an additional untrained token at test-time.
- Caveat: Test-time intervention.

## Paper: Vision Transformers Need More Than Registers
- Paper ID: 8029f812c7083ccffbd52e65aeeabbb5907d809e
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: contemporary follow-up (alternative mechanism)
- Why it matters: Argues artifacts arise from 'lazy aggregation behavior' where background patches are used as shortcuts for global semantics. Proposes selective feature integration into the [CLS] token instead of just adding registers.
- Caveat: Focuses on semantic shortcutting.
