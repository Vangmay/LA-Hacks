# Proposal Seeds



## Proposal Seed: Bidirectional Selective SSMs for Global Context

- Status: raw
- Originating taste: Gap Miner
- Seed-paper hook: Mamba's unidirectional scan limits comprehensive context integration.
- Evidence trigger: MTMixer (2025) explicitly notes that while Mamba has linear complexity, its unidirectional scan limits spatial context integration.
- Candidate novelty: Instead of interleaving layers (which keeps the SSM layers unidirectional), develop a mechanism where the SSM layer itself is inherently bidirectional or multi-directional while maintaining linear-time complexity.
- Technical mechanism: Implementation of a bidirectional selective scan (similar to S4/S6 but with a learned bidirectional gating mechanism) or a multi-directional state-space layer that avoids the quadratic cost of full self-attention.
- Closest prior-work collision: MTMixer (uses interleaving), standard Mamba (unidirectional).
- Closest future-work collision: Integrated bidirectional SSM architectures.
- Minimum validation: Evaluate a hybrid model with a 'bidirectional SSM' module vs. a standard Mamba-Transformer hybrid on long-sequence, high-resolution tasks (e.g., high-res remote sensing or long-context text).
- Falsification risk: Bidirectional scanning might re-introduce quadratic complexity or significantly increase the constant factor in linear time, negating the efficiency gain.
- Why this is not generic: It targets the specific structural deficiency (unidirectionality) of the most promising linear-time alternatives identified in 2025 literature.
- Confidence: medium
- Required next search: Search for 'bidirectional selective state space models' or 'bidirectional Mamba' to check for existing implementations.


## Proposal Seed: Single-Pass Non-Causal SSMs for Efficient Prefix-Language Modeling

- Status: promising
- Originating taste: Gap Miner
- Seed-paper hook: The efficiency/performance gap between causal SSMs and the high-performing non-causal prefix-LM (encoder-decoder) models like RedLLM.
- Evidence trigger: VSSD (2024) shows non-causality is possible via mathematical modification of SSD, but it is vision-centric. RedLLM (2025) shows prefix-LM (encoder-decoder) is a highly viable and competitive LLM paradigm.
- Candidate novelty: Moving from multi-scan/dual-pass bidirectional SSMs (which double the computational overhead) to a single-pass non-causal SSM mechanism specifically designed for the prefix-dependency patterns of LLM pre-training.
- Technical mechanism: A single-scan SSM where the state update incorporates a mechanism to capture 'future' context (relative to the current token) without a full second pass. This could involve a learned non-causal dependency or a modified kernel (inspired by VSSD's magnitude-weighting) optimized for 1D text sequences and prefix-LM workloads.
- Closest prior-work collision: VSSD (vision-centric), MTMixer (interleaved), Vision Mamba (multi-scan/dual-pass), RedLLM (Transformer-based prefix-LM).
- Closest future-work collision: General-purpose non-causal SSMs for LLMs.
- Minimum validation: Evaluate a 'Single-Pass Non-Causal SSM' vs. a 'Dual-Pass/Multi-Scan Mamba' vs. a 'Causal Mamba' on a prefix-LM task (e.g., completing a sentence given a prefix) in terms of perplexity, throughput, and memory efficiency.
- Falsification risk: The single-pass mechanism may fail to capture sufficient context to compete with dual-pass SSMs or standard attention-based prefix-LMs.
- Why this is not generic: It addresses the specific efficiency/performance bottleneck of current SSMs in the context of the high-performing non-causal LLM architectures identified in 2025 literature.
- Confidence: medium
- Required next search: Search for 'single-pass bidirectional state space models' or 'non-causal SSM sequence modeling' to check for any movement from vision-centric to text/LLM-centric non-causal SSMs.
