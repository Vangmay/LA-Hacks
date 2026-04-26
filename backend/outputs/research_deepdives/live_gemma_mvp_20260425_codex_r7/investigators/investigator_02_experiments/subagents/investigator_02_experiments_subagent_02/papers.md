# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: N/A (is the seed paper)
- Why it matters: Introduces the Transformer architecture, which uses solely attention mechanisms and dispensed with recurrence and convolutions, enabling massive parallelization and setting the foundation for modern large language models.
- Caveat: The extreme popularity and high citation count (173k+) may make it harder to find recent critiques of its core architectural assumptions without targeted searches.


## Paper: Echo State Transformer: Attention Over Finite Memories

- Paper ID: ae77842be0aebc13b208726a2b5f3565dcd2e66a
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct follow-up/Alternative architecture addressing quadratic complexity.
- Why it matters: Proposes a hybrid architecture (EST) that integrates Transformer attention with Reservoir Computing (Echo State Networks). It shifts attention from the entire input sequence to a fixed-size reservoir of units, achieving linear complexity while maintaining temporal sensitivity.
- Caveat: The performance on standard LLM tasks (text) vs. time-series tasks is a critical distinction; the abstract emphasizes time-series benchmarks.


## Paper: Reservoir Computing as a Language Model

- Paper ID: ea78c1c0c4b19d13b405c3c2b8151df9d68f2838
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct collision/Prior work for the SRT seed.
- Why it matters: Compares character-level language modeling using traditional reservoir computing vs. Transformers. Critically, it explores an 'attention-enhanced reservoir' that uses attention to adapt output weights. It finds Transformers have better quality while RC is more efficient.
- Caveat: Focuses on character-level modeling, which may not capture the same semantic depth as word/subword-level Transformers.


## Paper: Reservoir Computing as a Language Model

- Paper ID: ea78c1c0c4b19d13b405c3c2b8151df9d68f2838
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Collision/Technical predecessor for SRT.
- Why it matters: Investigates RC for character-level language modeling. Compares static linear readouts with 'attention-enhanced reservoirs' where attention adapts output weights. Shows RC is more efficient but Transformers have better quality.
- Caveat: The attention mechanism is applied to the readout stage, not the internal reservoir dynamics.


## Paper: Geometry and efficiency of learned and reservoir recurrent dynamics in context-dependent integration-switching.

- Paper ID: 4330d4276315658e068dac5b4f033d2d68f871f1
- Year: 2026
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Direct technical collision/Theoretical background.
- Why it matters: Investigates the geometry of state-space dynamics. It finds that trainable RNNs are more efficient than fixed reservoirs because they 'sculpt' their internal dynamics into low-dimensional, task-aligned manifolds, whereas fixed reservoirs rely on high-dimensional, entangled representations.
- Caveat: Focuses on context-dependent integration tasks rather than high-dimensional NLP; however, it provides the mathematical motivation for why 'sculpting' (learning) the reservoir is necessary.


## Paper: Recurrent Self-Attention Dynamics: An Energy-Agnostic Perspective from Jacobians

- Paper ID: 8d52c75ddac2dbd87115f975bd9191d06e0b6696
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Theoretical collision/Adjacent work.
- Why it matters: Provides a dynamical systems analysis of self-attention inference dynamics. While it focuses on characterizing standard self-attention, its use of Jacobian-based analysis provides a formal framework that could be used to analyze the stability and signal propagation of the proposed ASUR mechanism.
- Caveat: It is a theoretical characterization of *existing* attention, not a proposal for reservoir-based attention.


## Paper: Echo State and Band-pass Networks with aqueous memristors: leaky reservoir computing with a leaky substrate

- Paper ID: a00e7c132f4ae603f5cb8b8e252764fd296a880a
- Year: 2025
- Source bucket: relevance_search
- Found by: paper_relevance_search
- Relation to seed: Adjacent work (structural/physical gating).
- Why it matters: Discusses 'leaky reservoir computing' implemented via physical memristors. While 'leaky' is a form of gating (regulating the speed of state changes), it is a structural/physical property rather than a learned, attentional mechanism that dynamically sculpts the state based on input context.
- Caveat: This is a hardware-centric implementation; its relevance to software-based attentional modeling is purely conceptual regarding 'gating'.


## Paper: Reservoir Computing With Dynamic Reservoir using Cascaded DNA Memristors

- Paper ID: 00122523348dee783641e25bef91cae789bdad8b
- Year: 2023
- Source bucket: bulk_search
- Found by: paper_bulk_search
- Relation to seed: Adjacent work (dynamic reservoir implementation).
- Why it matters: Proposes a way to synthesize a 'dynamic reservoir' through cascaded DNA memristors. The cascade connections can change dynamically, which is more efficient than a static reservoir. This confirms that 'dynamic' reservoir architectures are a recognized research direction, though the implementation here is physical/molecular rather than the proposed attentional/algorithmic approach.
- Caveat: This is a hardware-focused paper on DNA computing; its mechanism for 'dynamic' behavior is structural rather than sequence-dependent logic.
