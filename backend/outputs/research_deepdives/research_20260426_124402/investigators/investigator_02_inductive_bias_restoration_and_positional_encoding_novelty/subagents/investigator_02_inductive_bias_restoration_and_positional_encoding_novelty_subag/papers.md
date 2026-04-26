# Papers



## Paper: Attention is All you Need

- Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- Year: 2017
- Source bucket: seed_metadata
- Found by: resolve_arxiv_paper
- Relation to seed: Seed paper for the Transformer architecture.
- Why it matters: Introduces sinusoidal positional encodings to inject sequence order into the attention mechanism. This is the baseline against which all future relative, rotary, and aliased positional encodings are compared.
- Caveat: The original absolute sinusoidal encoding lacks the relative distance inductive bias found in later methods like RoPE or ALiBi, which frequently leads to performance degradation on sequence lengths unseen during training.


## Paper: Attention is All you Need

- **Paper ID**: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
- **Year**: 2017
- **Source bucket**: seed_metadata
- **Found by**: resolve_arxiv_paper
- **Relation to seed**: Seed Paper
- **Why it matters**: It is the foundation of the modern Transformer architecture. It explicitly claims to discard recurrence and convolution in favor of self-attention, using sinusoidal encodings to inject spatial/temporal layout. This 'pure attention' approach creates the inductive bias gap that later work attempts to restore.
- **Caveat**: The original absolute positional encoding is not translation invariant, which is a significant signal processing departure from CNNs.


## Paper: LEDiT: Your Length-Extrapolatable Diffusion Transformer without Positional Encoding

- Paper ID: 23ff21c3608b641c32b5fe191dcc307071e829b5
- Year: 2025
- Source bucket: recent_followups
- Found by: paper_relevance_search
- Relation to seed: Proposes a departure from the standard RoPE logic used in most Transformer derivatives.
- Why it matters: Argues that explicit positional encodings (PE) like RoPE are the primary obstacle to resolution/length scaling because they require extrapolation to unseen positions. Claims causal attention can implicitly encode global positional information, supporting extrapolation up to 4x training resolution.
- Caveat: Primarily tested on Diffusion Transformers (image generation), but the mechanism of causal attention providing implicit bias has significant implications for LLMs.


## Paper: Self-Attention with Relative Position Representations

- **Paper ID**: c8efcc854d97dfc2a42b83316a2109f9d166e43f
- **Year**: 2018
- **Source bucket**: closest_prior_work
- **Found by**: paper_relevance_search
- **Relation to seed**: Direct follow-up; cites Vaswani et al. (2017).
- **Why it matters**: This is the seminal work introducing Relative Positional Encodings (RPE). It argues that absolute positions are not sufficient for some tasks and proposes learning weights based on the distance between elements. From a signal processing perspective, this is the first step toward restoring 'shift-invariance' (Toeplitz structure) to the attention mechanism.
- **Caveat**: The implementation uses a clipping distance $k$, which effectively turns the global attention into a local windowed filter with respect to the positional component.


## Paper: Transformer Language Models without Positional Encodings Still Learn Positional Information

- Paper ID: a2fc77f075f666b462d9350e7576f0ba9845c61b
- Year: 2022
- Source bucket: foundational_references
- Found by: paper_relevance_search
- Relation to seed: Direct challenge to the necessity of explicit positional encodings introduced in Vaswani et al. (2017).
- Why it matters: Establishes that causal transformer LMs (like GPT architectures) acquire an implicit notion of absolute position from the causal mask itself. This predates the 2025 LEDiT claim and proves the phenomenon exists in NLP, not just Vision.
- Caveat: While models are 'competitive' without PEs, they typically still benefit from explicit PE on specific complex structural tasks; the 'implicit bias' alone may be coarse and insufficient for SOTA precision.


## Paper: 2-D SSM: A General Spatial Layer for Visual Transformers

- **Paper ID**: debbb47abc9fb757857f7c06aa86ca558d37c2d7
- **Year**: 2023
- **Source bucket**: recent_followups
- **Found by**: paper_relevance_search
- **Relation to seed**: Provides an alternative to the positional encoding gap by using State Space Models (SSMs) to restore translation invariance.
- **Why it matters**: It demonstrates that Transformers can function without explicit positional encodings (APE/RPE) if the layer geometry satisfies shift-invariance. This is a modular confirmation of my archaeologist hypothesis: the 'novel' attention mechanism is often just a less-efficient way to learn what classical signal processing already guarantees via structure.
- **Caveat**: The SSM approach is a separate layer type; it doesn't solve the core inductive bias gap *within* the self-attention operation itself.


## Paper: Equivariance Discovery by Learned Parameter-Sharing

- **Paper ID**: c487dd8dabfdc6cd3aed6c03c5d8cddef4980ed7
- **Year**: 2022
- **Source bucket**: nearby_publication_competitors
- **Found by**: google_scholar_search / paper_relevance_search
- **Relation to seed**: Provides the mathematical framework for 'discovering' shift-invariance (Toeplitz structure) from data.
- **Why it matters**: It formalizes the search for equivariance as an optimization problem over parameter-sharing schemes. It confirms that the 'shift' property can be recovered by learning a Toeplitz matrix. This is the closest collision to my proposal, though it focuses on general parameter sharing rather than the specific dynamic kernel of self-attention.
- **Caveat**: It treats the matrix as a parameter-sharing map rather than a distance-based bias in a transformer-style attention head.
