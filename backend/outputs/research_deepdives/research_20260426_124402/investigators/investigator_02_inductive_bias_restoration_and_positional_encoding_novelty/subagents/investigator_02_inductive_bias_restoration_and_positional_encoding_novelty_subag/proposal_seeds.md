# Proposal Seeds



## Proposal Seed: Context-Adaptive Rotary Base Scaling (CARBS)

- Status: speculative
- Originating taste: SOTA Research-Gap Miner
- Seed-paper hook: Vaswani et al. (2017) introduced absolute positional signals that do not scale well and lack relative bias. Later improvements like RoPE provide relative bias but still rely on a fixed base frequency parameter (e.g., 10,000) that limits extrapolation.
- Evidence trigger: The lack of high-citation 'limitation' papers for RoPE in recent bulk searches suggests that scaling failures are typically addressed with heuristic context-window extensions (e.g., Positional Interpolation, NTK-aware scaling) rather than fundamental architectural changes to how positional inductive bias is generated.
- Candidate novelty: Dynamically adjusting the 'base' frequency of rotary embeddings based on the attention entropy or sequence length detected at inference time, rather than fixed interpolation.
- Technical mechanism: A small MLP or gating mechanism that predicts the optimal RoPE base frequency scaling factor for each attention head based on the input hidden states, allowing the model to switch between local precision and global context coverage.
- Closest prior-work collision: NTK-aware RoPE, YaRN, and LongRoRA (all use manual or piecewise interpolation/scaling).
- Closest future-work collision: Continuous position representations that dispense with rotary logic entirely.
- Minimum validation: Test on the 'Passkey Retrieval' task and LongBench after fine-tuning a Llama-2-7B equivalent with this gating mechanism.
- Falsification risk: Static NTK-aware scaling might already outperform a dynamic gate if the gate fails to generalize to truly OOD lengths.
- Why this is not generic: It moves positional encoding from a static preprocessing step to a dynamic, learned attention component.
- Confidence: low
- Required next search: Search for 'dynamic base scaling RoPE' or 'learned rotary frequency'.


## Proposal Seed: Translation-Invariant Attention via Toeplitz-Structured Positional Bias

- Status: raw
- Originating taste: Cross-Era Terminology Deconfounder (Signal Processing focus)
- Seed-paper hook: The original Transformer uses sinusoids for absolute position, which lack the shift-invariance of CNNs.
- Evidence trigger: Finding: Intentional Removal of Local Inductive Biases. The seed paper's transition to absolute positioning creates a mismatch with classical signal processing requirements for translation equivariance.
- Candidate novelty: Reformulating self-attention as a sequence of dynamic filters where the positional bias is constrained to be a Toeplitz matrix, ensuring the attention mechanism behaves like a shift-invariant operator by design, rather than by learning.
- Technical mechanism: Impose a constraint on the attention logit $A = QK^T + B$, where $B_{i,j} = f(i-j)$. This $f$ is modeled as a learned continuous function or a structured kernel that explicitly represents the 'shift' property found in discrete convolutions.
- Closest prior-work collision: Shaw et al. (2018) 'Self-Attention with Relative Position Representations'.
- Closest future-work collision: T5 (Raffel et al. 2019) relative bias; RoPE (Su et al. 2021).
- Minimum validation: Compare parity of a toy Transformer with Toeplitz-bias vs. standard APE on a synthetic 'string shift' task where the model must detect patterns regardless of their absolute index.
- Falsification risk: If learned absolute positional encodings already approximate shift-invariance sufficiently in large-scale data, the explicit constraint may only improve sample efficiency but not final performance.
- Why this is not generic: It moves beyond simply 'adding relative bias' to a formal requirement that the attention kernel must satisfy the mathematical definition of a convolution (linear time-invariance) via structured matrices.
- Confidence: medium
- Required next search: Search for 'Toeplitz matrix attention' and 'shift-invariant self-attention' to check if this formal connection to classical signal processing has been exhausted or merely used as a heuristic.


## Proposal Seed: Implicit-Explicit Hybrid Resonance (IE-HR)

