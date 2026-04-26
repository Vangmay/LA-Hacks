# Findings



## Finding: Linear Complexity via Fixed-Size Reservoir Memory

- Claim: Shifting attention from the entire input sequence to a fixed set of evolving memory units (Reservoir Computing) can achieve linear complexity.
- Confidence: medium
- Evidence:
  - ae77842be0aebc13b208726a2b5f3565dcd2e66a (Echo State Transformer: Attention Over Finite Memories, 2025)
- Why it matters: Offers a concrete mechanism to break the quadratic scaling bottleneck of the original Transformer architecture by decoupling sequence length from attention computation cost.
- Caveat: The primary evaluation in the source is on time-series benchmarks; the applicability and performance on high-entropy natural language tasks remain an open question.


## Finding: Readout-based vs. State-based Reservoir Attention

- Claim: Recent work on Reservoir Computing (RC) for NLP uses attention primarily at the readout stage to adapt output weights.
- Confidence: high
- Evidence:
  - ea78c1c0c4b19d13b405c3c2b8151df9d68f2838 (Reservoir Computing as a Language Model, 2025)
- Why it matters: This creates a technical gap. While attention-enhanced reservoirs (readout-based) improve output adaptability, they may not improve the reservoir's ability to represent complex, hierarchical sequence information. A mechanism that applies attention to the internal reservoir state updates (state-based) could provide deeper semantic representation than a simple readout-based approach.
- Caveat: It is unknown if state-based attention increases the computational complexity back toward quadratic or if it can maintain the linear benefits of RC.


## Finding: Contextual Modulation vs. Internal Attentional Sculpting

- Claim: Current methods for improving reservoir dynamics (e.g., via RL) focus on external context modulation, rather than internal, sequence-driven attentional sculpting.
- Confidence: medium
- Evidence:
  - d5cd4318c0952171de76025319bed74bab5f278b (Modulating Reservoir Dynamics via RL, 2024)
  - 4330d4276315658e068dac5b4f033d2d68f871f1 (Geometry and efficiency of learned and reservoir recurrent dynamics, 2026)
- Why it matters: While RL can provide task-relevant context to a reservoir, it doesn't address how the reservoir should dynamically adapt its internal state representations to the specific nuances of a long, high-entropy input sequence (like text). The 'sculpting' identified by Maslennikov (2026) as the key to RNN efficiency suggests that an internal mechanism—specifically one that can perform attentional selection/integration during the state update—is likely necessary to bridge the gap between RC efficiency and Transformer performance.
- Caveat: The computational cost of this 'internal sculpting' must be carefully managed to ensure it remains $O(L)$ and doesn't revert to the quadratic cost of standard Transformers.
