# Papers



## Paper: Attention is All you Need
- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: The seed paper itself
- Why it matters: Introduced the Transformer architecture, which relies entirely on attention mechanisms, dispensing with recurrence and convolutions. This revolutionized sequence transduction tasks.
- Caveat: While foundational, the quadratic complexity of self-attention w.r.t. sequence length is a known bottleneck addressed by many follow-up works.


## Paper: In Transformer We Trust? A Perspective on Transformer Architecture Failure Modes
- Paper ID: 96c6404f0f38b50299017be181a50d6c51e6480d
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct critique of the Transformer architecture's reliability.
- Why it matters: Provides a systematic review of failure modes across NLP, CV, and scientific computing (robotics, medicine, etc.), specifically focusing on interpretability, robustness, and structural vulnerabilities.
- Caveat: As a 2026 paper (likely a preprint/early access), its findings represent the current SOTA critique of the architecture.


## Paper: EEG Emotion recognition based on attention mechanism fusion transformer network
- Paper ID: 6363872d053e028a2e3123ed913a7f17ba475ecd
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Uses a dual-encoder Transformer (time-step and channel attention) for EEG signal processing.
- Why it matters: Demonstrates the use of multi-faceted attention (temporal and spatial/channel) for complex physiological signals, a key component of the proposed diagnostic framework.
- Caveat: Focuses on performance (accuracy) for emotion recognition rather than structural robustness or stability under noise/perturbations.


## Paper: Sensitivity Analysis of Word Importance using GPT Model: A Ranking XAI Approach with Attention Weights and KL Divergence
- Paper ID: f88c5105e8806105d792d077527ad32bcdd973e7
- Year: 2024
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Collision/Prior work on sensitivity analysis.
- Why it matters: Uses sensitivity analysis and attention weights to rank word importance (XAI). While it uses similar technical components, it focuses on *interpretability* (what is important) rather than *structural stability* (how much weights fluctuate under noise).
- Caveat: Primarily focused on NLP and generative models (GPT).


## Paper: Your Attention Matters: to Improve Model Robustness to Noise and Spurious Correlations
- Paper ID: f0daa947dd63f1d05412e20d30399aa18345a3f7
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Collision/Prior work on attention mechanism robustness.
- Why it matters: Evaluates different attention variants (Softmax, Sigmoid, Linear, etc.) for robustness to data corruption in Vision Transformers. It suggests that 'Doubly Stochastic' attention is more robust, providing a benchmark for how attention mechanisms themselves respond to noise.
- Caveat: Focuses on selecting/designing better attention mechanisms for robustness, rather than using attention weight stability as a diagnostic metric for safety-critical deployment.


## Paper: Stabilizing Transformer Training by Preventing Attention Entropy Collapse
- Paper ID: 385c363ea8e450f362d389f401beaeb5b42a0022
- Year: 2023
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision on 'attention entropy'.
- Why it matters: It uses attention entropy as a proxy for *training stability* (preventing collapse during training). While technically related, it differs from the proposed seed which uses attention stability/variance as a *diagnostic metric for deployment safety* in response to input perturbations.
- Caveat: Focus is on optimization and training dynamics, not deployment-time robustness to environmental noise.