- Status: promising
- Originating taste: SOTA Research-Gap Miner
- Seed-paper hook: Vaswani et al. (2017) sinusoid basis vs. Zhang et al. (2025) LEDiT PE-free causal attention.
- Evidence trigger: LEDiT (2025) claims explicit PE like RoPE is the 'primary obstacle' to length extrapolation. However, LEDiT focuses on Diffusion Transformers where global structure (implicit) and local fine-grained detail (enhanced by a locality module) are both critical.
- Candidate novelty: Instead of removing RoPE or purely relying on causal attention, this proposal suggests a gated hybrid where the high-frequency components of RoPE (encoding local precision) are preserved while the low-frequency components (encoding coarse global position) are suppressed or replaced by implicit causal signals.
- Technical mechanism: A frequency-dependent gain controller for RoPE. It applies a learnable or context-length-dependent decay to the lower frequency bands of the rotary embedding, effectively 'handing off' global positioning to the causal attention mechanism while maintaining RoPE's local relative bias.
- Closest prior-work collision: ALiBi (local bias), LEDiT (no PE), NTK-aware RoPE (modifies frequencies but doesn't suppress them in favor of implicit signals).
- Closest future-work collision: Fully implicit position LLMs (e.g., NoPE transformers).
- Minimum validation: Train a 1B parameter LLM with Frequency-Gated RoPE. Test on LongBench and image resolution scaling (cross-domain validation).
- Falsification risk: If the 'global positional information' in causal attention is too weak for complex symbolic reasoning tasks (e.g., code), the model will collapse compared to standard RoPE.
- Why this is not generic: It specifically addresses the contradiction between LEDiT (PE is bad) and standard LLM SOTA (RoPE is essential) by proposing a spectral decomposition of positional signals.
- Confidence: medium
- Required next search: Search for 'partial positional encoding' or 'frequency-specific bias in RoPE'.


## Proposal Seed: Spectral Deconfliction of Positional Bias (SD-PB)

- Status: promising
- Originating taste: SOTA Research-Gap Miner
- Seed-paper hook: Vaswani et al. (2017) explicit sinusoidal grid vs. Haviv et al. (2022) and Zhang et al. (2025) implicit causal-mask signals.
- Evidence trigger: Haviv (2022) shows LLMs without PE learn coarse global position. Zhang (2025) shows explicit PEs like RoPE are the 'primary obstacle' to extrapolation because they fail on OOD coordinate values. This suggests a redundancy: RoPE provides global info the model already has, while crashing on global metrics the model needs to ignore to generalize.
- Candidate novelty: 'Spectral Deconfliction'—restricting explicit positional encodings (RoPE) to *only* high-frequency components (local relative distance) while relying on the causal mask for low-frequency global positioning.
- Technical mechanism: Frequency-High-Pass RoPE. Modify the rotary embedding's frequency spectrum to zero out or drastically dampen frequencies below a certain threshold. This ensures the model 'sees' relative order within local windows through RoPE, but 'senses' global context only through the causal attention mask, which naturally scales to any length without coordinate-value OOD issues.
- Closest prior-work collision: NoPE (No Positional Encoding) - removes PE entirely; RoPE - uses the full spectrum; Alibi - uses a linear slope (monotonic, not frequency-based).
- Closest future-work collision: Continuous-form implicit positions.
- Minimum validation: Train two 3B-parameter Transformers: one with standard RoPE and one with SD-PB (High-Pass RoPE). Compare on 1) local syntax (English parsing) and 2) the 'Passkey Retrieval' challenge at 4x training length.
- Falsification risk: If the causal mask's implicit signal is too noisy in large context windows (e.g., >1M tokens), it might fail to resolve long-range dependencies that a full RoPE (with interpolation) could handle.
- Why this is not generic: It moves from 'PE interpolation' (trying to stretch the grid) to 'PE pruning' (removing the parts of the grid that cause the stretch to fail).
- Confidence: high
- Required next search: Adversarial search for 'High-pass filter positional encoding' or 'Band-limited RoPE'.
