# Proposal Families

## Family 1: Semantic-Spatial Synchronization (Hybrid Optimization)
**Focus:** Resolving the "Interface Gap" in multi-modal and multi-scale hybrid architectures.

### 1.1 Proposal: Synchronous Semantic-Spatial Alignment (S3A)
- **Core Novelty Claim:** Replaces passive fusion (concatenation/gating) with an active synchronization mechanism that forces local (CNN) and global (Transformer) representations into a coherent, shared latent manifold.
- **Mechanism:** A **Cross-Scale Contrastive Module** coupled with a dual-branch encoder. The module utilizes a joint latent embedding loss to minimize the distance between high-resolution local CNN patch embeddings and their corresponding low-resolution global Transformer semantic tokens.
- **Evidence Support:** 
    - **Gap:** Documented "semantic misalignment" where feature scales and spaces are incompatible during fusion.
    - **Sources:** `DBAANet (2025)` and `BGSC-Net (2026)`.
- **Collision Risks:**
    - **Prior-Work:** Standard CNN-ViT hybrids (e.g., `FusionSegNet 2026`) that use additive or attention-guided fusion. S3A differs by using *contrastive alignment* rather than just *attention-weighted integration*.
    - **Future-Work:** Unified "third-way" architectures that attempt to learn a single inductive bias from scratch.
- **Validation Path:**
    - **Benchmark:** High-precision segmentation tasks (e.g., polyp segmentation in medical imaging; building extraction in remote sensing).
    - **Metrics:** Boundary F1 (BF Score) and mIoU, specifically looking for improvements in edge/boundary reconstruction.
- **Falsification Criteria:** If the alignment module's FLOPs/parameter overhead negates accuracy gains, or if the alignment fails to resolve boundary loss due to underlying quantization errors in the tokenization process.
- **Confidence:** Medium (High implementation feasibility; medium research risk regarding computational cost).

---

## Family 2: Dynamics-based Compositional Architectures (Functional Evolution)
**Focus:** Resolving the "Compositionality Gap" and "Statelessness" in sequence modeling.

### 2.1 Proposal: Continuous Functional Manifold Augmentation (CFMA)
- **Core Novelty Claim:** Addresses the fundamental inability of Transformers to compose functions over large domains by integrating a continuous, differentiable latent state that serves as a dynamic, non-discrete functional scratchpad.
- **Mechanism:** Integration of a **Neural ODE-based Hidden State Layer** between Transformer blocks. This layer treats the transformation of intermediate function outputs as a continuous-time dynamical system, allowing the model to "evolve" its functional state via a differentiable manifold rather than relying on all-to-all attention communication for every state step.
- **Evidence Support:** 
    - **Gap:** Transformers are theoretically limited in function composition due to communication complexity and are formally "stateless" (effectively write-once DNCs).
    - **Sources:** `Peng et al. (2024)` (Compositionality limits) and `Tang & Xie (2026)` (Statelessness formalization).
- **Collision Risks:**
    - **Prior-Work (Discrete):** `Soulos et al. (2023)` (Differentiable tree operations) and `RetoMaton (2025)` (Neuro-symbolic WFA). CFMA is distinct because it targets *continuous functional manifolds* rather than discrete symbolic trees or automata.
    - **Prior-Work (State-Space):** Existing State Space Models (SSMs) like Mamba. The novelty lies in using the continuous manifold specifically to solve *functional composition* rather than just long-context efficiency.
- **Validation Path:**
    - **Benchmark:** "Deep Nesting" symbolic reasoning tasks (e.g., recursive tree traversal, nested logical deductions, or complex mathematical function composition) where the domain size scales.
    - **Metrics:** Success rate on compositional generalization vs. domain size scaling.
- **Falsification Criteria:** If the bottleneck is found to be the representational capacity of the token embeddings themselves, or if the ODE-based state update fails to converge during training due to the complexity of the gradient flow through the continuous-time dynamics.
- **Confidence:** Medium (High novelty; high technical risk regarding training stability and convergence).