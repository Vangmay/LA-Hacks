# Papers



## Paper: Attention is All you Need
- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: resolve_arxiv_paper
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (Seed Paper)
- Why it matters: Establishes the Transformer architecture, replacing recurrence and convolutions with self-attention, which is the foundation of modern LLMs.
- Caveat: Quadratic scaling of attention complexity with sequence length is a known bottleneck.


## Paper: On Limitations of the Transformer Architecture
- Paper ID: bbe0e4cc9b052e960362fdc18b6805043b81ca6b
- Year: 2024
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Direct critique of Transformer architectural capabilities.
- Why it matters: Uses Communication Complexity to prove Transformers are incapable of function composition for large domains. This provides a theoretical basis for LLM hallucinations and compositional failures.
- Caveat: Proof relies on assumptions regarding computational complexity conjectures.


## Paper: Limits of Deep Learning: Sequence Modeling through the Lens of Complexity Theory
- Paper ID: e640c1ba69f268a7a1eaa19552dbbc78cdc4cc9f
- Year: 2024
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Direct comparison/extension of the compositionality problem to SSMs.
- Why it matters: Proves that one-layer SSMs (and implicitly Transformers) cannot efficiently perform function composition over large domains without impractically large state sizes. Critically, it notes that even Chain-of-Thought (CoT) prompting does not resolve this scaling issue effectively.
- Caveat: The results are based on complexity theory proofs which may have specific boundary conditions.


## Paper: Transformers are Stateless Differentiable Neural Computers
- Paper ID: 669c7f363d9230263b29f8af58b195c8dbd11a15
- Year: 2026
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Direct collision/formalization of the proposed 'external state' concept.
- Why it matters: Provides a formal derivation showing that causal Transformers are equivalent to 'stateless DNCs' where the external memory is a write-once matrix of value vectors. This suggests that the 'statelessness' of the Transformer is a fundamental property that might be the root cause of the compositionality issues identified in Peng et al. (2024).
- Caveat: The paper treats the external memory as 'write-once', which differs from the 'dynamic/recurrent state' proposed in my seed.


## Paper: Differentiable Tree Operations Promote Compositional Generalization
- Paper ID: 179237bc5fb46f34ef936b1552600bf3521c3c64
- Year: 2023
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Direct collision/alternative mechanism for compositionality.
- Why it matters: Proposes a Differentiable Tree Machine (DTM) that uses an external memory and an agent to execute symbolic tree operations. It achieves 100% compositional generalization on synthetic tasks, significantly outperforming Transformers. This provides evidence that integrating symbolic-like structured operations with external memory is a viable path for compositionality.
- Caveat: It relies on a specific 'tree operation' paradigm which might be less general than a continuous functional state.


## Paper: TransXSSM: A Hybrid Transformer State Space Model with Unified Rotary Position Embedding
- Paper ID: 838e911ebe009dbadb87e6f78b654460c1cddd3a
- Year: 2025
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Hybrid architecture (Transformer + SSM).
- Why it matters: Addresses the positional encoding mismatch between Transformers (RoPE) and SSMs. While it improves efficiency and long-context modeling, it does not explicitly target the functional compositionality gap.
- Caveat: Focus is on positional consistency and efficiency rather than structural compositionality.


## Paper: Rethinking Reasoning in LLMs: Neuro-Symbolic Local RetoMaton Beyond ICL and CoT
- Paper ID: cfa00f9997c4eef5caef44788e2bb88b4efb7240
- Year: 2025
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Direct collision/related mechanism for symbolic reasoning.
- Why it matters: Replaces global datastores with local, task-adaptive Weighted Finite Automata (WFA) to promote robust, context-aware retrieval. This is a specialized form of external structured memory that provides symbolic traceability. It reinforces the idea that structured memory is superior to implicit CoT for reasoning, but it uses a specific automaton structure rather than a general functional state.
- Caveat: It focuses on WFAs/automata, which might be more constrained than a general 'differentiable scratchpad' or functional state space.


## Paper: Neural Ordinary Differential Equations with Differentiable Hidden State for Irregular Time Series
- Paper ID: e05c8b2c7be4c39f1efb12fa9fc79135d73c93e2
- Year: 2025
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Potential mechanism for continuous/differentiable state updates.
- Why it matters: Proposes a Differentiable Hidden State (DHS) within a Neural ODE framework to capture continuous dynamics. While applied to time series, the concept of a continuous, differentiable latent process that integrates new information without breaking continuity is technically close to the 'continuous functional state' needed for compositionality.
- Caveat: The primary focus is on temporal modeling for irregular time series rather than symbolic/logical compositionality.


## Paper: Universal Approximation Abilities of a Modular Differentiable Neural Network
- Paper ID: cb22e431201f0753e058726fdf058e8f07404eed
- Year: 2024
- Source bucket: relevance_search
- Found by: relevance_search
- Relation to seed: Potential mechanism for functional modularity.
- Why it matters: Proposes a class of networks built with reusable neural modules (functional blocks) that are differentiable and interpretable. It provides mathematical proofs for their approximation abilities. This supports the idea that functional modularity is a theoretically sound way to approach complex target functions via composition.
- Caveat: It focuses on the approximation properties of the modules themselves rather than the architectural integration into a sequence-modeling Transformer for reasoning tasks.
