# Proposal Seeds



## Proposal Seed: Automated Circuit Discovery for Transformer Scaling

- Status: speculative
- Originating taste: gap_miner
- Seed-paper hook: BERTology (Rogers et al., 2020) which highlights the gap in mechanistic understanding.
- Evidence trigger: The documented lack of mechanistic understanding regarding Transformer success.
- Candidate novelty: Moving from manual/heuristic probing (current BERTology) to automated discovery of functional circuits/motifs as models scale.
- Technical mechanism: Using causal intervention or gradient-based attribution to identify specific sub-networks (circuits) responsible for particular tasks or behaviors.
- Closest prior-work collision: Existing mechanistic interpretability frameworks (e.g., TransformerLens, causal mediation).
- Closest future-work collision: Scaling laws for interpretability/transparency.
- Minimum validation: Apply to a small Transformer on a toy task (e.g., induction heads) and successfully recover the circuit automatically.
- Falsification risk: Circuits might be too highly distributed or non-compositional for reliable automated discovery.
- Why this is not generic: It explicitly attempts to bridge the gap between empirical performance and mechanistic understanding via automation.
- Confidence: low
- Required next search: 'automated circuit discovery transformers' or 'mechanistic interpretability scaling laws'


## Proposal Seed: Entropy-Driven Dynamic Rank and Precision (ED-DRP) for Transformer Inference

- Status: promising
- Originating taste: gap_miner
- Seed-paper hook: The tension between the need for specialized Transformer compression (Guo et al., 2025) and the proven utility of entropy/adaptive rank (Lee et al., 2025; Maisonnave et al., 2025).
- Evidence trigger: The existence of separate works for adaptive rank (TALE), entropy-based selection (AdaptToken), and joint low-rank/quantization (MLoRQ), but no unified framework that uses entropy to modulate *both* simultaneously for the attention mechanism.
- Candidate novelty: A unified mechanism where the *entropy of the attention map* serves as the real-time control signal for a joint optimization of rank (for $Q, K, V$ matrices) and bit-width (for the resulting product/cache).
- Technical mechanism: A lightweight entropy estimator (e.g., on a subset of heads or using a proxy) that maps to a discrete set of (rank, bit-width) pairs, allowing the model to scale precision and complexity based on the informational density of the current input sequence.
- Closest prior-work collision: MLoRQ (joint optimization but static/pre-planned); TALE (rank-adaptive but not entropy-driven for precision).
- Closest future-work collision: Real-time hardware-aware dynamic scaling.
- Minimum validation: Implement on a Llama-3-8B model; compare accuracy/latency/memory against MLoRQ and TALE benchmarks.
- Falsification risk: The overhead of calculating entropy might negate the gains from compression; or entropy might not be highly correlated with the optimal (rank, bit-width) pair.
- Why this is not generic: It synthesizes three distinct recent research threads (entropy signals, adaptive rank, and joint compression) into a single architecture-aware inference optimization.
- Confidence: medium
- Required next search: 'entropy-based precision scaling transformers' or 'joint low-rank and quantization dynamic'
