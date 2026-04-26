# Findings



## Finding: Evolution from Recurrence to Attention

- Claim: The Transformer represents a paradigm shift from recurrent-based sequence transduction to purely attention-based architectures.
- Confidence: high
- Evidence:
  - Paper ID: cea967b59209c6be22829699f05b8b1ac4dc092d (Seq2Seq, 2014)
  - Paper ID: fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5 (Attention in NMT, 2014)
  - Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776 (Transformer, 2017)
- Why it matters: Understanding this lineage reveals that the Transformer did not invent attention, but rather leveraged it to replace the sequential bottleneck of RNNs.
- Caveat: The transition was driven by compute/parallelization needs as much as architectural elegance.

## Finding: The Parallelization Bottleneck in RNNs

- Claim: Recurrent architectures (LSTMs, GRUs) impose a sequential dependency that limits training speed and scalability.
- Confidence: high
- Evidence:
  - Paper ID: 2e9d221c206e9503ceb452302d68d10e293f2a10 (LSTM, 1997)
  - Paper ID: 204e3073870fae3d05bcbc2f6a8e263d9b72e776 (Transformer, 2017)
- Why it matters: This is the primary 'gap' or 'failure' of previous SOTA that the Transformer specifically addressed, enabling the training of much larger models.
- Caveat: While Transformers improve parallelization, they introduce quadratic complexity with respect to sequence length.


## Finding: Attention Sinks as Geometric Reference Frames

- Claim: The attention sink phenomenon is a manifestation of a fundamental geometric principle: the establishment of reference frames that anchor representational spaces in high-dimensional manifolds.
- Confidence: medium
- Evidence:
  - Paper ID: 5958e8a8010d39947104efe599b676b9e1d0e040 (What are you sinking?, 2025)
- Why it matters: This shifts the view of attention sinks from being 'architectural artifacts' or 'wasteful' to being a structural necessity for stable coordinate systems. It suggests that novelty could lie in how these reference frames are explicitly managed or designed, rather than just observed.
- Caveat: This is a relatively new geometric interpretation; empirical validation across more architectures is needed.

## Finding: Attention Sinks as Security/Efficiency Vulnerabilities

- Claim: Attention sinks represent both a source of computational waste and a potential vector for backdoor attacks.
- Confidence: medium
- Evidence:
  - Paper ID: 5c308e16788bb80d9a6292c05448d319928f0be5 (Visual Attention Sink in LMMs, 2025) - Wasted attention budget.
  - Paper ID: 33eb524517cd5fc1a0eba5afcf9ed9f037650986 (Forgetting to Forget, 2025) - Backdoor gateway.
- Why it matters: If sinks are necessary for stability but wasteful/insecure, then designing an architecture that provides 'clean' reference frames is a high-value research direction.
- Caveat: The link to backdoors is specific to the unlearning context.


## Finding: Conflict in the Root Cause of Attention Sinks

- Claim: There is a lack of consensus on whether attention sinks/artifacts are a structural mathematical necessity or a byproduct of training dynamics/semantics.
- Confidence: medium
- Evidence:
  - Paper ID: 10bd38673951f5d7729568284093cbd80482ab16 (Darcet et al., 2023) - Views them as computational artifacts requiring 'registers' to hold information.
  - Paper ID: 8029f812c7083ccffbd52e65aeeabbb5907d809e (Shi et al., 2026) - Suggests they are 'lazy aggregation' shortcuts driven by coarse-grained semantic supervision.
  - Paper ID: 5958e8a8010d39947104efe599b676b9e1d0e040 (Ruscio et al., 2025) - Argues they are a fundamental geometric necessity for establishing reference frames.
- Why it matters: If it's geometric, we need a structural anchor. If it's semantic, we need better regularization or supervision. If it's a computational artifact, we need registers.
- Caveat: These perspectives are not necessarily mutually exclusive, but their priority in architecture design is contested.
